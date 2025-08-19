# ui/main_window.py
# -*- coding: utf-8 -*-
import time
import threading
import webbrowser
from pathlib import Path
from utils.paths import APP_DIR, GROUPS_FILE, PROFILE_DIR, app_path, POST_WL_FILE, DEL_WL_FILE
from utils.whitelist import load_list, normalize_url
import subprocess 
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QSettings
from utils.i18n import Lang, tr
from core.steam_poster import SteamPoster
from widgets.logger import UiLogger
from widgets.card import Card
from ui.styles import apply_modern_style, fade_in
from utils.paths import APP_DIR, GROUPS_FILE, PROFILE_DIR, app_path
from utils.browser import launch_official_chrome_login, fmt_duration
from utils.whitelist import load_list, normalize_url


STEAM_AUTHOR_URL = "https://steamcommunity.com/id/wuyan1337/"

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SteamEchoPost')
        self.resize(880, 900)
        self.setWindowIcon(QtGui.QIcon(app_path("resources", "ico.ico")))
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)

        # ===== 布局 =====
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        self.card = Card(self)
        root.addWidget(self.card, 1)
        body = QtWidgets.QVBoxLayout(self.card)
        body.setContentsMargins(20, 20, 20, 20)
        body.setSpacing(14)

        self.btn_launch_chrome = QtWidgets.QPushButton('登录Steam')
        self.msg = QtWidgets.QPlainTextEdit(); self.msg.setPlaceholderText('要发送的文本…')
        self.delay = QtWidgets.QDoubleSpinBox(); self.delay.setRange(0.0, 60.0); self.delay.setValue(0.8); self.delay.setSuffix(' s/组')
        self.groups_path = QtWidgets.QLineEdit(str(GROUPS_FILE))
        self.pick_btn = QtWidgets.QPushButton('选择 groups.txt')
        self.fetch_btn = QtWidgets.QPushButton('抓取群组到 groups.txt（后台）')
        self.start_btn = QtWidgets.QPushButton('开始自动发布（后台）')
        self.stop_btn = QtWidgets.QPushButton('停止'); self.stop_btn.setEnabled(False)
        self.btn_open_home = QtWidgets.QPushButton('打开作者主页')
        self.open_github_btn = QtWidgets.QPushButton("打开 GitHub 主页") 
        self.leave_btn = QtWidgets.QPushButton('退出无权限组（扫描）')
        #self.add_groups_btn = QtWidgets.QPushButton('添加组') 暂未实现

        # 白名单相关
        self.post_wl_path = QtWidgets.QLineEdit(str(POST_WL_FILE))
        self.post_wl_btn  = QtWidgets.QPushButton('编辑留言白名单')
        self.del_wl_path  = QtWidgets.QLineEdit(str(DEL_WL_FILE))
        self.del_wl_btn   = QtWidgets.QPushButton('编辑删除白名单')

        self.log_view = QtWidgets.QPlainTextEdit(); self.log_view.setReadOnly(True)
        self.logger = UiLogger(self.log_view)

        # 顶部按钮行：登录、作者主页、GitHub 主页
        hdr_row = QtWidgets.QHBoxLayout()
        hdr_row.addWidget(self.btn_launch_chrome)
        #hdr_row.addWidget(self.add_groups_btn)  
        hdr_row.addWidget(self.btn_open_home)
        hdr_row.addWidget(self.open_github_btn) 
        hdr_row.addStretch(1)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        form.addRow('发送内容:', self.msg)
        form.addRow('每组间隔:', self.delay)

        path_row = QtWidgets.QHBoxLayout()
        path_row.addWidget(self.groups_path)
        path_row.addWidget(self.pick_btn)

        # 留言白名单行
        post_wl_row = QtWidgets.QHBoxLayout()
        post_wl_row.addWidget(self.post_wl_path)
        post_wl_row.addWidget(self.post_wl_btn)

        # 删除白名单行
        del_wl_row = QtWidgets.QHBoxLayout()
        del_wl_row.addWidget(self.del_wl_path)
        del_wl_row.addWidget(self.del_wl_btn)

        # 功能按钮行
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(self.fetch_btn)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.leave_btn)

        # 组装到页面
        body.addLayout(hdr_row)
        body.addLayout(form)
        body.addWidget(QtWidgets.QLabel('groups.txt 路径:'))
        body.addLayout(path_row)

        body.addWidget(QtWidgets.QLabel('留言白名单（这些群不会自动留言）:'))
        body.addLayout(post_wl_row)
        body.addWidget(QtWidgets.QLabel('删除白名单（这些群不会被自动退出）:'))
        body.addLayout(del_wl_row)

        body.addLayout(btn_row)
        body.addWidget(QtWidgets.QLabel('日志输出:'))
        body.addWidget(self.log_view, 1)



        # ===== 状态 =====
        self.poster: SteamPoster | None = None
        self.worker_thread: threading.Thread | None = None
        self._stop_flag = threading.Event()

        # ===== 连接 =====
        self.btn_launch_chrome.clicked.connect(self.on_launch_chrome)
        self.btn_open_home.clicked.connect(self.on_open_home)
        self.pick_btn.clicked.connect(self.pick_groups)
        self.fetch_btn.clicked.connect(self.do_fetch)
        self.start_btn.clicked.connect(self.do_start)
        self.stop_btn.clicked.connect(self.do_stop)
        self.leave_btn.clicked.connect(self.leave_no_comment_groups)
        self.post_wl_btn.clicked.connect(self.open_post_whitelist)
        self.del_wl_btn.clicked.connect(self.open_del_whitelist)
        self.open_github_btn.clicked.connect(self.on_open_github)
        #self.add_groups_btn.clicked.connect(self.on_add_groups_clicked) 之后再搞吧我tm太懒了




        # ===== 样式 & 欢迎 =====
        apply_modern_style(self)
        fade_in(self)
        self.log("[✓] SteamEchoPost v0.1")
        self.log("[✓] 作者QQ1730249")
        self.log("[✓] ------使用方法------")
        self.log("[✓] 1. 登录Steam")
        self.log("[✓] 2. 抓取群")
        self.log("[✓] 3. 填写发送内容")
        self.log("[✓] 4. 开始自动发布")

    # ---------- helpers ----------
    def log(self, s: str):
        self.logger.message.emit(s)

    def ensure_poster(self) -> SteamPoster:
        if self.poster is None:
            self.poster = SteamPoster(log_emit=self.log, headless=True)
        return self.poster

    # ---------- actions ----------
    def on_launch_chrome(self):
        try:
            launch_official_chrome_login()
            self.log(f'[i] 已启动官方浏览器，并使用专用用户目录：{PROFILE_DIR} 请在弹出的窗口中完成登录。登录一次后将长期生效。')
            self.log('[!] 登录成功后请手动关闭浏览器，否则会导致后续报错。')
            self.log('[!] 登录成功后请手动关闭浏览器，否则会导致后续报错。')
            self.log('[!] 登录成功后请手动关闭浏览器，否则会导致后续报错。')
        except Exception as e:
            self.log(f'[!] 启动失败：{e}')

    def on_open_home(self):
        try:
            webbrowser.open(STEAM_AUTHOR_URL)
            self.log("[i] 已在默认浏览器打开作者主页")
        except Exception as e:
            self.log(f"[!] 打开主页失败: {e}")

    def pick_groups(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, '选择 groups.txt', str(APP_DIR), 'Text Files (*.txt)')
        if p:
            self.groups_path.setText(p)

    def do_fetch(self):
        def run():
            try:
                self.log("[*] 开始抓取群组…")
                poster = self.ensure_poster()
                if not poster.ensure_logged():
                    self.log('[!] 未检测到登录状态。请先登录。')
                    return
                out = Path(self.groups_path.text())
                out.parent.mkdir(parents=True, exist_ok=True)
                poster.fetch_groups(out)
            except Exception as e:
                self.log(f'[!] 抓取异常: {e!r}')
        threading.Thread(target=run, daemon=True).start()


    def on_open_github(self):
        url = "https://github.com/wuyan1337/SteamEchoPoster-SEP"
        try:
            import webbrowser
            webbrowser.open(url)
            self.log(f"[i] 已在默认浏览器打开Github主页")
        except Exception as e:
            self.log(f"[!] 打开 GitHub 主页失败: {e}")



    def do_start(self):
        message = self.msg.toPlainText().strip()
        if not message:
            self.log('[!] 发送内容为空。')
            return
        path = Path(self.groups_path.text())
        if not path.exists():
            self.log('[!] 未找到 groups.txt。')
            return

        raw = path.read_text(encoding='utf-8')
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith('#')]
        if not lines and raw.count("https://") > 1:
            parts = raw.split("https://")
            for p in parts:
                p = p.strip()
                if p:
                    lines.append("https://" + p)

        links = lines
        if not links:
            self.log('[!] groups.txt 为空。')
            return

        self._stop_flag.clear()
        self.stop_btn.setEnabled(True)
        self.start_btn.setEnabled(False)

        delay = float(self.delay.value())
        send_wait = max(0.8, delay)
        per_group = send_wait + delay
        total_eta = per_group * len(links)
        self.log(f'[i] 待发送群组数: {len(links)}')
        self.log(f'[i] 每组间隔: {delay:.2f}s，点击后等待: {send_wait:.2f}s')
        self.log(f'[i] 预计总耗时 ≈ {fmt_duration(total_eta)}（约 {total_eta:.1f} 秒）')

        def run():
            t0 = time.time()
            try:
                self.log('[*] 开始发送任务（已进入后台线程）…')

                poster = self.ensure_poster()
                try:
                    poster.driver.set_script_timeout(60)
                except Exception:
                    pass
                try:
                    poster.driver.set_page_load_timeout(12)
                except Exception:
                    pass

                try:
                    if not poster.ensure_logged():
                        self.log('[!] 未登录，无法发送。请先登录。')
                        return
                except Exception as e:
                    self.log(f'[!] 登录检测异常：{e!r}（将尝试继续，但可能失败）')

                total = len(links)
                sent = 0

                post_wl = load_list(self.post_wl_path.text())
                self.log(f'[i] 留言白名单已加载：{len(post_wl)} 条')

                for i, url in enumerate(links, 1):
                    if self._stop_flag.is_set():
                        self.log('[*] 已停止。')
                        break

                    if normalize_url(url) in post_wl:
                        self.log(f'[{i}/{total}] 留言白名单跳过：{url}')
                        continue

                    self.log(f'[{i}/{total}] 打开群组：{url}')

                    ok = False
                    try:
                        ok = poster.post_in_group(url, message, wait_after_send=send_wait)
                    except Exception as e:
                        self.log(f'    [!] 发送异常：{e!r}')

                    if ok:
                        self.log('    [✓] 已发送。')
                        sent += 1
                    else:
                        self.log('    [!] 跳过。')

                    if ok:
                        time.sleep(max(0.0, delay))
                    else:
                        time.sleep(min(0.2, delay * 0.25))

                self.log(f'[✓] 完成。成功发送 {sent}/{total} 个群组。')

            except Exception as e:
                self.log(f'[!] 发送过程中异常: {e!r}')
            finally:
                elapsed = time.time() - t0
                self.log(f'[i] 实际耗时：{fmt_duration(elapsed)}（{elapsed:.1f} 秒）')
                self.stop_btn.setEnabled(False)
                self.start_btn.setEnabled(True)


        self.worker_thread = threading.Thread(target=run, daemon=True)
        self.worker_thread.start()

    def leave_no_comment_groups(self):
        """退出没有留言权限的群组（带二次确认 + 删除白名单保护）"""

        m = QtWidgets.QMessageBox.question(
            self, "确认操作",
            "将自动扫描 groups.txt 中的群组，凡是没有留言框（无权限）的将尝试退出。\n\n是否继续？",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if m != QtWidgets.QMessageBox.StandardButton.Yes:
            self.log("[i] 已取消退出扫描。")
            return

        path = Path(self.groups_path.text())
        if not path.exists():
            self.log('[!] 未找到 groups.txt。')
            return
        raw = path.read_text(encoding='utf-8', errors='ignore')
        links = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith('#')]
        if not links:
            self.log('[!] groups.txt 为空。')
            return

        self._stop_flag.clear()
        self.stop_btn.setEnabled(True)

        def run():
            try:
                poster = self.ensure_poster()
                if not poster.ensure_logged():
                    self.log('[!] 未检测到登录状态。请先登录。')
                    return

                total = len(links)
                left_count = 0
                skipped = 0

                from utils.whitelist import load_list, normalize_url
                del_wl = load_list(self.del_wl_path.text())

                self.log(f'[*] 开始扫描 {total} 个群组，自动退出无权限组…')
                for i, url in enumerate(links, 1):
                    if self._stop_flag.is_set():
                        self.log('[*] 已停止。')
                        break

                    try:
                        poster.driver.get(url)
                    except Exception:
                        try:
                            poster.driver.execute_script("window.stop();")
                        except Exception:
                            pass

                    try:
                        if poster.has_comment_box():
                            self.log(f'[{i}/{total}] 有留言权限，跳过：{url}')
                            skipped += 1
                            continue
                    except Exception:
                        pass

                    if normalize_url(url) in del_wl:
                        self.log(f'[{i}/{total}] 删除白名单保护，不退出：{url}')
                        skipped += 1
                        continue

                    self.log(f'[{i}/{total}] 无留言权限，尝试退出：{url}')
                    ok = poster.leave_group_if_possible()
                    if ok:
                        left_count += 1

                    time.sleep(0.3) 

                self.log(f'[✓] 扫描完成。退出 {left_count} 个；保留/跳过 {skipped} 个。')
            except Exception as e:
                self.log(f'[!] 退出扫描异常: {e!r}')
            finally:
                self.stop_btn.setEnabled(False)

        threading.Thread(target=run, daemon=True).start()


    def do_stop(self):
        self._stop_flag.set()

    def open_post_whitelist(self):
        path = Path(self.post_wl_path.text())
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("# 每行一个群链接，例如：\n# https://steamcommunity.com/groups/yourgroup/\n", encoding='utf-8')
        try:
            subprocess.Popen(["notepad.exe", str(path)])
            self.log(f"[i] 已打开留言白名单：{path}")
        except Exception as e:
            self.log(f"[!] 打开留言白名单失败：{e!r}")

    def open_del_whitelist(self):
        path = Path(self.del_wl_path.text())
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("# 每行一个群链接，不会被自动退出：\n# https://steamcommunity.com/groups/yourgroup/\n", encoding='utf-8')
        try:
            subprocess.Popen(["notepad.exe", str(path)])
            self.log(f"[i] 已打开删除白名单：{path}")
        except Exception as e:
            self.log(f"[!] 打开删除白名单失败：{e!r}")



    def on_add_groups_clicked(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("添加组（根据对方主页）")
        dlg.setModal(True)
        dlg.resize(520, 160)

        url_edit = QtWidgets.QLineEdit(dlg)
        url_edit.setPlaceholderText("粘贴对方主页链接，例如：https://steamcommunity.com/id/xxxx 或 /profiles/xxxxxxxxxxxxxxx")
        url_edit.setText("https://steamcommunity.com/id/")  

        delay_sb = QtWidgets.QDoubleSpinBox(dlg)
        delay_sb.setRange(0.0, 3.0)
        delay_sb.setValue(0.3)
        delay_sb.setSuffix(" s/次")

        start_btn = QtWidgets.QPushButton("开始加入", dlg)
        close_btn = QtWidgets.QPushButton("关闭", dlg)
        status_lbl = QtWidgets.QLabel("", dlg)

        form = QtWidgets.QFormLayout()
        form.addRow("主页链接：", url_edit)
        form.addRow("请求间隔：", delay_sb)

        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(start_btn)
        btns.addWidget(close_btn)
        btns.addStretch(1)

        lay = QtWidgets.QVBoxLayout(dlg)
        lay.addLayout(form)
        lay.addWidget(status_lbl)
        lay.addLayout(btns)

        def _do_join():
            url = url_edit.text().strip()
            if not url or "steamcommunity.com" not in url:
                status_lbl.setText("请填写正确的 Steam 主页链接。")
                return

            start_btn.setEnabled(False)
            status_lbl.setText("准备中…")
            self.log(f"[*] 添加组：{url}")

            def worker():
                try:
                    poster = self.ensure_poster()
                    if not poster.ensure_logged():
                        self.log('[!] 未检测到登录状态。请先登录。')
                        QtCore.QMetaObject.invokeMethod(status_lbl, "setText", QtCore.Qt.ConnectionType.QueuedConnection,
                            QtCore.Q_ARG(str, "未登录，请先在主窗口点击『登录Steam』"))
                        QtCore.QMetaObject.invokeMethod(start_btn, "setEnabled", QtCore.Qt.ConnectionType.QueuedConnection,
                            QtCore.Q_ARG(bool, True))
                        return

                    res = poster.join_groups_from_profile(url, per_join_delay=float(delay_sb.value()))
                    if res.get("error"):
                        msg = f"失败：{res['error']}"
                    else:
                        msg = f"完成：共 {res.get('total',0)}，成功 {res.get('ok',0)}，失败 {res.get('fail',0)}"

                    QtCore.QMetaObject.invokeMethod(status_lbl, "setText", QtCore.Qt.ConnectionType.QueuedConnection,
                        QtCore.Q_ARG(str, msg))
                    self.log(f"[i] 添加组结果：{msg}")

                except Exception as e:
                    self.log(f"[!] 添加组异常：{e!r}")
                    QtCore.QMetaObject.invokeMethod(status_lbl, "setText", QtCore.Qt.ConnectionType.QueuedConnection,
                        QtCore.Q_ARG(str, f"异常：{e!r}"))
                finally:
                    QtCore.QMetaObject.invokeMethod(start_btn, "setEnabled", QtCore.Qt.ConnectionType.QueuedConnection,
                        QtCore.Q_ARG(bool, True))

            threading.Thread(target=worker, daemon=True).start()

        start_btn.clicked.connect(_do_join)
        close_btn.clicked.connect(dlg.close)
        dlg.exec()

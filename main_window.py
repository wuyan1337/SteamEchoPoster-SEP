# ui/main_window.py
# -*- coding: utf-8 -*-
import time
import threading
import webbrowser
import subprocess
from pathlib import Path

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QSettings

from core.steam_poster import SteamPoster
from widgets.logger import UiLogger
from widgets.card import Card
from ui.styles import apply_modern_style, fade_in

from utils.paths import APP_DIR, GROUPS_FILE, PROFILE_DIR, app_path, POST_WL_FILE, DEL_WL_FILE
from utils.browser import launch_official_chrome_login, fmt_duration
from utils.whitelist import load_list, normalize_url
from utils.i18n import Lang, tr

STEAM_AUTHOR_URL = "https://steamcommunity.com/id/wuyan1337/"

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SteamEchoPost')
        self.resize(880, 900)
        self.setWindowIcon(QtGui.QIcon(app_path("resources", "ico.ico")))
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.settings = QSettings("SEP", "SteamEchoPost")
        saved_lang = str(self.settings.value("lang", Lang.EN.value))
        self.lang = Lang(saved_lang) if saved_lang in (Lang.ZH.value, Lang.EN.value) else Lang.EN

        # ===== 布局 =====
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        self.card = Card(self)
        root.addWidget(self.card, 1)
        body = QtWidgets.QVBoxLayout(self.card)
        body.setContentsMargins(20, 20, 20, 20)
        body.setSpacing(14)

        # 语言控件
        self.lang_label = QtWidgets.QLabel()
        self.lang_combo = QtWidgets.QComboBox()
        self.lang_combo.addItem(tr(self.lang, "lang_cn"), Lang.ZH.value)
        self.lang_combo.addItem(tr(self.lang, "lang_en"), Lang.EN.value)
        idx = self.lang_combo.findData(self.lang.value)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

        # 顶部按钮
        self.btn_launch_chrome = QtWidgets.QPushButton()
        self.btn_open_home = QtWidgets.QPushButton()
        self.open_github_btn = QtWidgets.QPushButton()
        self.leave_btn = QtWidgets.QPushButton()

        # 留言输入/延迟
        self.msg = QtWidgets.QPlainTextEdit()
        self.msg.setPlaceholderText(tr(self.lang, "msg_placeholder"))
        self.delay = QtWidgets.QDoubleSpinBox()
        self.delay.setRange(0.0, 60.0)
        self.delay.setValue(0.8)
        self.delay.setSuffix(tr(self.lang, "delay_suffix"))

        self.groups_path = QtWidgets.QLineEdit(str(GROUPS_FILE))
        self.pick_btn = QtWidgets.QPushButton()

        self.post_wl_path = QtWidgets.QLineEdit(str(POST_WL_FILE))
        self.post_wl_btn  = QtWidgets.QPushButton()
        self.del_wl_path  = QtWidgets.QLineEdit(str(DEL_WL_FILE))
        self.del_wl_btn   = QtWidgets.QPushButton()

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.logger = UiLogger(self.log_view)

        hdr_row = QtWidgets.QHBoxLayout()
        hdr_row.addWidget(self.lang_label)
        hdr_row.addWidget(self.lang_combo)
        hdr_row.addSpacing(10)
        hdr_row.addWidget(self.btn_launch_chrome)
        hdr_row.addWidget(self.btn_open_home)
        hdr_row.addWidget(self.open_github_btn)
        hdr_row.addStretch(1)

        self.lbl_msg = QtWidgets.QLabel()
        self.lbl_delay = QtWidgets.QLabel()
        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        form.addRow(self.lbl_msg, self.msg)
        form.addRow(self.lbl_delay, self.delay)

        path_row = QtWidgets.QHBoxLayout()
        path_row.addWidget(self.groups_path)
        path_row.addWidget(self.pick_btn)


        post_wl_row = QtWidgets.QHBoxLayout()
        post_wl_row.addWidget(self.post_wl_path)
        post_wl_row.addWidget(self.post_wl_btn)

        del_wl_row = QtWidgets.QHBoxLayout()
        del_wl_row.addWidget(self.del_wl_path)
        del_wl_row.addWidget(self.del_wl_btn)

        self.fetch_btn = QtWidgets.QPushButton()
        self.start_btn = QtWidgets.QPushButton()
        self.stop_btn = QtWidgets.QPushButton()
        self.stop_btn.setEnabled(False)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(self.fetch_btn)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.leave_btn)

        self.lbl_groups_path = QtWidgets.QLabel()
        self.lbl_post_wl = QtWidgets.QLabel()
        self.lbl_del_wl = QtWidgets.QLabel()
        self.lbl_logs = QtWidgets.QLabel()

        body.addLayout(hdr_row)
        body.addLayout(form)

        body.addWidget(self.lbl_groups_path)
        body.addLayout(path_row)

        body.addWidget(self.lbl_post_wl)
        body.addLayout(post_wl_row)

        body.addWidget(self.lbl_del_wl)
        body.addLayout(del_wl_row)

        body.addLayout(btn_row)

        body.addWidget(self.lbl_logs)
        body.addWidget(self.log_view, 1)

        self.poster: SteamPoster | None = None
        self.worker_thread: threading.Thread | None = None
        self._stop_flag = threading.Event()

        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)

        self.btn_launch_chrome.clicked.connect(self.on_launch_chrome)
        self.btn_open_home.clicked.connect(self.on_open_home)
        self.open_github_btn.clicked.connect(self.on_open_github)

        self.pick_btn.clicked.connect(self.pick_groups)
        self.fetch_btn.clicked.connect(self.do_fetch)
        self.start_btn.clicked.connect(self.do_start)
        self.stop_btn.clicked.connect(self.do_stop)
        self.leave_btn.clicked.connect(self.leave_no_comment_groups)

        self.post_wl_btn.clicked.connect(self.open_post_whitelist)
        self.del_wl_btn.clicked.connect(self.open_del_whitelist)

        apply_modern_style(self)
        fade_in(self)

        self.apply_texts()

        self.print_welcome_logs()


    # ---------- helpers ----------
    def log(self, s: str):
        self.logger.message.emit(s)

    def ensure_poster(self) -> SteamPoster:
        if self.poster is None:
            self.poster = SteamPoster(log_emit=self.log, headless=True)
        return self.poster

    def on_lang_changed(self):
        data = self.lang_combo.currentData()
        try:
            self.lang = Lang(data)
        except Exception:
            self.lang = Lang.EN
        self.settings.setValue("lang", self.lang.value)
        self.apply_texts()
        self.log_view.clear()

        self.log(f"[i] {tr(self.lang, 'lang_switched', name=(tr(self.lang, 'lang_cn') if self.lang == Lang.ZH else tr(self.lang, 'lang_en')))}")
        self.print_welcome_logs()

    def print_welcome_logs(self):
        self.log(f"[✓] {tr(self.lang, 'welcome_1')}")
        self.log(f"[✓] {tr(self.lang, 'welcome_2')}")
        self.log(f"[✓] {tr(self.lang, 'welcome_use_1')}")
        self.log(f"[✓] {tr(self.lang, 'welcome_use_2')}")
        self.log(f"[✓] {tr(self.lang, 'welcome_use_3')}")
        self.log(f"[✓] {tr(self.lang, 'welcome_use_4')}")
        self.log(f"[✓] {tr(self.lang, 'welcome_use_5')}")



    def apply_texts(self):
        self.setWindowTitle(tr(self.lang, "app_title"))

        self.lang_label.setText(tr(self.lang, "lang_label"))
        self.btn_launch_chrome.setText(tr(self.lang, "login"))
        self.btn_open_home.setText(tr(self.lang, "open_home"))
        self.open_github_btn.setText(tr(self.lang, "open_github"))

        self.lbl_msg.setText(tr(self.lang, "msg_label"))
        self.msg.setPlaceholderText(tr(self.lang, "msg_placeholder"))

        self.lbl_delay.setText(tr(self.lang, "delay_label"))
        self.delay.setSuffix(tr(self.lang, "delay_suffix"))

        self.lbl_groups_path.setText(tr(self.lang, "groups_path_label"))
        self.lbl_post_wl.setText(tr(self.lang, "post_wl_label"))
        self.lbl_del_wl.setText(tr(self.lang, "del_wl_label"))
        self.lbl_logs.setText(tr(self.lang, "log_label"))

        self.pick_btn.setText(tr(self.lang, "open_home") if False else tr(self.lang, "fetch"))  # 只是避免未用变量告警，无实义
        self.fetch_btn.setText(tr(self.lang, "fetch"))
        self.start_btn.setText(tr(self.lang, "start"))
        self.stop_btn.setText(tr(self.lang, "stop"))
        self.leave_btn.setText(tr(self.lang, "leave_scan"))
        self.post_wl_btn.setText(tr(self.lang, "post_wl_label"))
        self.del_wl_btn.setText(tr(self.lang, "del_wl_label"))
        self.pick_btn.setText(self.tr_pick_button())

    def tr_pick_button(self) -> str:
        return "选择 groups.txt" if self.lang == Lang.ZH else "Browse groups.txt"

    # ---------- actions ----------
    def on_launch_chrome(self):
        try:
            launch_official_chrome_login()
            self.log(tr(self.lang, "login_started", profile=PROFILE_DIR))
            self.log(tr(self.lang, "login_warn"))
        except Exception as e:
            self.log(f'[!] 启动失败：{e}')

    def on_open_home(self):
        try:
            webbrowser.open(STEAM_AUTHOR_URL)
        except Exception as e:
            self.log(f"[!] 打开主页失败: {e}")

    def on_open_github(self):
        url = "https://github.com/wuyan1337/SteamEchoPoster-SEP"
        try:
            webbrowser.open(url)
        except Exception as e:
            self.log(f"[!] 打开 GitHub 主页失败: {e}")

    def pick_groups(self):
        caption = "选择 groups.txt" if self.lang == Lang.ZH else "Choose groups.txt"
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, caption, str(APP_DIR), 'Text Files (*.txt)')
        if p:
            self.groups_path.setText(p)

    def do_fetch(self):
        def run():
            try:
                self.log(f"[*] {tr(self.lang, 'fetch_start')}")
                poster = self.ensure_poster()
                if not poster.ensure_logged():
                    self.log(f"[!] {tr(self.lang, 'need_login')}")
                    return
                out = Path(self.groups_path.text())
                out.parent.mkdir(parents=True, exist_ok=True)
                n = poster.fetch_groups(out)
            except Exception as e:
                self.log(f'[!] 抓取异常: {e!r}')
        threading.Thread(target=run, daemon=True).start()

    def do_start(self):
        message = self.msg.toPlainText().strip()
        if not message:
            self.log(f"[!] {tr(self.lang, 'send_empty')}")
            return
        path = Path(self.groups_path.text())
        if not path.exists():
            self.log(f"[!] {tr(self.lang, 'groups_missing')}")
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
            self.log(f"[!] {tr(self.lang, 'groups_empty')}")
            return

        self._stop_flag.clear()
        self.stop_btn.setEnabled(True)
        self.start_btn.setEnabled(False)

        delay = float(self.delay.value())
        send_wait = max(0.8, delay)
        per_group = send_wait + delay
        total_eta = per_group * len(links)
        self.log(f"[i] {tr(self.lang, 'to_send_count', n=len(links))}")
        self.log(f"[i] {tr(self.lang, 'per_group_delay', delay=delay, wait=send_wait)}")
        self.log(f"[i] {tr(self.lang, 'send_eta', eta=fmt_duration(total_eta), sec=total_eta)}")


        def run():
            t0 = time.time()
            try:
                self.log(f"[*] {tr(self.lang, 'start_thread')}")

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
                        self.log(f"[!] {tr(self.lang, 'need_login')}")
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

                    self.log(tr(self.lang, "open_group", i=i, total=total, url=url))

                    ok = False
                    try:
                        ok = poster.post_in_group(url, message, wait_after_send=send_wait)
                    except Exception as e:
                        self.log(f'    [!] 发送异常：{e!r}')

                    if ok:
                        self.log(tr(self.lang, "sent_ok"))
                        sent += 1
                    else:
                        self.log(tr(self.lang, "sent_skip"))

                    if ok:
                        time.sleep(max(0.0, delay))
                    else:
                        time.sleep(min(0.2, delay * 0.25))

                self.log(f"[✓] {tr(self.lang, 'done', ok=sent, total=total)}")

            except Exception as e:
                self.log(f'[!] 发送过程中异常: {e!r}')
            finally:
                elapsed = time.time() - t0
                self.log(f"[i] {tr(self.lang, 'time_real', fmt=fmt_duration(elapsed), sec=elapsed)}")
                self.stop_btn.setEnabled(False)
                self.start_btn.setEnabled(True)

        self.worker_thread = threading.Thread(target=run, daemon=True)
        self.worker_thread.start()

    def leave_no_comment_groups(self):
   
        m = QtWidgets.QMessageBox.question(
            self,
            "确认操作" if self.lang == Lang.ZH else "Confirm",
            "将自动扫描 groups.txt 中的群组，凡是没有留言框（无权限）的将尝试退出。\n\n是否继续？"
            if self.lang == Lang.ZH
            else "This will scan groups in groups.txt and try to leave any group without comment box.\n\nContinue?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if m != QtWidgets.QMessageBox.StandardButton.Yes:
            self.log("[i] 已取消退出扫描。" if self.lang == Lang.ZH else "[i] Leave scan canceled.")
            return

        path = Path(self.groups_path.text())
        if not path.exists():
            self.log(f"[!] {tr(self.lang, 'groups_missing')}")
            return
        raw = path.read_text(encoding='utf-8', errors='ignore')
        links = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith('#')]
        if not links:
            self.log(f"[!] {tr(self.lang, 'groups_empty')}")
            return

        self._stop_flag.clear()
        self.stop_btn.setEnabled(True)

        def run():
            try:
                poster = self.ensure_poster()
                if not poster.ensure_logged():
                    self.log(f"[!] {tr(self.lang, 'need_login')}")
                    return

                total = len(links)
                left_count = 0
                skipped = 0

                del_wl = load_list(self.del_wl_path.text())

                self.log(''.join([
                    '[*] 开始扫描 ', str(total), ' 个群组，自动退出无权限组…'
                ]) if self.lang == Lang.ZH else f"[*] Scanning {total} groups, leaving no-permission ones…")

                for i, url in enumerate(links, 1):
                    if self._stop_flag.is_set():
                        self.log('[*] 已停止。' if self.lang == Lang.ZH else "[*] Stopped.")
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
                            self.log(f'[{i}/{total}] 有留言权限，跳过：{url}' if self.lang == Lang.ZH
                                     else f'[{i}/{total}] Has comment permission, skip: {url}')
                            skipped += 1
                            continue
                    except Exception:
                        pass

                    if normalize_url(url) in del_wl:
                        self.log(f'[{i}/{total}] 删除白名单保护，不退出：{url}' if self.lang == Lang.ZH
                                 else f'[{i}/{total}] Protected by Leave Whitelist, skip: {url}')
                        skipped += 1
                        continue

                    self.log(f'[{i}/{total}] 无留言权限，尝试退出：{url}' if self.lang == Lang.ZH
                             else f'[{i}/{total}] No permission, try leaving: {url}')
                    ok = poster.leave_group_if_possible()
                    if ok:
                        left_count += 1

                    time.sleep(0.3)

                self.log(f'[✓] 扫描完成。退出 {left_count} 个；保留/跳过 {skipped} 个。'
                         if self.lang == Lang.ZH
                         else f'[✓] Scan complete. Left {left_count}; kept/skipped {skipped}.')
            except Exception as e:
                self.log(f'[!] 退出扫描异常: {e!r}' if self.lang == Lang.ZH else f'[!] Leave scan error: {e!r}')
            finally:
                self.stop_btn.setEnabled(False)

        threading.Thread(target=run, daemon=True).start()

    def do_stop(self):
        self._stop_flag.set()

    def open_post_whitelist(self):
        path = Path(self.post_wl_path.text())
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            tmpl = (
                "# 每行一个群链接，例如：\n# https://steamcommunity.com/groups/yourgroup/\n"
                if self.lang == Lang.ZH else
                "# One group URL per line, for example:\n# https://steamcommunity.com/groups/yourgroup/\n"
            )
            path.write_text(tmpl, encoding='utf-8')
        try:
            subprocess.Popen(["notepad.exe", str(path)])
          
        except Exception as e:
            self.log(f"[!] 打开留言白名单失败：{e!r}" if self.lang == Lang.ZH else f"[!] Failed to open Post Whitelist: {e!r}")

    def open_del_whitelist(self):
        path = Path(self.del_wl_path.text())
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            tmpl = (
                "# 每行一个群链接，不会被自动退出：\n# https://steamcommunity.com/groups/yourgroup/\n"
                if self.lang == Lang.ZH else
                "# One group URL per line; these groups will NOT be auto-left:\n# https://steamcommunity.com/groups/yourgroup/\n"
            )
            path.write_text(tmpl, encoding='utf-8')
        try:
            subprocess.Popen(["notepad.exe", str(path)])
        except Exception as e:
            self.log(f"[!] 打开删除白名单失败：{e!r}" if self.lang == Lang.ZH else f"[!] Failed to open Leave Whitelist: {e!r}")

    def on_add_groups_clicked(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("添加组（根据对方主页）" if self.lang == Lang.ZH else "Add Groups (from profile)")
        dlg.setModal(True)
        dlg.resize(520, 160)

        url_edit = QtWidgets.QLineEdit(dlg)
        url_edit.setPlaceholderText(
            "粘贴对方主页链接，例如：https://steamcommunity.com/id/xxxx 或 /profiles/xxxxxxxxxxxxxxx" if self.lang == Lang.ZH
            else "Paste profile URL, e.g. https://steamcommunity.com/id/xxxx or /profiles/xxxxxxxxxxxxxxx"
        )
        url_edit.setText("https://steamcommunity.com/id/")

        delay_sb = QtWidgets.QDoubleSpinBox(dlg)
        delay_sb.setRange(0.0, 3.0)
        delay_sb.setValue(0.3)
        delay_sb.setSuffix(" s")

        start_btn = QtWidgets.QPushButton("开始加入" if self.lang == Lang.ZH else "Start")
        close_btn = QtWidgets.QPushButton("关闭" if self.lang == Lang.ZH else "Close")
        status_lbl = QtWidgets.QLabel("", dlg)

        form = QtWidgets.QFormLayout()
        form.addRow("主页链接：" if self.lang == Lang.ZH else "Profile URL:", url_edit)
        form.addRow("请求间隔：" if self.lang == Lang.ZH else "Delay:", delay_sb)

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
                status_lbl.setText("请填写正确的 Steam 主页链接。" if self.lang == Lang.ZH else "Please enter a valid Steam profile URL.")
                return

            start_btn.setEnabled(False)
            status_lbl.setText("准备中…" if self.lang == Lang.ZH else "Preparing…")
            self.log(f"[*] 添加组：{url}" if self.lang == Lang.ZH else f"[*] Add groups: {url}")

            def worker():
                try:
                    poster = self.ensure_poster()
                    if not poster.ensure_logged():
                        msg = '未登录，请先在主窗口点击「登录Steam」' if self.lang == Lang.ZH else 'Not logged in. Please click "Login Steam" in main window first.'
                        self.log(f"[!] {tr(self.lang, 'need_login')}")
                        QtCore.QMetaObject.invokeMethod(status_lbl, "setText",
                            QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, msg))
                        QtCore.QMetaObject.invokeMethod(start_btn, "setEnabled",
                            QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(bool, True))
                        return

                    res = poster.join_groups_from_profile(url, per_join_delay=float(delay_sb.value()))
                    if res.get("error"):
                        msg = ("失败：" if self.lang == Lang.ZH else "Failed: ") + res["error"]
                    else:
                        msg = ("完成：共 {t}，成功 {o}，失败 {f}".format(
                                t=res.get('total',0), o=res.get('ok',0), f=res.get('fail',0))
                               if self.lang == Lang.ZH else
                               "Done: total {t}, ok {o}, fail {f}".format(
                                t=res.get('total',0), o=res.get('ok',0), f=res.get('fail',0)))

                    QtCore.QMetaObject.invokeMethod(status_lbl, "setText",
                        QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, msg))
                    self.log(f"[i] 添加组结果：{msg}" if self.lang == Lang.ZH else f"[i] Add groups result: {msg}")

                except Exception as e:
                    txt = f"异常：{e!r}" if self.lang == Lang.ZH else f"Error: {e!r}"
                    self.log(f"[!] 添加组异常：{e!r}" if self.lang == Lang.ZH else f"[!] Add groups error: {e!r}")
                    QtCore.QMetaObject.invokeMethod(status_lbl, "setText",
                        QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, txt))
                finally:
                    QtCore.QMetaObject.invokeMethod(start_btn, "setEnabled",
                        QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(bool, True))

            threading.Thread(target=worker, daemon=True).start()

        start_btn.clicked.connect(_do_join)
        close_btn.clicked.connect(dlg.close)
        dlg.exec()


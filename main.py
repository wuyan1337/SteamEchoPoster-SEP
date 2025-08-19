#250819
#QQ1730249
import sys
import os
import time
import threading
import webbrowser
import subprocess
from pathlib import Path
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets, QtCore, QtGui

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

APP_DIR = Path(os.getcwd())
PROFILE_DIR = (APP_DIR / 'chrome_profile').resolve()
GROUPS_FILE = APP_DIR / 'groups.txt'

STEAM_LOGIN_URL = 'https://store.steampowered.com/login/'
MY_GROUPS_URL = 'https://steamcommunity.com/my/groups/'

# ===================== Utilities =====================
def app_path(*parts) -> str:
    base = getattr(sys, '_MEIPASS', Path.cwd())
    return str(Path(base, *parts))

def find_chrome_path() -> str | None:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return None


def launch_official_chrome_login():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome_path()
    if not chrome:
        raise RuntimeError('未找到 Chrome 或 Edge。请安装任意一个，或在源代码中改路径。https://github.com/wuyan1337/SteamEchoPoster-SEP')
    args = [
        chrome,
        f"--user-data-dir={PROFILE_DIR}",
        "--new-window",
        STEAM_LOGIN_URL,
    ]
    try:
        subprocess.Popen(args)
    except Exception as e:
        raise RuntimeError(f'启动官方浏览器失败: {e}')


def make_driver(headless: bool = True) -> webdriver.Chrome:
    opts = webdriver.ChromeOptions()
    opts.add_argument(f"--user-data-dir={PROFILE_DIR}")
    if headless:
        opts.add_argument('--headless=new')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--lang=en-US')
    try:
        driver = webdriver.Chrome(options=opts)
    except WebDriverException as e:
        raise RuntimeError(f'无法启动 Chrome WebDriver: {e}')
    driver.set_window_size(1280, 900)
    driver.set_page_load_timeout(3)
    driver.set_script_timeout(3)
    return driver


def is_logged_in(driver: webdriver.Chrome) -> bool:
    driver.get('https://steamcommunity.com/')
    try:
        driver.find_element(By.CSS_SELECTOR, 'a.global_action_link[href*="login"]')
        return False
    except NoSuchElementException:
        return True

def fmt_duration(sec: float) -> str:
    sec = int(round(sec))
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return f"{m:02d}:{s:02d}"

# ===================== Core automation =====================
class SteamPoster:
    def __init__(self, log_emit, headless=True):
        self._emit = log_emit
        self.driver = make_driver(headless=headless)

    def log(self, s: str):
        self._emit(s)

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    def ensure_logged(self) -> bool:
        ok = is_logged_in(self.driver)
        return ok

    def fetch_groups(self, out_path: Path = GROUPS_FILE) -> int:
        d = self.driver
        self.log('[*] 打开“我的群组”页面...')
        d.get(MY_GROUPS_URL)
        time.sleep(2)

        last_h = 0
        for _ in range(30):
            d.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(0.6)
            h = d.execute_script('return document.body.scrollHeight')
            if h == last_h:
                break
            last_h = h

        js = r"""
        const sels = [
        '.groupBlock .groupTitle a',
        '.groupBlock a[href*="/groups/"]',
        'a.linkTitle[href*="/groups/"]',
        'a[href^="https://steamcommunity.com/groups/"]'
        ];
        let elems = [];
        for (const s of sels) { 
            const t = [...document.querySelectorAll(s)]; 
            if (t.length) { elems = t; break; } 
        }
        const links = [...new Set(
            elems.map(a => new URL(a.getAttribute('href'), location.origin).href.split('?')[0])
        )].filter(h => /^https:\/\/steamcommunity\.com\/groups\/[^\/]+\/?$/.test(h));
        return links;
        """
        try:
            links = d.execute_script(js) or []
        except Exception:
            links = []

        if not links:
            self.log('[!] 未抓到任何群组链接。确认你已加入群组并能访问该页面。')
            return 0
        
        out_path.write_text('\n'.join(links), encoding='utf-8')
        self.log(f'[✓] 已抓取 {len(links)} 个群组，保存到 {out_path.resolve()}')
        return len(links)


    def post_in_group(self, group_url: str, message: str, wait_after_send: float = 1.5) -> bool:
        d = self.driver
        self.log(f'[-] 打开群组：{group_url}')
        from selenium.common.exceptions import TimeoutException

        try:
            d.get(group_url)
        except TimeoutException:
            try:
                d.execute_script("window.stop();")
            except Exception:
                pass

        quick_js = r"""
            const sels = [
            'textarea.commentthread_textarea',
            'textarea[id*="commentthread_"][id$="_textarea"]',
            'textarea[name*="commentthread_"][name$="_textarea"]'
            ];
            for (const s of sels) {
            if (document.querySelector(s)) return true;
            }
            return false;
        """
        try:
            has_textarea = bool(d.execute_script(quick_js))
        except Exception:
            has_textarea = False

        if not has_textarea:
            self.log('    [!] 未找到留言框（快速预检）。跳过。')
            return False

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException

        selectors = [
            'textarea.commentthread_textarea',
            'textarea[id*="commentthread_"][id$="_textarea"]',
            'textarea[name*="commentthread_"][name$="_textarea"]'
        ]
        ta = None
        for sel in selectors:
            try:
                ta = WebDriverWait(d, 2.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                break
            except TimeoutException:
                continue
        if not ta:
            self.log('    [!] 未找到留言框（二次确认）。跳过。')
            return False

        current = ta.get_attribute('value') or ''
        if not current.strip():
            try:
                ta.clear()
            except Exception:
                pass
            ta.send_keys(message)

        btn_selectors = [
            '[id^="commentthread_"][id$="_submit"]',
            '.commentthread_submit, .commentthread_submit_button',
            '.btn_green_white_innerfade[id*="_submit"]',
            'span[role="button"].btn_green_white_innerfade'
        ]
        btn = None
        for sel in btn_selectors:
            try:
                btn = WebDriverWait(d, 2.0).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                break
            except TimeoutException:
                continue
        if not btn:
            self.log('    [!] 未找到发送按钮，跳过。')
            return False

        try:
            btn.click()
        except Exception:
            try:
                d.execute_script('arguments[0].click();', btn)
            except Exception:
                self.log('    [!] 点击失败，跳过。')
                return False

        import time as _t
        _t.sleep(wait_after_send)
        self.log('    [✓] 已发送。')
        return True

# ===================== Thread-safe UI logger =====================
class UiLogger(QtCore.QObject):
    message = QtCore.pyqtSignal(str)
    def __init__(self, widget: QtWidgets.QPlainTextEdit):
        super().__init__()
        self.widget = widget
        self.message.connect(self._append)
    @QtCore.pyqtSlot(str)
    def _append(self, text: str):
        self.widget.appendPlainText(text)
        sb = self.widget.verticalScrollBar(); sb.setValue(sb.maximum())

# ===================== Modern Card Wrapper =====================
class Card(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setGraphicsEffect(self._make_shadow())

    def _make_shadow(self):
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 12)
        shadow.setColor(QtGui.QColor(0, 0, 0, 40))
        return shadow

# ===================== Main Window =====================
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SteamEchoPost')
        self.resize(880, 740)
        self.setWindowIcon(QtGui.QIcon(app_path("ico.ico")))
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)

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


        self.log_view = QtWidgets.QPlainTextEdit(); self.log_view.setReadOnly(True)
        self.logger = UiLogger(self.log_view)

        hdr_row = QtWidgets.QHBoxLayout()
        hdr_row.addWidget(self.btn_launch_chrome)

        self.btn_open_home = QtWidgets.QPushButton('打开作者主页')
        hdr_row.addWidget(self.btn_open_home)

        hdr_row.addStretch(1)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        form.addRow('发送内容:', self.msg)
        form.addRow('每组间隔:', self.delay)

        path_row = QtWidgets.QHBoxLayout()
        path_row.addWidget(self.groups_path)
        path_row.addWidget(self.pick_btn)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(self.fetch_btn)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)

        body.addLayout(hdr_row)
        body.addLayout(form)
        body.addWidget(QtWidgets.QLabel('groups.txt 路径:'))
        body.addLayout(path_row)
        body.addLayout(btn_row)
        body.addWidget(QtWidgets.QLabel('日志输出:'))
        body.addWidget(self.log_view, 1)

        self.poster: SteamPoster | None = None
        self.worker_thread: threading.Thread | None = None
        self._stop_flag = threading.Event()

        self.btn_launch_chrome.clicked.connect(self.on_launch_chrome)
        self.pick_btn.clicked.connect(self.pick_groups)
        self.fetch_btn.clicked.connect(self.do_fetch)
        self.start_btn.clicked.connect(self.do_start)
        self.stop_btn.clicked.connect(self.do_stop)
        self.btn_open_home.clicked.connect(self.on_open_home)

        self.apply_modern_style()
        self.fade_in()
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

    def fade_in(self):
        self.setWindowOpacity(0.0)
        anim = QtCore.QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(280)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutCubic)
        anim.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def apply_modern_style(self):
        self.setStyleSheet("""
            * { font-family: "Segoe UI", "Microsoft YaHei", "Inter", sans-serif; }
            QWidget { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                      stop:0 #f5f7fb, stop:1 #eef1f6); }
            #Card {
                background: rgba(255,255,255,0.72);
                border-radius: 18px;
                border: 1px solid rgba(255,255,255,0.65);
            }
            QLabel { color: #111; font-size: 13px; }
            QLineEdit, QPlainTextEdit, QDoubleSpinBox {
                background: rgba(255,255,255,0.78);
                border: 1px solid rgba(0,0,0,0.12);
                border-radius: 12px;
                padding: 8px 10px;
                selection-background-color: #d0e1ff;
            }
            QPlainTextEdit { min-height: 100px; }
            QPushButton {
                background: rgba(255,255,255,0.70);
                border: 1px solid rgba(0,0,0,0.12);
                border-radius: 12px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.90);
            }
            QPushButton:pressed {
                background: rgba(245,245,245,1.0);
            }
            QScrollBar:vertical {
                background: transparent; width: 10px; margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0,0,0,0.25); border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
        """)

    # ---------- actions ----------
    def on_launch_chrome(self):
        try:
            launch_official_chrome_login()
            self.log(f'[i] 已启动官方浏览器，并使用专用用户目录：{PROFILE_DIR}请在弹出的窗口中完成登录。登录一次后将长期生效。')
            self.log('[!] 登录成功后请手动关闭浏览器 否则会导致后续报错')
            self.log('[!] 登录成功后请手动关闭浏览器 否则会导致后续报错')
            self.log('[!] 登录成功后请手动关闭浏览器 否则会导致后续报错')
        except Exception as e:
            self.log(f'[!] 启动失败：{e}')
    
    def on_open_home(self):
        url = "https://steamcommunity.com/id/wuyan1337/"
        try:
            webbrowser.open(url)
            self.log(f"[i] 已在默认浏览器打开作者主页")
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
                    self.log('[!] 未检测到登录状态。请先登录）”。')
                    return
                out = Path(self.groups_path.text())
                out.parent.mkdir(parents=True, exist_ok=True)
                poster.fetch_groups(out)
            except Exception as e:
                self.log(f'[!] 抓取异常: {e!r}')
        threading.Thread(target=run, daemon=True).start()

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
        lines = []
        for ln in raw.splitlines():
            ln = ln.strip()
            if ln:
                lines.append(ln)
        if not lines and raw.count("https://") > 1:
            parts = raw.split("https://")
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                lines.append("https://" + p)

        links = [ln for ln in lines if ln and not ln.startswith('#')]
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
                poster = self.ensure_poster()
                if not poster.ensure_logged():
                    self.log('[!] 未登录，无法发送。请先登录。')
                    return
                sent = 0
                for i, url in enumerate(links, 1):
                    if self._stop_flag.is_set():
                        self.log('[*] 已停止。')
                        break
                    ok = poster.post_in_group(url, message, wait_after_send=send_wait)
                    sent += int(ok)
                    time.sleep(max(0.0, delay))
                self.log(f'[✓] 完成。成功发送 {sent}/{len(links)} 个群组。')
            except Exception as e:
                self.log(f'[!] 发送过程中异常: {e!r}')
            finally:
                elapsed = time.time() - t0
                self.log(f'[i] 实际耗时：{fmt_duration(elapsed)}（{elapsed:.1f} 秒）')
                self.stop_btn.setEnabled(False)
                self.start_btn.setEnabled(True)
        self.worker_thread = threading.Thread(target=run, daemon=True)
        self.worker_thread.start()

    def do_stop(self):
        self._stop_flag.set()

    

# ===================== app entry =====================
def main():
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QGuiApplication
    from PyQt6 import QtWidgets

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

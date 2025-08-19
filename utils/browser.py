# utils/browser.py
# -*- coding: utf-8 -*-

from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By

STEAM_LOGIN_URL = 'https://store.steampowered.com/login/'
MY_GROUPS_URL = 'https://steamcommunity.com/my/groups/'

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

def launch_official_chrome_login(profile_dir: Path | str = None):
    import subprocess
    from utils.paths import PROFILE_DIR
    prof = Path(profile_dir) if profile_dir else PROFILE_DIR
    prof.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome_path()
    if not chrome:
        raise RuntimeError('未找到 Chrome 或 Edge。请安装一个，或在源码中改路径。')
    args = [chrome, f"--user-data-dir={prof}", "--new-window", STEAM_LOGIN_URL]
    try:
        subprocess.Popen(args)
    except Exception as e:
        raise RuntimeError(f'启动官方浏览器失败: {e}')

def make_driver(headless: bool = True) -> webdriver.Chrome:
    from utils.paths import PROFILE_DIR
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
    driver.set_script_timeout(120)
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

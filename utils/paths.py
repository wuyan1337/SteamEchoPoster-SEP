# utils/paths.py
# -*- coding: utf-8 -*-
import sys, os
from pathlib import Path

def app_path(*parts) -> str:
    base = getattr(sys, '_MEIPASS', Path.cwd())
    return str(Path(base, *parts))

APP_DIR = Path(os.getcwd())
PROFILE_DIR = (APP_DIR / 'chrome_profile').resolve()
GROUPS_FILE = APP_DIR / 'groups.txt'
POST_WL_FILE = APP_DIR / 'post_whitelist.txt'     # 留言白名单
DEL_WL_FILE  = APP_DIR / 'delete_whitelist.txt'   # 删除白名单


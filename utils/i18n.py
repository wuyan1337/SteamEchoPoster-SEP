# utils/i18n.py
from enum import Enum

class Lang(str, Enum):
    ZH = "zh"
    EN = "en"

STR = {
    "zh": {
        "app_title": "SteamEchoPost",
        "login": "登录Steam",
        "open_home": "打开作者主页",
        "open_github": "打开 GitHub 主页",
        "fetch": "抓取群组到 groups.txt（后台）",
        "start": "开始自动发布（后台）",
        "stop": "停止",
        "leave_scan": "退出无权限组（扫描）",
        "groups_path_label": "groups.txt 路径:",
        "msg_label": "发送内容:",
        "msg_placeholder": "要发送的文本…",
        "delay_label": "每组间隔:",
        "delay_suffix": " s/组",
        "post_wl_label": "留言白名单（这些群不会自动留言）:",
        "del_wl_label": "删除白名单（这些群不会被自动退出）:",
        "log_label": "日志输出:",
        "lang_label": "语言:",
        "lang_cn": "中文",
        "lang_en": "English",
        # 日志常用
        "welcome_1": "SteamEchoPost v0.1",
        "welcome_2": "作者QQ1730249",
        "welcome_use_1": "------使用方法------",
        "welcome_use_2": "1. 登录Steam",
        "welcome_use_3": "2. 抓取群",
        "welcome_use_4": "3. 填写发送内容",
        "welcome_use_5": "4. 开始自动发布",
        "need_login": "未检测到登录状态。请先登录。",
        "fetch_start": "开始抓取群组…",
        "groups_missing": "未找到 groups.txt。",
        "groups_empty": "groups.txt 为空。",
        "send_empty": "发送内容为空。",
        "send_eta": "预计总耗时 ≈ {eta}（约 {sec:.1f} 秒）",
        "start_thread": "开始发送任务（已进入后台线程）…",
        "open_group": "[{i}/{total}] 打开群组：{url}",
        "sent_ok": "    [✓] 已发送。",
        "sent_skip": "    [!] 跳过。",
        "done": "完成。成功发送 {ok}/{total} 个群组。",
        "time_real": "实际耗时：{fmt}（{sec:.1f} 秒）",
        "lang_switched": "已切换语言：{name}",
        "login_started": "已启动官方浏览器，并使用专用用户目录：{profile} 请在弹出的窗口中完成登录。登录一次后将长期生效。",
        "login_warn": "登录成功后请手动关闭浏览器，否则会导致后续报错。",
        "fetch_open_groups": "打开“我的群组”页面...",
        "fetch_saved_n": "已抓取 {n} 个群组，保存到 {path}",
        "scan_start": "扫描 {total} 个群组，自动退出无权限组…",
        "has_comment_skip": "[{i}/{total}] 有留言权限，跳过：{url}",
        "leave_protected": "[{i}/{total}] 删除白名单保护，不退出：{url}",
        "no_perm_try_leave": "[{i}/{total}] 无留言权限，尝试退出：{url}",
        "stopped": "已停止。",
        "scan_done": "扫描完成。退出 {left} 个；保留/跳过 {skip} 个。",
        "leave_error": "退出扫描异常: {err}",

        # 发送任务前 3 行（也做成可翻译）
        "to_send_count": "待发送群组数: {n}",
        "per_group_delay": "每组间隔: {delay:.2f}s，点击后等待: {wait:.2f}s",
    },
    "en": {
        "app_title": "SteamEchoPost",
        "login": "Login Steam",
        "open_home": "Open Author Profile",
        "open_github": "Open GitHub",
        "fetch": "Fetch groups to groups.txt (background)",
        "start": "Start Auto Posting (background)",
        "stop": "Stop",
        "leave_scan": "Leave No-Permission Groups (scan)",
        "groups_path_label": "groups.txt Path:",
        "msg_label": "Message:",
        "msg_placeholder": "Text to send…",
        "delay_label": "Delay per group:",
        "delay_suffix": " s/group",
        "post_wl_label": "Post Whitelist (won’t auto-post):",
        "del_wl_label": "Leave Whitelist (won’t be auto-left):",
        "log_label": "Logs:",
        "lang_label": "Language:",
        "lang_cn": "中文",
        "lang_en": "English",
        # logs
        "welcome_1": "SteamEchoPost v0.1",
        "welcome_2": "Author QQ1730249",
        "welcome_use_1": "------How to use------",
        "welcome_use_2": "1. Login Steam",
        "welcome_use_3": "2. Fetch Groups",
        "welcome_use_4": "3. Fill Message",
        "welcome_use_5": "4. Start Auto Posting",
        "need_login": "Not logged in. Please login first.",
        "fetch_start": "Fetching groups…",
        "groups_missing": "groups.txt not found.",
        "groups_empty": "groups.txt is empty.",
        "send_empty": "Message is empty.",
        "send_eta": "Estimated total time ≈ {eta} (about {sec:.1f} sec)",
        "start_thread": "Start sending task (worker thread entered)…",
        "open_group": "[{i}/{total}] Open group: {url}",
        "sent_ok": "    [✓] Sent.",
        "sent_skip": "    [!] Skipped.",
        "done": "Done. Sent {ok}/{total} groups successfully.",
        "time_real": "Actual time: {fmt} ({sec:.1f} sec)",
        # 英文包对应翻译：
        "login_started": "Launched the official browser with profile: {profile}. Please complete login in the popup window. It will persist.",
        "login_warn": "After logging in, please close the browser manually to avoid later errors.",

        "fetch_open_groups": "Opening “My Groups” page...",
        "fetch_saved_n": "Fetched {n} groups, saved to {path}",

        "scan_start": "Scanning {total} groups, leaving no-permission ones…",
        "has_comment_skip": "[{i}/{total}] Has comment permission, skip: {url}",
        "leave_protected": "[{i}/{total}] Protected by Leave Whitelist, skip: {url}",
        "no_perm_try_leave": "[{i}/{total}] No permission, try leaving: {url}",
        "stopped": "Stopped.",
        "scan_done": "Scan complete. Left {left}; kept/skipped {skip}.",
        "leave_error": "Leave scan error: {err}",

        "to_send_count": "Groups to send: {n}",
        "per_group_delay": "Delay per group: {delay:.2f}s, wait after click: {wait:.2f}s",

        "lang_switched": "Language switched: {name}",

    }
}

def tr(lang: Lang, key: str, **kwargs) -> str:
    s = STR.get(lang.value, {}).get(key, key)
    if kwargs:
        try:
            return s.format(**kwargs)
        except Exception:
            return s
    return s

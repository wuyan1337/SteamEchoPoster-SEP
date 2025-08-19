# core/steam_poster.py
# -*- coding: utf-8 -*-
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException
)

from utils.paths import PROFILE_DIR, GROUPS_FILE
from utils.browser import MY_GROUPS_URL, make_driver, is_logged_in

class SteamPoster:
    def __init__(self, log_emit, headless: bool = True):
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
        return is_logged_in(self.driver)

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

        Path(out_path).write_text('\n'.join(links), encoding='utf-8')
        self.log(f'[✓] 已抓取 {len(links)} 个群组，保存到 {Path(out_path).resolve()}')
        return len(links)

    def post_in_group(self, group_url: str, message: str, wait_after_send: float = 1.5) -> bool:
        d = self.driver
        try:
            d.get(group_url)
        except TimeoutException:
            try:
                d.execute_script("window.stop();")
            except Exception:
                pass

        # 快速预检
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
            return False

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
            return False

        try:
            btn.click()
        except Exception:
            try:
                d.execute_script('arguments[0].click();', btn)
            except Exception:
                return False

        time.sleep(wait_after_send)
        return True

    def has_comment_box(self) -> bool:
        """当前群组页是否存在留言框（快速预检，避免长等待）。"""
        d = self.driver
        quick_js = r"""
            const sels = [
              'textarea.commentthread_textarea',
              'textarea[id*="commentthread_"][id$="_textarea"]',
              'textarea[name*="commentthread_"][name$="_textarea"]'
            ];
            for (const s of sels) { if (document.querySelector(s)) return true; }
            return false;
        """
        try:
            return bool(d.execute_script(quick_js))
        except Exception:
            return False


    def leave_group_if_possible(self) -> bool:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        d = self.driver

        link = None
        try:
            link = WebDriverWait(d, 2.0).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="javascript:ConfirmLeaveGroup"]'))
            )
        except Exception:
            try:
                link = d.execute_script("return document.querySelector('a[href^=\"javascript:ConfirmLeaveGroup\"]');")
            except Exception:
                link = None

        if link:
            try:
                d.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
            except Exception:
                pass
            try:
                link.click()
            except Exception:
                try:
                    d.execute_script('arguments[0].click();', link)
                except Exception:
                    link = None

            if link:
                try:
                    WebDriverWait(d, 3.0).until(EC.alert_is_present())
                    alert = d.switch_to.alert
                    alert.accept()  
                    time.sleep(0.8)
                    self.log('    [✓] 已提交退出（确认弹窗）。')
                    return True
                except Exception:
                    pass

        try:
            ok = d.execute_script("""
                var f = document.getElementById('leave_group_form');
            if (f) { f.submit(); return true; } else { return false; }
            """)
            if ok:
                time.sleep(0.8)
                self.log('    [✓] 已提交退出（表单兜底）。')
                return True
        except Exception:
            pass

        self.log('    [!] 未能触发退出操作。')
        return False

    def join_groups_from_profile(self, profile_url: str, per_join_delay: float = 0.3) -> dict:
        """
        打开一个 Steam 主页（/id/xxx 或 /profiles/xxxxxxxxxxxxx），读取该用户的所有群组并逐个加入。
        返回：{total, ok, fail, joined:[], failed:[], error?}
        """
        d = self.driver
        self.log(f'[*] 打开对方主页：{profile_url}')

        try:
            orig_script_to = d.timeouts.script
        except Exception:
            orig_script_to = None
        try:
            orig_page_to = d.timeouts.page_load
        except Exception:
            orig_page_to = None
        try:
            d.set_script_timeout(300)
        except Exception:
            pass
        try:
            d.set_page_load_timeout(15)
        except Exception:
            pass

        try:
            try:
                d.get(profile_url)
            except Exception:
                try:
                    d.execute_script("window.stop();")
                except Exception:
                    pass

            js = r"""
            var done = arguments[0];
            var delayMs = arguments[1] || 0;

            (async () => {
                const sleep = (ms) => new Promise(r => setTimeout(r, ms));

                const getSessionID = () => {
                    try { if (typeof g_sessionID !== 'undefined' && g_sessionID) return g_sessionID; } catch (e) {}
                    try {
                        const m = document.cookie.match(/(?:^|;\s*)sessionid=([^;]+)/i);
                        if (m && m[1]) return decodeURIComponent(m[1]);
                    } catch (e) {}
                    return null;
                };

                const getSteamIdFromPage = async () => {
                    let m = location.pathname.match(/\/profiles\/(\d{17})/);
                    if (m) return m[1];
                    m = location.pathname.match(/\/id\/([^\/]+)/);
                    if (m) {
                        const vanity = m[1];
                        const resp = await fetch(`https://steamcommunity.com/id/${vanity}/?xml=1`, { credentials: 'include' });
                        if (!resp.ok) throw new Error('获取 vanity 对应 steamID64 失败：HTTP ' + resp.status);
                        const txt = await resp.text();
                        const sid = (txt.match(/<steamID64>(\d{17})<\/steamID64>/) || [])[1];
                        if (sid) return sid;
                    }
                    try { if (window.g_rgProfileData && g_rgProfileData.steamid) return g_rgProfileData.steamid; } catch (e) {}
                    return null;
                };

                try {
                    const sessionID = getSessionID();
                    if (!sessionID) throw new Error('无法获取 sessionID（请确认已登录 steamcommunity.com）');

                    const steamID = await getSteamIdFromPage();
                    if (!steamID) throw new Error('无法确定对方 steamID（主页不可访问或未公开）');

                    const xmlResp = await fetch(`https://steamcommunity.com/profiles/${steamID}/?xml=1`, { credentials: 'include' });
                    if (!xmlResp.ok) throw new Error('获取群组列表失败：HTTP ' + xmlResp.status);
                    const xmlText = await xmlResp.text();
                    const parser = new DOMParser();
                    const xmlDoc = parser.parseFromString(xmlText, 'text/xml');
                    const gids = Array.from(xmlDoc.querySelectorAll('groupID64'))
                                      .map(n => (n.textContent || '').trim())
                                      .filter(Boolean);

                    let ok = 0, fail = 0;
                    const joined = [], failed = [];

                    for (const gid of gids) {
                        try {
                            const resp = await fetch(`https://steamcommunity.com/gid/${gid}`, {
                                method: 'POST',
                                credentials: 'include',
                                headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' },
                                body: new URLSearchParams({ action: 'join', sessionID })
                            });
                            if (resp.ok) { ok++; joined.push(gid); }
                            else { fail++; failed.push(gid); }
                        } catch (e) { fail++; failed.push(gid); }
                        if (delayMs > 0) await sleep(delayMs);
                    }

                    return { total: gids.length, ok, fail, joined, failed };
                } catch (err) {
                    return { error: String(err) };
                }
            })().then(done).catch(e => done({ error: String(e) }));
            """
            res = d.execute_async_script(js, int(max(0.0, per_join_delay) * 1000))
            if isinstance(res, dict):
                if res.get('error'):
                    self.log(f"[!] 添加组失败：{res['error']}")
                else:
                    self.log(f"[✓] 加入完成：共 {res.get('total',0)}，成功 {res.get('ok',0)}，失败 {res.get('fail',0)}")
                return res
            else:
                self.log("[!] 未返回有效结果。")
                return {"error": "no_result"}

        except Exception as e:
            self.log(f"[!] 执行脚本异常: {e!r}")
            return {"error": repr(e)}

        finally:
            try:
                if orig_script_to is not None:
                    d.set_script_timeout(orig_script_to.total_seconds() if hasattr(orig_script_to, 'total_seconds') else int(orig_script_to))
                else:
                    d.set_script_timeout(30)
            except Exception:
                pass
            try:
                if orig_page_to is not None:
                    d.set_page_load_timeout(orig_page_to.total_seconds() if hasattr(orig_page_to, 'total_seconds') else int(orig_page_to))
                else:
                    d.set_page_load_timeout(10)
            except Exception:
                pass



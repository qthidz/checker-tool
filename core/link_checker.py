# core/link_checker.py - Module kiểm tra link sống/chết
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

class LinkCheckWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int, int) # live, total

    def __init__(self, urls, proxy=None):
        super().__init__()
        self.urls = urls
        self.proxy = proxy
        self.is_running = True

    def run(self):
        live_count = 0
        total = len(self.urls)
        
        self.log_signal.emit(f"[*] Bắt đầu kiểm tra {total} link...")

        session = requests.Session()
        session.headers.update(HEADERS)
        if self.proxy:
            p = self.proxy if self.proxy.startswith("http") else "http://" + self.proxy
            session.proxies = {"http": p, "https": p}

        for i, url in enumerate(self.urls):
            if not self.is_running: break
            url = url.strip()
            if not url: continue

            try:
                # Gửi request với timeout 15s, không theo dõi redirect quá sâu
                r = session.get(url, timeout=15, verify=False, allow_redirects=True)
                
                # Đánh giá dựa trên HTTP Status
                if r.status_code in (200, 201, 202, 301, 302):
                    live_count += 1
                    self.log_signal.emit(f"[{i+1}/{total}] [LIVE] HTTP {r.status_code} | {url[:60]}...")
                else:
                    self.log_signal.emit(f"[{i+1}/{total}] [DEAD] HTTP {r.status_code} | {url[:60]}...")
                    
            except requests.exceptions.Timeout:
                self.log_signal.emit(f"[{i+1}/{total}] [DEAD] Timeout | {url[:60]}...")
            except requests.exceptions.RequestException as e:
                self.log_signal.emit(f"[{i+1}/{total}] [DEAD] Lỗi mạng | {url[:60]}...")
            except Exception as e:
                self.log_signal.emit(f"[{i+1}/{total}] [DEAD] Lỗi | {url[:60]}...")

        self.finished_signal.emit(live_count, total)
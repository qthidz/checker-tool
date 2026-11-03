# core/cc_engine.py - Bản Full (Tích hợp ZCCV-V2 Smart Extract & Webhook)
import os
import re
import json
import time
import threading
import queue
import urllib.request
import csv
import zipfile
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtCore import QObject, pyqtSlot, QTimer
from PyQt5.QtWidgets import QFileDialog, QApplication
import requests

# ─── Regex & Helpers ─────────────────────────────────────────────────────────
P_CC = re.compile(
    r'(?<!\d)([3-6]\d{14,18})\s*[\|/\\ ]\s*(0?[1-9]|1[0-2])\s*[\|/\\ ]\s*(20\d{2}|\d{2})\s*[\|/\\ ]\s*(\d{3,4})(?!\d)'
)
P_EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
P_PHONE = re.compile(r'(?i)(?:phone|tel|mobile)[\s\t:=]*(\+?[\d\s\-\(\)]{8,20})')
P_IP = re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b')

def norm_year(y): return '20' + y if len(y) == 2 else y

def luhn_check(num):
    digits = [int(d) for d in num]
    digits.reverse()
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9: d -= 9
        total += d
    return total % 10 == 0

def clean_phone(p):
    c = re.sub(r'[^\d+]', '', p)
    if c.startswith('+'): c = '+' + c[1:].replace('+', '')
    else: c = c.replace('+', '')
    digits = c[1:] if c.startswith('+') else c
    return c if 8 <= len(digits) <= 15 else ""

def is_valid(cc, m, y, cvv):
    if not (1 <= int(m) <= 12): return False
    if cvv in ('000', '0000'): return False
    if not luhn_check(cc): return False
    return True

def fmt(cc, m, y, cvv): return f'{cc}|{m.zfill(2)}|{norm_year(y)}|{cvv}'

# ─── ZCCV-V2 Smart Extract ───────────────────────────────────────────────────
def extract_cards_zccv(content):
    """Bóc tách thẻ từ nhiều định dạng (chia block, pipe, space)"""
    cards = []
    separators = re.split(r"[━─=#\-]{10,}|\n{3,}", content)
    for block in separators:
        card_patterns = [
            r"(?:Card\s*Number|Card\s*No|CN|Number)[:\s]*[^\d]*(\d{12,19})",
            r"(?:Card)[:\s]*[^\d]*(\d{12,19})",
            r"^(\d{12,19})$"
        ]
        card_num = None
        for pattern in card_patterns:
            match = re.search(pattern, block, re.I | re.M)
            if match:
                card_num = match.group(1); break
        if not card_num: continue
        
        exp_patterns = [
            r"(?:Exp(?:iration)?|Expiry|DATE|Valid)[:\s]*(\d{1,2})\s*[/\-]\s*(\d{2,4})",
            r"(\d{1,2})\s*/\s*(\d{2,4})"
        ]
        exp_match = None
        for pattern in exp_patterns:
            exp_match = re.search(pattern, block, re.I)
            if exp_match: break
        if not exp_match: continue
        
        cvv_patterns = [
            r"(?:CVC|CVV|Security\s*Code)[:\s]*(\d{3,4})",
            r"\b(\d{3,4})\b"
        ]
        cvv_val = None
        for pattern in cvv_patterns:
            cvv_match = re.search(pattern, block, re.I)
            if cvv_match:
                val = cvv_match.group(1)
                if len(val) in [3, 4] and val != card_num[:4]:
                    cvv_val = val; break
        if not cvv_val: continue
        
        month = exp_match.group(1).zfill(2)
        year = exp_match.group(2)
        if len(year) == 2: year = "20" + year
        
        cards.append(f"{card_num}|{month}|{year}|{cvv_val}")
        
    for line in content.split('\n'):
        pipe_match = re.search(r'(\d{12,19})\s*\|\s*(\d{1,2})\s*\|\s*(\d{2,4})\s*\|\s*(\d{3,4})', line)
        if pipe_match:
            m = pipe_match.group(2).zfill(2); y = pipe_match.group(3)
            if len(y) == 2: y = "20" + y
            cards.append(f"{pipe_match.group(1)}|{m}|{y}|{pipe_match.group(4)}")
            
        space_match = re.search(r'(\d{12,19})\s+(\d{1,2})[/\-](\d{2,4})\s+(\d{3,4})', line)
        if space_match:
            m = space_match.group(2).zfill(2); y = space_match.group(3)
            if len(y) == 2: y = "20" + y
            cards.append(f"{space_match.group(1)}|{m}|{y}|{space_match.group(4)}")
            
    return cards

# ─── Engine ──────────────────────────────────────────────────────────────────
class CCEngine(QObject):
    def __init__(self, parent_tab):
        super().__init__()
        self.page = None
        self.parent_tab = parent_tab
        self.extracted_cards = {}
        self.bin_cache = {}
        self.log_info_cache = {}
        self.is_scanning = False
        self.cancel_scan = False
        self.folder_path = ""
        self.api_queue = queue.Queue()
        self.lock = threading.Lock()
        self.bins_checked = 0
        self.bins_total = 0
        self.files_scanned = 0
        self.total_files = 0
        
        self.history_file = os.path.join(os.getcwd(), 'scanned_history.json')
        self.cards_db_file = os.path.join(os.getcwd(), 'cards_db.json')
        self.scanned_history = {}
        
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.scanned_history = json.load(f)
            except: pass

        self._js_queue = queue.Queue()
        self._stats_dirty = False
        self._last_stats_time = 0
        self._page_loaded = False

        for _ in range(8):
            threading.Thread(target=self._api_worker, daemon=True).start()

    def set_page(self, page):
        self.page = page
        self._timer = QTimer()
        self._timer.timeout.connect(self._flush_js)
        self._timer.start(60)

    @pyqtSlot()
    def pageLoaded(self):
        self._page_loaded = True

    def _flush_js(self):
        if not self._page_loaded or not self.page: return
        count = 0
        while not self._js_queue.empty() and count < 25:
            try:
                self.page.runJavaScript(self._js_queue.get_nowait())
                count += 1
            except: break
                
        if self._stats_dirty:
            now = time.time()
            if now - self._last_stats_time >= 0.3:
                self._last_stats_time = now
                self._stats_dirty = False
                stats = {
                    "files": self.files_scanned, "totalFiles": self.total_files,
                    "cards": len(self.extracted_cards),
                    "bins": self.bins_checked, "totalBins": self.bins_total
                }
                self.page.runJavaScript(f"updateStats({json.dumps(stats)})")

    def _js(self, code): self._js_queue.put(code)
    def _mark_stats_dirty(self): self._stats_dirty = True

    @pyqtSlot()
    def selectFolder(self):
        folder = QFileDialog.getExistingDirectory(None, "Select Log Folder")
        if folder:
            self.folder_path = folder
            self._js(f"onFolderSelected({json.dumps(folder)})")

    @pyqtSlot()
    def startScan(self):
        if not self.folder_path or self.is_scanning: return
        self.extracted_cards.clear(); self.bin_cache.clear(); self.log_info_cache.clear()
        self.bins_checked = 0; self.bins_total = 0; self.files_scanned = 0; self.total_files = 0
        self.is_scanning = True; self.cancel_scan = False
        self._js("onScanStarted()")
        threading.Thread(target=self._scan_thread, daemon=True).start()

    @pyqtSlot()
    def stopScan(self):
        if self.is_scanning:
            self.cancel_scan = True
            self._js('setStatus("Stopping scan...")')

    @pyqtSlot(str)
    def openFolder(self, path):
        if os.path.exists(path):
            try: os.startfile(path)
            except: pass

    @pyqtSlot()
    def copyAll(self):
        if not self.extracted_cards: return self._js('showToast("No cards")')
        lines = []
        for d in self.extracted_cards.values():
            p = d["parts"]
            line = f"{p[0]}|{p[1]}|{p[2]}|{p[3]}"
            i = d["info"]
            if i.get("brand") and i["brand"] not in ("N/A", "..."): line += f" | {i['brand']} | {i['type']} | {i['level']} | {i['bank']} | {i['country']}"
            if d.get("email"): line += f" | {d['email']}"
            if d.get("phone"): line += f" | {d['phone']}"
            if d.get("ip"): line += f" | {d['ip']}"
            if d.get("holder"): line += f" | {d['holder']}"
            lines.append(line)
        QApplication.clipboard().setText("\n".join(lines))
        self._js(f'showToast("Copied {len(lines)} cards!")')

    @pyqtSlot()
    def exportAll(self):
        if not self.extracted_cards: return self._js('showToast("No cards")')
        path, _ = QFileDialog.getSaveFileName(None, "Export", "", "Text Files (*.txt)")
        if not path: return
        with open(path, 'w', encoding='utf-8') as f:
            for d in self.extracted_cards.values():
                p = d["parts"]
                line = f"{p[0]}|{p[1]}|{p[2]}|{p[3]}"
                i = d["info"]
                if i.get("brand") and i["brand"] not in ("N/A", "..."): line += f" | {i['brand']} | {i['type']} | {i['level']} | {i['bank']} | {i['country']}"
                if d.get("email"): line += f" | {d['email']}"
                if d.get("ip"): line += f" | {d['ip']}"
                if d.get("holder"): line += f" | {d['holder']}"
                f.write(line + "\n")
        self._js(f'showToast("Exported!")')

    @pyqtSlot()
    def exportCSV(self):
        if not self.extracted_cards: return self._js('showToast("No cards")')
        path, _ = QFileDialog.getSaveFileName(None, "Export CSV", "", "CSV Files (*.csv)")
        if not path: return
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Card Number", "Exp", "CVV", "Brand", "Type", "Level", "Bank", "Country", "Email", "Phone", "IP", "Holder", "Log Path"])
            for d in self.extracted_cards.values():
                p = d["parts"]; i = d["info"]
                writer.writerow([p[0], f"{p[1]}/{p[2]}", p[3], i.get("brand",""), i.get("type",""), i.get("level",""), i.get("bank",""), i.get("country",""), d.get("email",""), d.get("phone",""), d.get("ip",""), d.get("holder",""), d.get("log_root","")])
        self._js(f'showToast("Exported to CSV!")')

    def _scan_thread(self):
        all_files = []
        for root, _, files in os.walk(self.folder_path):
            if self.cancel_scan: break
            for fn in files: all_files.append(os.path.join(root, fn))

        if self.cancel_scan:
            self._js('onScanComplete("Scan stopped.")'); self.is_scanning = False; return

        self.total_files = len(all_files)
        self._mark_stats_dirty()
        self._js(f'setStatus("Found {self.total_files} files - scanning...")')

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = []
            for fpath in all_files:
                if self.cancel_scan: break
                if fpath.lower().endswith('.zip'): futures.append(pool.submit(self._process_zip, fpath))
                else: futures.append(pool.submit(self._process_file, fpath))
            for future in futures: future.result()

        try:
            with open(self.history_file, 'w', encoding='utf-8') as f: json.dump(self.scanned_history, f)
            with open(self.cards_db_file, 'w', encoding='utf-8') as f: json.dump(list(self.extracted_cards.values()), f)
        except: pass

        self._stats_dirty = True; self._last_stats_time = 0
        msg = f"Done - {len(self.extracted_cards)} cards extracted" if not self.cancel_scan else "Scan stopped."
        self._js(f'onScanComplete("{msg}")'); self.is_scanning = False

    def _process_file(self, fpath):
        if self.cancel_scan: return
        try:
            mtime = os.path.getmtime(fpath)
            if fpath in self.scanned_history and self.scanned_history[fpath] == mtime:
                with self.lock: self.files_scanned += 1
                self._mark_stats_dirty(); return
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
        except:
            with self.lock: self.files_scanned += 1
            self._mark_stats_dirty(); return

        with self.lock: self.files_scanned += 1
        
        # Sử dụng ZCCV Smart Extract thay vì P_CC
        zccv_cards = extract_cards_zccv(content)
        # Sử dụng P_CC làm fallback
        for cc, m, y, cvv in P_CC.findall(content):
            if is_valid(cc, m, y, cvv):
                zccv_cards.append(fmt(cc, m, y, cvv))

        found = {}
        for c_fmt in zccv_cards:
            if c_fmt not in found: 
                # Tìm ngữ cảnh của dòng chứa thẻ để bóc email/ip
                parts = c_fmt.split('|')
                for line in content.splitlines():
                    if parts[0] in line:
                        found[c_fmt] = line
                        break
                else:
                    found[c_fmt] = ""

        if not found: self._mark_stats_dirty(); return

        dir_path = os.path.dirname(fpath); log_root = dir_path
        while dir_path and dir_path != self.folder_path:
            if os.path.exists(os.path.join(dir_path, 'information.txt')) or os.path.basename(dir_path).lower() in ['creditcards', 'autofill']:
                if os.path.basename(dir_path).lower() in ['creditcards', 'autofill']: log_root = os.path.dirname(dir_path)
                else: log_root = dir_path
                break
            dir_path = os.path.dirname(dir_path)

        with self.lock: cached_info = self.log_info_cache.get(log_root)
        if cached_info: info_data = cached_info
        else:
            info_data = {"email": "", "phone": "", "ip": "", "holder": ""}
            info_path = os.path.join(log_root, "information.txt")
            if os.path.exists(info_path):
                try:
                    with open(info_path, 'r', encoding='utf-8', errors='ignore') as inf:
                        icontent = inf.read()
                        m_ip = re.search(r'\b(?:IP|ip)\s*[:=]\s*(\d{1,3}(?:\.\d{1,3}){3})\b', icontent)
                        if m_ip: info_data["ip"] = m_ip.group(1)
                        else:
                            m_ip2 = P_IP.search(icontent)
                            if m_ip2: info_data["ip"] = m_ip2.group(1)
                except: pass

            autofill_dir = os.path.join(log_root, "Autofill")
            if os.path.exists(autofill_dir):
                for afn in os.listdir(autofill_dir):
                    if afn.endswith('.txt'):
                        try:
                            with open(os.path.join(autofill_dir, afn), 'r', encoding='utf-8', errors='ignore') as af:
                                text = af.read()
                                if not info_data.get("email"):
                                    amatch = P_EMAIL.search(text)
                                    if amatch: info_data["email"] = amatch.group(0)
                                if not info_data.get("phone"):
                                    pmatch = P_PHONE.search(text)
                                    if pmatch:
                                        cleaned = clean_phone(pmatch.group(1))
                                        if cleaned: info_data["phone"] = cleaned
                                if info_data.get("email") and info_data.get("phone"): break
                        except: pass
            with self.lock: self.log_info_cache[log_root] = info_data

        email = info_data["email"]; phone = info_data.get("phone", ""); ip = info_data["ip"]; holder = info_data.get("holder", "")
        new_cards = []
        with self.lock:
            for c, line_ctx in found.items():
                if c in self.extracted_cards: continue
                parts = c.split('|'); bin6 = parts[0][:6]

                m_email = P_EMAIL.search(line_ctx); c_email = m_email.group(0) if m_email else email
                m_phone = P_PHONE.search(line_ctx); c_phone = ""
                if m_phone: c_phone = clean_phone(m_phone.group(1))
                if not c_phone: c_phone = phone
                m_ip = P_IP.search(line_ctx); c_ip = m_ip.group(1) if m_ip else ip
                c_holder = holder
                line_parts = line_ctx.split('|')
                if len(line_parts) >= 5 and not c_holder:
                    pot_name = line_parts[4].strip()
                    if pot_name and '@' not in pot_name and not re.match(r'^\d', pot_name): c_holder = pot_name

                cached = self.bin_cache.get(bin6)
                if isinstance(cached, dict): info = cached
                else:
                    info = {"brand": "...", "type": "...", "level": "...", "bank": "...", "country": "..."}
                    if cached is None:
                        self.bin_cache[bin6] = "FETCHING"; self.bins_total += 1; self.api_queue.put(bin6)

                self.extracted_cards[c] = {
                    "bin": bin6, "parts": parts, "info": info,
                    "email": c_email, "phone": c_phone, "ip": c_ip, "holder": c_holder, "log_root": log_root
                }
                new_cards.append({
                    "cc": parts[0], "exp": f"{parts[1]}/{parts[2]}", "cvv": parts[3], "bin": bin6,
                    "brand": info["brand"], "type": info["type"], "level": info["level"], "bank": info["bank"], "country": info["country"],
                    "email": c_email, "phone": c_phone, "ip": c_ip, "holder": c_holder, "log_root": log_root
                })

        self.scanned_history[fpath] = mtime
        if new_cards: self._js(f"addCards({json.dumps(new_cards)})")
        self._mark_stats_dirty()

    def _process_zip(self, zpath):
        # (Giữ nguyên logic cũ, chỉ thay P_CC.findall bằng extract_cards_zccv)
        if self.cancel_scan: return
        try:
            mtime = os.path.getmtime(zpath)
            if zpath in self.scanned_history and self.scanned_history[zpath] == mtime:
                with self.lock: self.files_scanned += 1
                self._mark_stats_dirty(); return
            with zipfile.ZipFile(zpath, 'r') as z:
                txt_files = [f for f in z.namelist() if f.lower().endswith('.txt')]
                for txt_name in txt_files:
                    if self.cancel_scan: break
                    try: content = z.read(txt_name).decode('utf-8', errors='ignore')
                    except: continue
                    
                    zccv_cards = extract_cards_zccv(content)
                    for cc, m, y, cvv in P_CC.findall(content):
                        if is_valid(cc, m, y, cvv):
                            zccv_cards.append(fmt(cc, m, y, cvv))

                    found = {}
                    for c_fmt in zccv_cards:
                        if c_fmt not in found: 
                            parts = c_fmt.split('|')
                            for line in content.splitlines():
                                if parts[0] in line:
                                    found[c_fmt] = line
                                    break
                            else:
                                found[c_fmt] = ""
                    
                    if not found: continue
                        
                    info_data = {"email": "", "phone": "", "ip": "", "holder": ""}
                    dir_path = os.path.dirname(txt_name)
                    
                    info_txt_path = os.path.join(dir_path, "information.txt").replace('\\', '/')
                    if info_txt_path in z.namelist():
                        try:
                            icontent = z.read(info_txt_path).decode('utf-8', errors='ignore')
                            m_ip = re.search(r'\b(?:IP|ip)\s*[:=]\s*(\d{1,3}(?:\.\d{1,3}){3})\b', icontent)
                            if m_ip: info_data["ip"] = m_ip.group(1)
                            else:
                                m_ip2 = P_IP.search(icontent)
                                if m_ip2: info_data["ip"] = m_ip2.group(1)
                        except: pass
                    
                    autofill_prefix = os.path.join(dir_path, "Autofill/").replace('\\', '/')
                    autofill_files = [f for f in z.namelist() if f.startswith(autofill_prefix) and f.endswith('.txt')]
                    for afn in autofill_files:
                        try:
                            af_content = z.read(afn).decode('utf-8', errors='ignore')
                            if not info_data.get("email"):
                                amatch = P_EMAIL.search(af_content)
                                if amatch: info_data["email"] = amatch.group(0)
                            if not info_data.get("phone"):
                                pmatch = P_PHONE.search(af_content)
                                if pmatch: 
                                    cleaned = clean_phone(pmatch.group(1))
                                    if cleaned: info_data["phone"] = cleaned
                            if info_data.get("email") and info_data.get("phone"): break
                        except: pass

                    email = info_data["email"]; phone = info_data.get("phone", ""); ip = info_data["ip"]; holder = info_data.get("holder", "")
                    log_root = zpath + "::" + dir_path
                    new_cards = []
                    
                    with self.lock:
                        for c, line_ctx in found.items():
                            if c in self.extracted_cards: continue
                            parts = c.split('|'); bin6 = parts[0][:6]
                            
                            m_email = P_EMAIL.search(line_ctx); c_email = m_email.group(0) if m_email else email
                            m_phone = P_PHONE.search(line_ctx); c_phone = ""
                            if m_phone: c_phone = clean_phone(m_phone.group(1))
                            if not c_phone: c_phone = phone
                            m_ip = P_IP.search(line_ctx); c_ip = m_ip.group(1) if m_ip else ip
                            c_holder = holder
                            line_parts = line_ctx.split('|')
                            if len(line_parts) >= 5 and not c_holder:
                                pot_name = line_parts[4].strip()
                                if pot_name and '@' not in pot_name and not re.match(r'^\d', pot_name): c_holder = pot_name

                            cached = self.bin_cache.get(bin6)
                            if isinstance(cached, dict): info = cached
                            else:
                                info = {"brand": "...", "type": "...", "level": "...", "bank": "...", "country": "..."}
                                if cached is None:
                                    self.bin_cache[bin6] = "FETCHING"; self.bins_total += 1; self.api_queue.put(bin6)

                            self.extracted_cards[c] = {
                                "bin": bin6, "parts": parts, "info": info,
                                "email": c_email, "phone": c_phone, "ip": c_ip, "holder": c_holder, "log_root": log_root
                            }
                            new_cards.append({
                                "cc": parts[0], "exp": f"{parts[1]}/{parts[2]}", "cvv": parts[3], "bin": bin6,
                                "brand": info["brand"], "type": info["type"], "level": info["level"], "bank": info["bank"], "country": info["country"],
                                "email": c_email, "phone": c_phone, "ip": c_ip, "holder": c_holder, "log_root": log_root
                            })
                    if new_cards: self._js(f"addCards({json.dumps(new_cards)})")

            self.scanned_history[zpath] = mtime
        except: pass
        with self.lock: self.files_scanned += 1
        self._mark_stats_dirty()

    def _api_worker(self):
        while True:
            bin6 = self.api_queue.get()
            info = self._fetch_bin(bin6)
            with self.lock:
                self.bin_cache[bin6] = info
                self.bins_checked += 1
                for data in self.extracted_cards.values():
                    if data["bin"] == bin6: data["info"] = info
            js_data = dict(info, bin=bin6)
            self._js(f"updateBin({json.dumps(js_data)})")
            self._mark_stats_dirty()
            self.api_queue.task_done()

    def _fetch_bin(self, bin6):
        # Thử API 1: Antipublic
        url = f"https://bins.antipublic.cc/bins/{bin6}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp: d = json.loads(resp.read().decode())
            flag = d.get("country_flag", ""); cname = d.get("country_name", d.get("country", "N/A"))
            return {
                "brand": str(d.get("brand", "N/A")).upper(), "type": str(d.get("type", "N/A")).upper(),
                "level": str(d.get("level", "N/A")).upper(), "bank": str(d.get("bank", "N/A")),
                "country": f"{flag} {cname}".strip()
            }
        except: pass
        
        # Thử API 2: HandyAPI (Fallback)
        try:
            r = requests.get(f"https://data.handyapi.com/bin/{bin6}", timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get("Status") == "SUCCESS":
                    return {
                        "brand": data.get("Scheme", "N/A").upper(),
                        "type": data.get("Type", "CREDIT").upper(),
                        "level": data.get("Issuer", "N/A").upper(),
                        "bank": data.get("Issuer", "N/A"),
                        "country": data.get("Country", {}).get("A2", "N/A")
                    }
        except: pass

        return {"brand": "N/A", "type": "N/A", "level": "N/A", "bank": "N/A", "country": "N/A"}
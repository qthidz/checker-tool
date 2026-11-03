import os
import re
import time
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtCore import QThread, pyqtSignal

CHUNK = 50000

def is_valid(line):
    if not line or ':' not in line:
        return False
    last = line.split(':')[-1]
    return not re.match(r'^[0-9a-fA-F]{20,}$', last)

def extract(line):
    parts = line.split(':')
    for i, p in enumerate(parts):
        p = p.strip()
        if '@' in p and '.' in p and i + 1 < len(parts):
            pwd = parts[i+1].strip()
            if pwd and len(pwd) >= 2:
                return f"{p}:{pwd}"
    cleaned = [
        p.strip() for p in parts
        if p.strip() and len(p.strip()) <= 60
        and not re.match(r'^[0-9a-fA-F]{32,}$', p.strip())
    ]
    if len(cleaned) >= 2:
        user, pwd = cleaned[-2], cleaned[-1]
        if len(user) >= 2 and not user.isdigit():
            return f"{user}:{pwd}"
    return None

def _process_chunk(lines, keywords):
    local_seen = set()
    hits = []
    for line in lines:
        line = line.strip()
        if not is_valid(line): continue
        up = extract(line)
        if not up or up in local_seen: continue
        local_seen.add(up)
        ll = line.lower()
        upl = up.lower()
        for kw in keywords:
            if kw in ll or kw in upl:
                hits.append((kw, up))
                break
    return hits

class KeywordSearchWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(dict, int, int) # results, total_lines, total_valid

    def __init__(self, filepath, keywords, threads=6):
        super().__init__()
        self.filepath = filepath
        self.keywords = keywords
        self.threads = threads

    def run(self):
        self.log_signal.emit(f"[*] Đang đọc file: {self.filepath}")
        t0 = time.time()
        try:
            with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
        except Exception as e:
            self.log_signal.emit(f"[!] Lỗi đọc file: {e}")
            return

        total_lines = len(all_lines)
        self.log_signal.emit(f"[*] Đã đọc {total_lines:,} dòng ({time.time()-t0:.2f}s). Bắt đầu lọc...")
        
        chunks = [all_lines[i:i+CHUNK] for i in range(0, total_lines, CHUNK)]
        total_chunks = len(chunks)

        results = defaultdict(list)
        seen = set()
        done = [0]
        lock = threading.Lock()

        with ThreadPoolExecutor(max_workers=self.threads) as pool:
            futures = {pool.submit(_process_chunk, chunk, self.keywords): i for i, chunk in enumerate(chunks)}
            
            from concurrent.futures import as_completed
            for future in as_completed(futures):
                hits = future.result()
                with lock:
                    for kw, up in hits:
                        if up not in seen:
                            seen.add(up)
                            results[kw].append(up)
                    done[0] += 1
                    self.progress_signal.emit(done[0], total_chunks)

        self.finished_signal.emit(results, total_lines, len(seen))

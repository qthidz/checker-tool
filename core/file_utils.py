import os
import re
import zipfile
import rarfile
from PyQt5.QtCore import QThread, pyqtSignal

# Regex nhận diện domain
DOMAIN_RE = re.compile(r"^(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:/.*)?$")

def normalize_ulp_line(line):
    """Tách domain thừa, chuẩn hóa về user:pass"""
    line = line.strip()
    if not line or line.startswith("#") or ":" not in line:
        return None
    parts = line.split(":")
    if len(parts) == 3 and DOMAIN_RE.match(parts[0]):
        return f"{parts[1]}:{parts[2]}"
    if len(parts) == 3 and DOMAIN_RE.match(parts[2]):
        return f"{parts[0]}:{parts[1]}"
    if len(parts) == 2:
        return f"{parts[0]}:{parts[1]}"
    if len(parts) > 2:
        if DOMAIN_RE.match(parts[0]):
            return f"{parts[1]}:{':'.join(parts[2:])}"
        return f"{parts[0]}:{':'.join(parts[1:])}"
    return None

class FileWorker(QThread):
    """Luồng xử lý file để không treo GUI"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, task_type, filepath, output_path, keyword=""):
        super().__init__()
        self.task_type = task_type # "domain", "keyword", "cookie"
        self.filepath = filepath
        self.output_path = output_path
        self.keyword = keyword

    def run(self):
        try:
            self.log_signal.emit(f"[*] Bắt đầu xử lý: {self.task_type}")
            lines = self._read_input(self.filepath)
            if not lines:
                self.finished_signal.emit(False, "File rỗng hoặc không đọc được.")
                return

            self.log_signal.emit(f"[*] Đã đọc {len(lines)} dòng.")
            results = []

            if self.task_type == "domain":
                for line in lines:
                    norm = normalize_ulp_line(line)
                    if norm:
                        results.append(norm)
            
            elif self.task_type == "keyword":
                kw = self.keyword.lower()
                if not kw:
                    self.finished_signal.emit(False, "Chưa nhập keyword.")
                    return
                for line in lines:
                    if kw in line.lower():
                        results.append(line)
            
            elif self.task_type == "cookie":
                # Regex tìm block cookie (đơn giản hóa)
                full_text = "\n".join(lines)
                cookie_blocks = re.findall(r'(?:[a-zA-Z0-9_]+=[^;]+;\s*)+', full_text)
                for ck in cookie_blocks:
                    if len(ck) > 20:
                        results.append(ck.strip())

            if results:
                with open(self.output_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(results))
                self.finished_signal.emit(True, f"Đã lưu {len(results)} dòng vào {self.output_path}")
            else:
                self.finished_signal.emit(False, "Không tìm thấy dữ liệu phù hợp.")

        except Exception as e:
            self.finished_signal.emit(False, f"Lỗi: {str(e)}")

    def _read_input(self, filepath):
        """Đọc txt, zip, rar"""
        lines = []
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = [l.strip() for l in f if l.strip()]
        elif ext == ".zip":
            with zipfile.ZipFile(filepath) as z:
                for n in z.namelist():
                    if n.endswith(".txt"):
                        with z.open(n) as f:
                            lines.extend([l.strip() for l in f.read().decode("utf-8","ignore").splitlines() if l.strip()])
        elif ext == ".rar":
            with rarfile.RarFile(filepath) as r:
                for n in r.namelist():
                    if n.endswith(".txt"):
                        with r.open(n) as f:
                            lines.extend([l.strip() for l in f.read().decode("utf-8","ignore").splitlines() if l.strip()])
        return lines
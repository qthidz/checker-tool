import os
import shutil
from PyQt5.QtCore import QThread, pyqtSignal

class CleanerWorker(QThread):
    log_signal = pyqtSignal(str)
    scan_done = pyqtSignal(list)
    clean_done = pyqtSignal(bool, str)

    def __init__(self, base_dir, task="scan"):
        super().__init__()
        self.base_dir = base_dir
        self.task = task

    def run(self):
        if self.task == "scan":
            self._scan()
        elif self.task == "clean":
            self._clean()

    def _scan(self):
        self.log_signal.emit("[*] Đang quét file rác...")
        trash_files = []
        # Các thư mục mục tiêu cần quét
        target_dirs = ["temp", "proxies", "cache", "outputs"]
        
        for d in target_dirs:
            dir_path = os.path.join(self.base_dir, d)
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for f in files:
                        file_path = os.path.join(root, f)
                        try:
                            size = os.path.getsize(file_path)
                            trash_files.append({"path": file_path, "size": size})
                        except: pass
                        
        # Quét __pycache__
        for root, dirs, files in os.walk(self.base_dir):
            if "__pycache__" in dirs:
                pyc_dir = os.path.join(root, "__pycache__")
                trash_files.append({"path": pyc_dir, "size": 0, "is_dir": True})

        self.log_signal.emit(f"[+] Tìm thấy {len(trash_files)} mục rác.")
        self.scan_done.emit(trash_files)

    def _clean(self):
        self.log_signal.emit("[*] Bắt đầu dọn dẹp...")
        # Thực tế cần truyền danh sách file cần xóa từ GUI vào, nhưng để đơn giản ta quét lại và xóa
        # (Trong bản hoàn thiện sẽ truyền list cụ thể)
        count = 0
        freed = 0
        target_dirs = ["temp", "proxies", "cache"]
        
        for d in target_dirs:
            dir_path = os.path.join(self.base_dir, d)
            if os.path.exists(dir_path):
                for item in os.listdir(dir_path):
                    item_path = os.path.join(dir_path, item)
                    try:
                        if os.path.isfile(item_path):
                            freed += os.path.getsize(item_path)
                            os.remove(item_path)
                            count += 1
                        elif os.path.isdir(item_path):
                            freed += sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(item_path) for f in fs)
                            shutil.rmtree(item_path)
                            count += 1
                    except: pass

        # Quét __pycache__
        for root, dirs, files in os.walk(self.base_dir):
            if "__pycache__" in dirs:
                pyc_dir = os.path.join(root, "__pycache__")
                try:
                    shutil.rmtree(pyc_dir)
                    count += 1
                except: pass

        mb_freed = round(freed / (1024 * 1024), 2)
        self.clean_done.emit(True, f"Đã xóa {count} mục, giải phóng {mb_freed} MB.")

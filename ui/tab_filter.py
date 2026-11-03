from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QTextEdit, QTabWidget)
from core.file_utils import FileWorker
from core.filter_engine import KeywordSearchWorker
import os

class TabFilter(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Lọc & Xử Lý Dữ Liệu")
        title.setProperty("class", "PageTitle")
        layout.addWidget(title)

        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #2D313A; background: #1A1D24; }
            QTabBar::tab { background: #0F1115; color: #94A3B8; padding: 8px 16px; }
            QTabBar::tab:selected { background: #1A1D24; color: #00F0FF; border-bottom: 2px solid #00F0FF; }
        """)
        
        self.tab_domain = self._create_sub_tab("Tách Domain", "Nhập file ULP có domain...", "domain")
        self.tab_keyword = self._create_keyword_tab() # Tab Keyword mới dùng Engine
        self.tab_dumper = self._create_sub_tab("Dumper Cookie", "Nhập file log chứa cookie...", "cookie")

        self.sub_tabs.addTab(self.tab_domain, "Tách Domain")
        self.sub_tabs.addTab(self.tab_keyword, "Lọc Keyword (High-Speed)")
        self.sub_tabs.addTab(self.tab_dumper, "Dumper Cookie")
        
        layout.addWidget(self.sub_tabs)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)

    def _create_sub_tab(self, title, placeholder, task_type):
        # Giữ nguyên code cũ của bạn
        pass 

    def _create_keyword_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # File Input
        file_layout = QHBoxLayout()
        self.kw_entry_file = QLineEdit()
        self.kw_entry_file.setPlaceholderText("Chọn file log lớn (.txt)...")
        btn_file = QPushButton("Chọn File")
        btn_file.setProperty("class", "BtnNeon")
        btn_file.clicked.connect(lambda: self._select_file(self.kw_entry_file))
        file_layout.addWidget(self.kw_entry_file)
        file_layout.addWidget(btn_file)
        layout.addLayout(file_layout)

        # Keyword Input
        kw_layout = QHBoxLayout()
        self.kw_entry_text = QLineEdit()
        self.kw_entry_text.setPlaceholderText("Nhập danh sách keyword (cách nhau bằng dấu phẩy, VD: gmail, admin, 2024)...")
        kw_layout.addWidget(QLabel("Keywords:"))
        kw_layout.addWidget(self.kw_entry_text)
        layout.addLayout(kw_layout)

        # Settings
        thread_layout = QHBoxLayout()
        self.kw_entry_threads = QLineEdit("6")
        self.kw_entry_threads.setFixedWidth(50)
        thread_layout.addWidget(QLabel("Số luồng:"))
        thread_layout.addWidget(self.kw_entry_threads)
        thread_layout.addStretch()
        layout.addLayout(thread_layout)

        btn_run = QPushButton("BẮT ĐẦU LỌC")
        btn_run.setProperty("class", "BtnNeon")
        btn_run.setFixedHeight(40)
        btn_run.clicked.connect(self._start_keyword_search)
        layout.addWidget(btn_run)
        
        layout.addStretch()
        return widget

    def _start_keyword_search(self):
        filepath = self.kw_entry_file.text()
        kw_raw = self.kw_entry_text.text()
        
        if not filepath or not os.path.exists(filepath):
            self.log_box.append("[!] File không hợp lệ.")
            return
        if not kw_raw:
            self.log_box.append("[!] Chưa nhập keyword.")
            return

        keywords = set([k.strip().lower() for k in kw_raw.split(",") if k.strip()])
        
        try: threads = int(self.kw_entry_threads.text())
        except: threads = 6

        self.log_box.append(f"[*] Bắt đầu lọc với {len(keywords)} keywords, {threads} luồng...")
        
        self.kw_worker = KeywordSearchWorker(filepath, keywords, threads)
        self.kw_worker.log_signal.connect(self.log_box.append)
        self.kw_worker.progress_signal.connect(self._update_kw_progress)
        self.kw_worker.finished_signal.connect(self._on_kw_finished)
        self.kw_worker.start()

    def _update_kw_progress(self, done, total):
        # Có thể cập nhật ProgressBar nếu cần, tạm thời in ra log mỗi 10%
        if done % max(1, total // 10) == 0:
            self.log_box.append(f"[*] Tiến độ: {done}/{total} chunks...")

    def _on_kw_finished(self, results, total_lines, total_valid):
        self.log_box.append(f"[+] Hoàn tất! Đã quét {total_lines:,} dòng, tìm thấy {total_valid:,} kết quả hợp lệ.")
        
        # Lưu file output
        output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        for kw, lines in results.items():
            out_path = os.path.join(output_dir, f"COMBO-{kw.upper()}.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            self.log_box.append(f"[+] Đã lưu {len(lines):,} kết quả cho từ khóa '{kw}' -> {out_path}")
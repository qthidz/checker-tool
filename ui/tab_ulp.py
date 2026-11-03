# -------------------------------------------------------------------
# FILE: ui/tab_ulp.py (Cập nhật giao diện Tab Mail cho phép nhập Proxy)
# -------------------------------------------------------------------
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QTextEdit, QTabWidget)
from PyQt5.QtCore import QThread, pyqtSignal
from core.ulp_checker import mine_proxies, check_web_auto, check_mail_imap
import os

class ProxyMinerWorker(QThread):
    log_signal = pyqtSignal(str)
    done_signal = pyqtSignal(list)
    def __init__(self, domain, need):
        super().__init__()
        self.domain = domain
        self.need = need
    def run(self):
        self.log_signal.emit(f"[*] Đang đào proxy cho {self.domain} (cần {self.need})...")
        proxies = mine_proxies(self.domain, self.need)
        self.log_signal.emit(f"[+] Đã tìm thấy {len(proxies)} proxy sống.")
        self.done_signal.emit(proxies)

class ULPCheckWorker(QThread):
    log_signal = pyqtSignal(str)
    def __init__(self, mode, filepath, domain, proxies):
        super().__init__()
        self.mode = mode
        self.filepath = filepath
        self.domain = domain
        self.proxies = proxies
    def run(self):
        try:
            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = [l.strip() for l in f if l.strip()]
            self.log_signal.emit(f"[*] Tổng số: {len(lines)} tài khoản.")
            live_count = 0
            for i, line in enumerate(lines):
                if ":" not in line: continue
                user, pwd = line.split(":", 1)
                proxy = self.proxies[i % len(self.proxies)] if self.proxies else None
                
                if self.mode == "web":
                    is_live, msg = check_web_auto(self.domain, user, pwd, proxy)
                    if not is_live and ("Proxy" in msg or "Timeout" in msg):
                        is_live, msg = check_web_auto(self.domain, user, pwd, None)
                else:
                    is_live, msg = check_mail_imap(user, pwd, proxy)
                    
                if is_live:
                    self.log_signal.emit(f"[LIVE] {user}:{pwd} | {msg}")
                    live_count += 1
                else:
                    self.log_signal.emit(f"[DEAD] {user}:{pwd} | {msg}")
            self.log_signal.emit(f"=== HOÀN TẤT: {live_count} LIVE ===")
        except Exception as e:
            self.log_signal.emit(f"[!] Lỗi: {str(e)}")

class TabULP(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("ULP Checker (User / Pass)")
        title.setProperty("class", "PageTitle")
        layout.addWidget(title)
        
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #2D313A; background: #1A1D24; }
            QTabBar::tab { background: #0F1115; color: #94A3B8; padding: 8px 16px; }
            QTabBar::tab:selected { background: #1A1D24; color: #00F0FF; border-bottom: 2px solid #00F0FF; }
        """)
        
        self.tab_web = self._create_web_tab()
        self.tab_mail = self._create_mail_tab()

        self.sub_tabs.addTab(self.tab_web, "Web Login (Form/API)")
        self.sub_tabs.addTab(self.tab_mail, "Mail Access (IMAP/SOCKS5)")
        
        layout.addWidget(self.sub_tabs)

    def _create_web_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        file_layout = QHBoxLayout()
        self.web_entry_file = QLineEdit()
        self.web_entry_file.setPlaceholderText("Chọn file ULP (.txt)...")
        btn_file = QPushButton("Chọn File")
        btn_file.setProperty("class", "BtnNeon")
        btn_file.clicked.connect(lambda: self._select_file(self.web_entry_file))
        file_layout.addWidget(self.web_entry_file)
        file_layout.addWidget(btn_file)
        layout.addLayout(file_layout)

        dom_layout = QHBoxLayout()
        self.web_entry_domain = QLineEdit()
        self.web_entry_domain.setPlaceholderText("Nhập domain mục tiêu...")
        dom_layout.addWidget(QLabel("Domain:"))
        dom_layout.addWidget(self.web_entry_domain)
        layout.addLayout(dom_layout)

        proxy_layout = QHBoxLayout()
        self.web_btn_mine = QPushButton("ĐÀO PROXY CHO DOMAIN NÀY")
        self.web_btn_mine.setProperty("class", "BtnNeon")
        self.web_btn_mine.clicked.connect(self._mine_proxies)
        proxy_layout.addWidget(self.web_btn_mine)
        self.web_lbl_proxy_status = QLabel("Chưa có proxy")
        proxy_layout.addWidget(self.web_lbl_proxy_status)
        proxy_layout.addStretch()
        layout.addLayout(proxy_layout)

        btn_run = QPushButton("BẮT ĐẦU CHECK WEB")
        btn_run.setProperty("class", "BtnNeon")
        btn_run.setFixedHeight(40)
        btn_run.clicked.connect(self._start_web)
        layout.addWidget(btn_run)

        self.web_log_box = QTextEdit()
        self.web_log_box.setReadOnly(True)
        layout.addWidget(self.web_log_box)
        
        return widget

    def _create_mail_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        file_layout = QHBoxLayout()
        self.mail_entry_file = QLineEdit()
        self.mail_entry_file.setPlaceholderText("Chọn file ULP (.txt) chứa email...")
        btn_file = QPushButton("Chọn File")
        btn_file.setProperty("class", "BtnNeon")
        btn_file.clicked.connect(lambda: self._select_file(self.mail_entry_file))
        file_layout.addWidget(self.mail_entry_file)
        file_layout.addWidget(btn_file)
        layout.addLayout(file_layout)

        # THÊM Ô NHẬP PROXY SOCKS5 CHO MAIL
        proxy_layout = QHBoxLayout()
        self.mail_entry_proxy = QLineEdit()
        self.mail_entry_proxy.setPlaceholderText("Nhập SOCKS5 Proxy (VD: socks5://1.2.3.4:1080) - Để trống nếu không dùng...")
        proxy_layout.addWidget(QLabel("Proxy:"))
        proxy_layout.addWidget(self.mail_entry_proxy)
        layout.addLayout(proxy_layout)

        btn_run = QPushButton("BẮT ĐẦU CHECK MAIL")
        btn_run.setProperty("class", "BtnNeon")
        btn_run.setFixedHeight(40)
        btn_run.clicked.connect(self._start_mail)
        layout.addWidget(btn_run)

        self.mail_log_box = QTextEdit()
        self.mail_log_box.setReadOnly(True)
        layout.addWidget(self.mail_log_box)
        
        return widget

    def _select_file(self, entry_widget):
        p, _ = QFileDialog.getOpenFileName(self, "Chọn File", "", "Text (*.txt)")
        if p: entry_widget.setText(p)

    def _mine_proxies(self):
        domain = self.web_entry_domain.text().strip()
        if not domain:
            self.web_log_box.append("[!] Vui lòng nhập domain.")
            return
        filepath = self.web_entry_file.text()
        need = 50
        if filepath and os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                need = len([l for l in f if l.strip()])
        
        self.web_btn_mine.setEnabled(False)
        self.web_lbl_proxy_status.setText("Đang đào...")
        self.miner = ProxyMinerWorker(domain, need)
        self.miner.log_signal.connect(self.web_log_box.append)
        self.miner.done_signal.connect(self._on_proxies_mined)
        self.miner.start()

    def _on_proxies_mined(self, proxies):
        self.web_proxies = proxies
        self.web_btn_mine.setEnabled(True)
        self.web_lbl_proxy_status.setText(f"Đã có {len(proxies)} proxy sống")

    def _start_web(self):
        filepath = self.web_entry_file.text()
        domain = self.web_entry_domain.text().strip()
        if not filepath or not os.path.exists(filepath) or not domain:
            self.web_log_box.append("[!] Vui lòng kiểm tra lại File và Domain.")
            return
        self.web_log_box.clear()
        self.web_log_box.append(f"[*] Bắt đầu check Web: {domain}")
        
        proxies = getattr(self, "web_proxies", [])
        self.web_worker = ULPCheckWorker("web", filepath, domain, proxies)
        self.web_worker.log_signal.connect(self.web_log_box.append)
        self.web_worker.start()

    def _start_mail(self):
        filepath = self.mail_entry_file.text()
        proxy = self.mail_entry_proxy.text().strip()
        
        if not filepath or not os.path.exists(filepath):
            self.mail_log_box.append("[!] Vui lòng chọn file.")
            return
            
        self.mail_log_box.clear()
        self.mail_log_box.append(f"[*] Bắt đầu check Mail...")
        if proxy: self.mail_log_box.append(f"[*] Sử dụng SOCKS5 Proxy: {proxy}")
        
        # Nếu có proxy, gán vào list để worker xoay vòng (dù chỉ có 1 con)
        proxies = [proxy] if proxy else []
        self.mail_worker = ULPCheckWorker("mail", filepath, "", proxies)
        self.mail_worker.log_signal.connect(self.mail_log_box.append)
        self.mail_worker.start()
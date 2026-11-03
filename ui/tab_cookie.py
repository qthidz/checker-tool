# ui/tab_cookie.py - Nâng cấp: Chọn nhiều nền tảng + Nút gạt mượt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QFileDialog, QTextEdit, 
                             QGridLayout, QScrollArea, QMessageBox, QFrame, QCheckBox)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QRect
from PyQt5.QtGui import QIcon, QFont, QPixmap
import os
import zipfile
import rarfile
from core.cookie_checker import PLATFORMS, CookieCheckWorker
from core.ulp_checker import mine_proxies, ProxyMinerWorker


# --- Tùy chỉnh Nút gạt (Switch) bằng Animation ---
class AnimatedSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 20)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("QCheckBox { background: transparent; } QCheckBox::indicator { width: 0px; height: 0px; }")
        
        # Thanh nền
        self.bg = QLabel(self)
        self.bg.setGeometry(0, 0, 40, 20)
        self.bg.setStyleSheet("background-color: #2D313A; border-radius: 10px;")
        
        # Cục tròn
        self.knob = QLabel(self)
        self.knob.setGeometry(2, 2, 16, 16)
        self.knob.setStyleSheet("background-color: #888888; border-radius: 8px;")
        
        self.stateChanged.connect(self.animate)

    def animate(self, state):
        if state == Qt.Checked:
            self.bg.setStyleSheet("background-color: #00F0FF; border-radius: 10px;")
            self.knob.setStyleSheet("background-color: #FFFFFF; border-radius: 8px;")
            self.anim = QPropertyAnimation(self.knob, b"geometry")
            self.anim.setDuration(150)
            self.anim.setEndValue(QRect(22, 2, 16, 16))
            self.anim.start()
        else:
            self.bg.setStyleSheet("background-color: #2D313A; border-radius: 10px;")
            self.knob.setStyleSheet("background-color: #888888; border-radius: 8px;")
            self.anim = QPropertyAnimation(self.knob, b"geometry")
            self.anim.setDuration(150)
            self.anim.setEndValue(QRect(2, 2, 16, 16))
            self.anim.start()

class CookieCard(QFrame):
    def __init__(self, platform_key, info, parent_tab):
        super().__init__()
        self.platform_key = platform_key
        self.info = info
        self.parent_tab = parent_tab
        
        self.setFixedSize(220, 200)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        top_layout = QHBoxLayout()
        self.icon_label = QLabel()
        icon_path = os.path.join(os.getcwd(), "assets", "icons", f"{platform_key}.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
        else:
            self.icon_label.setText("?")
            self.icon_label.setStyleSheet("font-size: 30px; color: gray;")
            
        top_layout.addWidget(self.icon_label)
        top_layout.addStretch()
        
        btn_link = QLabel("↗")
        btn_link.setStyleSheet("color: #555; font-size: 18px;")
        top_layout.addWidget(btn_link)
        layout.addLayout(top_layout)

        title = QLabel(info["name"])
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        desc = QLabel(info.get("desc", "No description"))
        desc.setStyleSheet("color: #888888; font-size: 11px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addStretch()

        bottom_layout = QHBoxLayout()
        self.btn_settings = QPushButton("⚙ Settings")
        self.btn_settings.setStyleSheet("""
            QPushButton { background-color: #2D313A; color: #E2E8F0; border-radius: 5px; padding: 4px 8px; font-size: 11px; }
            QPushButton:hover { background-color: #3A404C; }
        """)
        bottom_layout.addWidget(self.btn_settings)
        
        # Sử dụng AnimatedSwitch thay cho QCheckBox thường
        self.switch = AnimatedSwitch()
        bottom_layout.addWidget(self.switch)
        
        layout.addLayout(bottom_layout)

        # Bấm vào đâu cũng kích hoạt
        self.mousePressEvent = self.on_card_clicked
        self.btn_settings.clicked.connect(self.on_card_clicked)

        self.update_style(False)

    def on_card_clicked(self, event=None):
        # Đảo ngược trạng thái
        new_state = not self.switch.isChecked()
        self.parent_tab.toggle_platform(self.platform_key, new_state)

    def set_selected(self, is_selected):
        self.switch.setChecked(is_selected)
        self.update_style(is_selected)

    def update_style(self, is_selected):
        color = self.info["color"]
        if is_selected:
            self.setStyleSheet(f"""
                QFrame {{ background-color: #1A1D24; border: 2px solid {color}; border-radius: 12px; }}
            """)
        else:
            self.setStyleSheet("""
                QFrame { background-color: #111827; border: 2px solid #1E293B; border-radius: 12px; }
                QFrame:hover { border: 2px solid #334155; background-color: #1A1D24; }
            """)

class TabCookie(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_platforms = set() # Dùng Set để lưu nhiều nền tảng
        self.proxies = {}
        self.file_data = {} # Lưu trữ dữ liệu cookie theo nền tảng
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Cookie Checker (Đa nền tảng)")
        title.setProperty("class", "PageTitle")
        main_layout.addWidget(title)

        top_layout = QHBoxLayout()
        self.entry_file = QLineEdit()
        self.entry_file.setPlaceholderText("Chọn file cookie (.txt, .zip, .rar)...")
        btn_file = QPushButton("Chọn File")
        btn_file.setProperty("class", "BtnNeon")
        btn_file.clicked.connect(self.select_file)
        
        btn_mine = QPushButton("ĐÀO PROXY")
        btn_mine.setProperty("class", "BtnNeon")
        btn_mine.clicked.connect(self.mine_proxy)
        
        top_layout.addWidget(self.entry_file)
        top_layout.addWidget(btn_file)
        top_layout.addWidget(btn_mine)
        main_layout.addLayout(top_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll.setWidget(scroll_content)
        
        self.cards = {}
        row, col = 0, 0
        
        PLATFORMS["github"]["desc"] = "Repos, gists, profile"
        PLATFORMS["twitter"]["desc"] = "Tweets, followers, analytics"
        PLATFORMS["facebook"]["desc"] = "Friends, groups, pages"
        
        for key, info in PLATFORMS.items():
            card = CookieCard(key, info, self)
            self.grid_layout.addWidget(card, row, col)
            self.cards[key] = card
            
            col += 1
            if col > 2:
                col = 0
                row += 1
                
        main_layout.addWidget(scroll)

        bottom_layout = QHBoxLayout()
        self.lbl_status = QLabel("Chưa chọn nền tảng")
        self.lbl_status.setStyleSheet("color: #94A3B8; font-weight: bold;")
        
        self.btn_start = QPushButton("BẮT ĐẦU CHECK")
        self.btn_start.setProperty("class", "BtnNeon")
        self.btn_start.setFixedSize(150, 40)
        self.btn_start.clicked.connect(self.start_check)
        
        bottom_layout.addWidget(self.lbl_status)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_start)
        main_layout.addLayout(bottom_layout)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(120)
        main_layout.addWidget(self.log_box)

    def select_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "Chọn File Cookie", "", "All Files (*.txt *.zip *.rar)")
        if p:
            self.entry_file.setText(p)
            self.file_data = self._read_input(p)
            self.log_box.append(f"[*] Đã nạp dữ liệu từ file.")
            
    def _read_input(self, filepath):
        lines = []
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines.append(f.read())
        elif ext == ".zip":
            with zipfile.ZipFile(filepath) as z:
                for n in z.namelist():
                    if n.endswith(".txt"):
                        with z.open(n) as f:
                            lines.append(f.read().decode("utf-8","ignore"))
        elif ext == ".rar":
            with rarfile.RarFile(filepath) as r:
                for n in r.namelist():
                    if n.endswith(".txt"):
                        with r.open(n) as f:
                            lines.append(f.read().decode("utf-8","ignore"))
        return lines

    def toggle_platform(self, key, is_checked):
        if is_checked:
            self.selected_platforms.add(key)
        else:
            self.selected_platforms.discard(key)
            
        self.cards[key].set_selected(is_checked)
        
        # Cập nhật Status
        if self.selected_platforms:
            names = [PLATFORMS[k]["name"] for k in self.selected_platforms]
            self.lbl_status.setText(f"Đã chọn: {', '.join(names)}")
        else:
            self.lbl_status.setText("Chưa chọn nền tảng")

    def mine_proxy(self):
        if not self.selected_platforms:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ít nhất 1 nền tảng trước.")
            return
            
        self.log_box.append(f"[*] Đang đào proxy cho các nền tảng đã chọn...")
        
        # Tạo list để lưu các luồng
        self.miners = []
        
        for key in self.selected_platforms:
            endpoint = PLATFORMS[key]["endpoint"]
            need = len(self.file_data) if self.file_data else 50
            
            # Gọi ProxyMinerWorker (đã được import từ core.ulp_checker)
            miner = ProxyMinerWorker(endpoint, need)
            miner.log_signal.connect(self.log_box.append)
            miner.done_signal.connect(lambda p, k=key: self._on_proxy_mined(k, p))
            
            self.miners.append(miner)
            miner.start() # Chạy ngầm, không gây đơ giao diện

    def _on_proxy_mined(self, key, proxies):
        """Hàm nhận kết quả khi Thread đào proxy xong"""
        self.proxies[key] = proxies
        self.log_box.append(f"[+] {PLATFORMS[key]['name']}: Đã đào {len(proxies)} proxy sống.")

    def start_check(self):
        if not self.selected_platforms or not self.file_data:
            QMessageBox.warning(self, "Lỗi", "Chưa chọn nền tảng hoặc chưa nạp file cookie.")
            return
        
        self.log_box.clear()
        self.btn_start.setEnabled(False)
        
        # Chạy song song từng nền tảng
        self.workers = []
        for key in self.selected_platforms:
            worker = CookieCheckWorker(key, self.file_data, self.proxies.get(key, []))
            worker.log_signal.connect(self.log_box.append)
            # Nếu cần gom kết quả thì viết thêm hàm on_platform_finished
            worker.finished_signal.connect(lambda live, total, k=key: self.log_box.append(f"[{PLATFORMS[k]['name']}] HOÀN TẤT: {live}/{total} LIVE"))
            self.workers.append(worker)
            worker.start()

    def on_finished(self, live, total):
        # Xử lý khi tất cả các luồng chạy xong (nếu cần)
        pass
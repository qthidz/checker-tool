# ui/main_window.py - Bản chuẩn (Đã kiểm tra kỹ import)
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QStackedWidget)
from PyQt5.QtCore import Qt

# --- KIỂM TRA KỸ CÁC DÒNG IMPORT NÀY ---
from ui.tab_cookie import TabCookie
from ui.tab_ulp import TabULP
from ui.tab_filter import TabFilter
from ui.tab_cc_extractor import TabCCExtractor
from ui.tab_settings import TabSettings  # BẮT BUỘC PHẢI CÓ DÒNG NÀY
# ----------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NSMOD Multi-Checker")
        self.setGeometry(100, 100, 1100, 750)
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Topbar
        self.topbar = QFrame()
        self.topbar.setObjectName("TopBar")
        self.topbar.setFixedHeight(40)
        topbar_layout = QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(10, 0, 10, 0)
        
        logo = QLabel("NSMOD MULTI-TOOL")
        logo.setObjectName("LogoText")
        topbar_layout.addWidget(logo)
        topbar_layout.addStretch()

        btn_min = QPushButton("—")
        btn_min.setObjectName("BtnMin")
        btn_min.setFixedSize(30, 30)
        btn_min.clicked.connect(self.showMinimized)
        topbar_layout.addWidget(btn_min)

        btn_close = QPushButton("✕")
        btn_close.setObjectName("BtnClose")
        btn_close.setFixedSize(30, 30)
        btn_close.clicked.connect(self.close)
        topbar_layout.addWidget(btn_close)

        main_layout.addWidget(self.topbar)

        # 2. Body (Sidebar + Content)
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("SideBar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 10, 0, 10)
        sidebar_layout.setSpacing(5)

        # Các nút trên Sidebar
        self.btn_tab1 = QPushButton("Cookie Checker")
        self.btn_tab2 = QPushButton("ULP Checker")
        self.btn_tab3 = QPushButton("Lọc Data")
        self.btn_tab5 = QPushButton("CC Extractor")
        self.btn_tab6 = QPushButton("Cài Đặt")

        self.side_buttons = [self.btn_tab1, self.btn_tab2, self.btn_tab3, 
                             self.btn_tab5, self.btn_tab6]
        
        for i, btn in enumerate(self.side_buttons):
            btn.setProperty("class", "SideBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, index=i: self.switch_tab(index))
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        self.btn_tab1.setChecked(True)

        body_layout.addWidget(sidebar)

        # Content (Stacked Widget)
        self.content_stack = QStackedWidget()
        
        # Khởi tạo các trang
        self.page1_cookie = TabCookie()
        self.page2_ulp = TabULP()
        self.page3_filter = TabFilter()
        self.page5_cc = TabCCExtractor()
        self.page6_settings = TabSettings() # Lỗi ở đây là do thiếu Import ở trên

        self.content_stack.addWidget(self.page1_cookie)
        self.content_stack.addWidget(self.page2_ulp)
        self.content_stack.addWidget(self.page3_filter)
        self.content_stack.addWidget(self.page5_cc)
        self.content_stack.addWidget(self.page6_settings)

        body_layout.addWidget(self.content_stack)
        main_layout.addLayout(body_layout)

    def switch_tab(self, index):
        for i, btn in enumerate(self.side_buttons):
            btn.setChecked(i == index)
        self.content_stack.setCurrentIndex(index)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()
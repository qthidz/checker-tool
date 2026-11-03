# ui/tab_settings.py - Tạo file này trong thư mục ui/
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QMessageBox, 
                             QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from core.platform_manager import load_platforms, add_platform, delete_platform
import os

class TabSettings(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Cài Đặt Nền Tảng (Add Tool/Config)")
        title.setProperty("class", "PageTitle")
        layout.addWidget(title)

        # Form nhập liệu
        form_layout = QVBoxLayout()
        
        # Tên nền tảng
        name_layout = QHBoxLayout()
        self.entry_name = QLineEdit()
        self.entry_name.setPlaceholderText("Nhập tên nền tảng (VD: Shopee)...")
        name_layout.addWidget(QLabel("Tên:"))
        name_layout.addWidget(self.entry_name)
        form_layout.addLayout(name_layout)

        # Đường dẫn file source
        script_layout = QHBoxLayout()
        self.entry_script = QLineEdit()
        self.entry_script.setPlaceholderText("Đường dẫn file source code (.py, .js, .c)...")
        btn_script = QPushButton("Chọn File")
        btn_script.setProperty("class", "BtnNeon")
        btn_script.clicked.connect(lambda: self._select_file(self.entry_script, "Source (*.py *.js *.c);;All (*.*)"))
        script_layout.addWidget(QLabel("Tool/Config:"))
        script_layout.addWidget(self.entry_script)
        script_layout.addWidget(btn_script)
        form_layout.addLayout(script_layout)

        # Đường dẫn Icon
        icon_layout = QHBoxLayout()
        self.entry_icon = QLineEdit()
        self.entry_icon.setPlaceholderText("Đường dẫn file ảnh (.png, .ico)...")
        btn_icon = QPushButton("Chọn Ảnh")
        btn_icon.setProperty("class", "BtnNeon")
        btn_icon.clicked.connect(lambda: self._select_file(self.entry_icon, "Images (*.png *.jpg *.ico);;All (*.*)"))
        icon_layout.addWidget(QLabel("Icon:"))
        icon_layout.addWidget(self.entry_icon)
        icon_layout.addWidget(btn_icon)
        form_layout.addLayout(icon_layout)

        layout.addLayout(form_layout)

        # Nút hành động
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("THÊM NỀN TẢNG")
        btn_add.setProperty("class", "BtnNeon")
        btn_add.clicked.connect(self._add_platform)
        
        btn_del = QPushButton("XÓA NỀN TẢNG ĐÃ CHỌN")
        btn_del.setProperty("class", "BtnNeon")
        btn_del.setStyleSheet("QPushButton.BtnNeon { color: #E74C3C; border-color: #E74C3C; } QPushButton.BtnNeon:hover { background-color: #E74C3C; color: white; }")
        btn_del.clicked.connect(self._delete_platform)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        layout.addLayout(btn_layout)

        # Danh sách hiển thị
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background-color: #1A1D24; color: #E2E8F0; border: 1px solid #2D313A; font-size: 14px; padding: 5px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #2D313A; }
            QListWidget::item:selected { background-color: #252A34; color: #00F0FF; }
        """)
        layout.addWidget(self.list_widget)

        self.refresh_list()

    def _select_file(self, entry, filter_str):
        p, _ = QFileDialog.getOpenFileName(self, "Chọn File", "", filter_str)
        if p: entry.setText(p)

    def _add_platform(self):
        name = self.entry_name.text().strip()
        script = self.entry_script.text().strip()
        icon = self.entry_icon.text().strip()

        if not name or not script:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Tên và chọn File Tool/Config.")
            return

        success, msg = add_platform(name, icon, script)
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.entry_name.clear()
            self.entry_script.clear()
            self.entry_icon.clear()
            self.refresh_list()
        else:
            QMessageBox.warning(self, "Lỗi", msg)

    def _delete_platform(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        pid = item.data(Qt.UserRole)
        delete_platform(pid)
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        platforms = load_platforms()
        for p in platforms:
            icon_path = p.get("icon", "")
            display_text = f"{p['name']}  |  {os.path.basename(p['script'])}"
            
            item = QListWidgetItem(display_text)
            if icon_path and os.path.exists(icon_path):
                item.setIcon(QIcon(icon_path))
                
            item.setData(Qt.UserRole, p["id"])
            self.list_widget.addItem(item)
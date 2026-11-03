import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

if __name__ == "__main__":
    # Khởi tạo ứng dụng
    app = QApplication(sys.argv)
    
    # Thiết lập style toàn cục (sẽ được load từ styles.py)
    try:
        with open(os.path.join("ui", "styles.qss"), "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Không thể load styles.qss: {e}")

    # Mở cửa sổ chính
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



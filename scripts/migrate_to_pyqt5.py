# scripts/migrate_to_pyqt5.py - Script tự động chuyển đổi code từ PyQt6 sang PyQt5
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_DIR = os.path.join(BASE_DIR, "ui")
CORE_DIR = os.path.join(BASE_DIR, "core")
MAIN_FILE = os.path.join(BASE_DIR, "main.py")

def migrate_file(filepath):
    if not os.path.exists(filepath):
        return False
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Thay thế import
    content = content.replace("from PyQt6", "from PyQt5")
    content = content.replace("import PyQt6", "import PyQt5")

    # 2. Thay thế các thuộc tính Enum bị thay đổi trong PyQt5
    content = content.replace("Qt.WindowType.FramelessWindowHint", "Qt.FramelessWindowHint")
    content = content.replace("Qt.WidgetAttribute.WA_TranslucentBackground", "Qt.WA_TranslucentBackground")
    content = content.replace("Qt.MouseButton.LeftButton", "Qt.LeftButton")
    content = content.replace("Qt.AlignmentFlag.AlignCenter", "Qt.AlignCenter")
    content = content.replace("Qt.TextInteractionFlag.TextSelectableByMouse", "Qt.TextSelectableByMouse")
    
    # Thay thế QWebEngineWidgets (nếu có)
    content = content.replace("from PyQt5.QtWebEngineWidgets", "from PyQt5.QtWebEngineWidgets")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return True

def main():
    print("[*] Bắt đầu quá trình chuyển đổi sang PyQt5...")
    
    # Chuyển đổi file main.py
    if migrate_file(MAIN_FILE):
        print(f"[+] Đã sửa: main.py")

    # Chuyển đổi toàn bộ file trong thư mục ui/
    if os.path.exists(UI_DIR):
        for filename in os.listdir(UI_DIR):
            if filename.endswith(".py"):
                filepath = os.path.join(UI_DIR, filename)
                if migrate_file(filepath):
                    print(f"[+] Đã sửa: ui/{filename}")

    # Chuyển đổi toàn bộ file trong thư mục core/ (nếu có dùng PyQt6)
    if os.path.exists(CORE_DIR):
        for filename in os.listdir(CORE_DIR):
            if filename.endswith(".py"):
                filepath = os.path.join(CORE_DIR, filename)
                if migrate_file(filepath):
                    print(f"[+] Đã sửa: core/{filename}")

    print("[+] Hoàn tất chuyển đổi! Bạn có thể chạy 'python main.py' để kiểm tra.")

if __name__ == "__main__":
    main()
# scripts/clean_project.py - Script dọn dẹp dự án theo yêu cầu
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_WINDOW_FILE = os.path.join(BASE_DIR, "ui", "main_window.py")
CLEANER_FILE = os.path.join(BASE_DIR, "ui", "tab_cleaner.py")
AUTH_CHECKER_FILE = os.path.join(BASE_DIR, "core", "auth_checker.py")

def update_main_window():
    if not os.path.exists(MAIN_WINDOW_FILE): return
    with open(MAIN_WINDOW_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Xóa import Cleaner
    content = re.sub(r'from ui\.tab_cleaner import TabCleaner\n', '', content)
    
    # Xóa nút Sidebar
    content = re.sub(r'\s*self\.btn_tab4 = QPushButton\("Dọn Dẹp"\)\n', '\n', content)

    # Sửa lại mảng side_buttons
    content = re.sub(
        r'self\.side_buttons = \[(.*?)\]', 
        lambda m: "self.side_buttons = [" + m.group(1).replace("self.btn_tab4, ", "").replace(", self.btn_tab4", "") + "]", 
        content, flags=re.DOTALL
    )

    # Xóa khởi tạo page4
    content = re.sub(r'\s*self\.page4_cleaner = TabCleaner\(\)\n', '\n', content)
    content = re.sub(r'\s*self\.content_stack\.addWidget\(self\.page4_cleaner\)\n', '\n', content)

    # Đảm bảo Import TabCCExtractor vẫn còn (vì ta giữ lại)
    if "from ui.tab_cc_extractor import TabCCExtractor" not in content:
        content = content.replace("from ui.main_window import", "from ui.tab_cc_extractor import TabCCExtractor\nfrom ui.main_window import")

    with open(MAIN_WINDOW_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print("[+] Đã cập nhật ui/main_window.py (Xóa Dọn Dẹp)")

def delete_files():
    if os.path.exists(CLEANER_FILE):
        os.remove(CLEANER_FILE)
        print("[+] Đã xóa ui/tab_cleaner.py")
    if os.path.exists(AUTH_CHECKER_FILE):
        os.remove(AUTH_CHECKER_FILE)
        print("[+] Đã xóa core/auth_checker.py")

if __name__ == "__main__":
    print("[*] Bắt đầu dọn dẹp...")
    update_main_window()
    delete_files()
    print("[+] HOÀN TẤT! Hãy chạy 'python main.py'.")
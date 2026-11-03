# core/platform_manager.py - Quản lý cấu hình nền tảng (lưu trữ JSON)
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "platforms.json")

os.makedirs(DATA_DIR, exist_ok=True)

def load_platforms():
    """Tải danh sách nền tảng từ file JSON"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_platforms(platforms):
    """Lưu danh sách nền tảng vào file JSON"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(platforms, f, indent=4, ensure_ascii=False)

def add_platform(name, icon_path, script_path, color="#00F0FF"):
    """Thêm nền tảng mới vào file JSON"""
    platforms = load_platforms()
    new_id = name.lower().replace(" ", "_")
    
    # Kiểm tra trùng lặp
    for p in platforms:
        if p["id"] == new_id:
            return False, "Nền tảng đã tồn tại."
            
    platforms.append({
        "id": new_id,
        "name": name,
        "icon": icon_path,
        "script": script_path,
        "color": color
    })
    save_platforms(platforms)
    return True, "Thêm thành công."

def delete_platform(platform_id):
    """Xóa nền tảng khỏi file JSON"""
    platforms = load_platforms()
    platforms = [p for p in platforms if p["id"] != platform_id]
    save_platforms(platforms)
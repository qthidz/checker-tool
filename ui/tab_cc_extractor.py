# ui/tab_cc_extractor.py - Bản Full (Chỉ giữ CC Extractor)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QFileDialog, QMessageBox, QHeaderView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
import zipfile
import re
import csv

from core.cc_engine import extract_cards_zccv, P_CC, P_EMAIL, P_PHONE, P_IP, is_valid, fmt, clean_phone

class CCScanWorker(QThread):
    log_signal = pyqtSignal(str)
    row_signal = pyqtSignal(list)
    finished_signal = pyqtSignal(int)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.is_running = True

    def run(self):
        self.log_signal.emit(f"[*] Bắt đầu quét thư mục: {self.folder_path}")
        all_files = []
        for root, _, files in os.walk(self.folder_path):
            for fn in files:
                all_files.append(os.path.join(root, fn))

        total_cards = 0
        for fpath in all_files:
            if not self.is_running: break
            try:
                if fpath.lower().endswith('.zip'):
                    cards = self._process_zip(fpath)
                else:
                    cards = self._process_file(fpath)
                
                if cards:
                    self.row_signal.emit(cards)
                    total_cards += len(cards)
            except Exception as e:
                self.log_signal.emit(f"[!] Lỗi file {os.path.basename(fpath)}: {str(e)[:30]}")

        self.finished_signal.emit(total_cards)

    def _process_file(self, fpath):
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except: return []

        zccv_cards = extract_cards_zccv(content)
        for cc, m, y, cvv in P_CC.findall(content):
            if is_valid(cc, m, y, cvv):
                zccv_cards.append(fmt(cc, m, y, cvv))

        found = {}
        for c_fmt in set(zccv_cards):
            parts = c_fmt.split('|')
            for line in content.splitlines():
                if parts[0] in line:
                    found[c_fmt] = line
                    break
            else:
                found[c_fmt] = ""

        if not found: return []
        return self._extract_info(found, os.path.dirname(fpath))

    def _process_zip(self, zpath):
        res = []
        try:
            with zipfile.ZipFile(zpath, 'r') as z:
                for txt_name in z.namelist():
                    if not txt_name.lower().endswith('.txt'): continue
                    try: content = z.read(txt_name).decode('utf-8', errors='ignore')
                    except: continue
                    
                    zccv_cards = extract_cards_zccv(content)
                    for cc, m, y, cvv in P_CC.findall(content):
                        if is_valid(cc, m, y, cvv):
                            zccv_cards.append(fmt(cc, m, y, cvv))

                    found = {}
                    for c_fmt in set(zccv_cards):
                        parts = c_fmt.split('|')
                        for line in content.splitlines():
                            if parts[0] in line:
                                found[c_fmt] = line
                                break
                        else:
                            found[c_fmt] = ""
                    
                    if found:
                        res.extend(self._extract_info(found, zpath + "::" + txt_name))
        except: pass
        return res

    def _extract_info(self, found_dict, log_root):
        email, ip = "", ""
        info_txt = os.path.join(log_root, "information.txt")
        if os.path.exists(info_txt):
            try:
                with open(info_txt, 'r', encoding='utf-8', errors='ignore') as inf:
                    content = inf.read()
                    m_ip = re.search(r'\b(?:IP|ip)\s*[:=]\s*(\d{1,3}(?:\.\d{1,3}){3})\b', content)
                    if m_ip: ip = m_ip.group(1)
            except: pass

        res = []
        for c_fmt, line_ctx in found_dict.items():
            parts = c_fmt.split('|')
            m_email = P_EMAIL.search(line_ctx)
            c_email = m_email.group(0) if m_email else email
            m_ip = P_IP.search(line_ctx)
            c_ip = m_ip.group(1) if m_ip else ip

            res.append({
                "cc": parts[0], "exp": f"{parts[1]}/{parts[2]}", "cvv": parts[3],
                "brand": "...", "type": "...", "level": "...", "bank": "...", "country": "...",
                "email": c_email, "ip": c_ip, "log": log_root,
                "bin": parts[0][:6]
            })
        return res

class TabCCExtractor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("CC Extractor (Từ Log)")
        title.setProperty("class", "PageTitle")
        layout.addWidget(title)

        ctrl_layout = QHBoxLayout()
        self.btn_select = QPushButton("Chọn Thư Mục Log")
        self.btn_select.setProperty("class", "BtnNeon")
        self.btn_select.clicked.connect(self.select_folder)
        ctrl_layout.addWidget(self.btn_select)

        self.lbl_folder = QLabel("Chưa chọn thư mục")
        self.lbl_folder.setStyleSheet("color: #94A3B8;")
        ctrl_layout.addWidget(self.lbl_folder)
        ctrl_layout.addStretch()

        self.btn_scan = QPushButton("BẮT ĐẦU QUÉT")
        self.btn_scan.setProperty("class", "BtnNeon")
        self.btn_scan.setEnabled(False)
        self.btn_scan.clicked.connect(self.start_scan)
        ctrl_layout.addWidget(self.btn_scan)

        self.btn_export = QPushButton("XUẤT CSV")
        self.btn_export.setProperty("class", "BtnNeon")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.export_csv)
        ctrl_layout.addWidget(self.btn_export)
        layout.addLayout(ctrl_layout)

        self.table = QTableWidget(0, 12)
        self.table.setHorizontalHeaderLabels([
            "Card Number", "Exp", "CVV", "Brand", "Type", "Level", "Bank", "Country", "Email", "IP", "Log Path", "BIN"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 150)
        self.table.setColumnWidth(7, 100)
        self.table.setColumnWidth(8, 200)
        self.table.setColumnWidth(9, 120)
        self.table.setColumnWidth(10, 250)
        
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1A1D24; color: #E2E8F0; border: 1px solid #2D313A; font-size: 13px; }
            QHeaderView::section { background-color: #252A34; color: #00F0FF; font-weight: bold; padding: 5px; }
        """)
        layout.addWidget(self.table)

        self.log_box = QLabel("Sẵn sàng.")
        layout.addWidget(self.log_box)

        self.folder_path = ""
        self.all_results = []

    def select_folder(self):
        p = QFileDialog.getExistingDirectory(self, "Chọn Thư Mục Log")
        if p:
            self.folder_path = p
            self.lbl_folder.setText(p)
            self.btn_scan.setEnabled(True)

    def start_scan(self):
        if not self.folder_path: return
        self.table.setRowCount(0)
        self.all_results.clear()
        self.btn_scan.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.log_box.setText("Đang quét...")

        self.worker = CCScanWorker(self.folder_path)
        self.worker.row_signal.connect(self.add_rows)
        self.worker.finished_signal.connect(self.scan_done)
        self.worker.start()

    def add_rows(self, cards):
        for c in cards:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(c["cc"]))
            self.table.setItem(row, 1, QTableWidgetItem(c["exp"]))
            self.table.setItem(row, 2, QTableWidgetItem(c["cvv"]))
            self.table.setItem(row, 3, QTableWidgetItem(c["brand"]))
            self.table.setItem(row, 4, QTableWidgetItem(c["type"]))
            self.table.setItem(row, 5, QTableWidgetItem(c["level"]))
            self.table.setItem(row, 6, QTableWidgetItem(c["bank"]))
            self.table.setItem(row, 7, QTableWidgetItem(c["country"]))
            self.table.setItem(row, 8, QTableWidgetItem(c["email"]))
            self.table.setItem(row, 9, QTableWidgetItem(c["ip"]))
            self.table.setItem(row, 10, QTableWidgetItem(c["log"]))
            
            bin_item = QTableWidgetItem(c["bin"])
            self.table.setItem(row, 11, bin_item)
            self.table.setColumnHidden(11, True)
            
            self.all_results.append(c)

    def scan_done(self, total):
        self.log_box.setText(f"Hoàn tất! Tìm thấy {total} thẻ.")
        self.btn_scan.setEnabled(True)
        if total > 0: self.btn_export.setEnabled(True)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu File CSV", "", "CSV (*.csv)")
        if not path: return
        try:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Card", "Exp", "CVV", "Brand", "Type", "Level", "Bank", "Country", "Email", "IP", "Log"])
                for r in self.all_results:
                    writer.writerow([r["cc"], r["exp"], r["cvv"], r["brand"], r["type"], r["level"], r["bank"], r["country"], r["email"], r["ip"], r["log"]])
            QMessageBox.information(self, "Thành công", "Đã xuất file CSV!")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", str(e))
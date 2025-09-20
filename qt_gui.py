import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
                             QTableWidgetItem, QDialog, QTextEdit, QLabel, 
                             QLineEdit, QFileDialog, QMessageBox, QProgressBar,
                             QGroupBox, QGridLayout, QComboBox, QSpinBox,
                             QTextBrowser, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import threading
import time
from datetime import datetime

# Import các function từ main.py
from main import (get_access_token, generate_image, 
                 generate_image_from_image, generate_image_from_multiple_images,
                 upload_image_to_google_labs, save_base64_image, sanitize_filename)
import main  # Import module để truy cập biến global

class CookieDialog(QDialog):
    """Dialog để thêm cookie mới"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thêm Cookie")
        self.setModal(True)
        self.setFixedSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Label hướng dẫn
        instruction_label = QLabel("Nhập cookie từ Google Labs:")
        instruction_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(instruction_label)
        
        # Text area cho cookie
        self.cookie_text = QTextEdit()
        self.cookie_text.setPlaceholderText("Dán cookie từ trình duyệt vào đây...")
        self.cookie_text.setMaximumHeight(200)
        layout.addWidget(self.cookie_text)
        
        # Label tên tài khoản
        name_label = QLabel("Tên tài khoản:")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nhập tên để dễ nhận biết...")
        layout.addWidget(self.name_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Kiểm tra Cookie")
        self.test_button.clicked.connect(self.test_cookie)
        button_layout.addWidget(self.test_button)
        
        self.add_button = QPushButton("Thêm")
        self.add_button.clicked.connect(self.accept)
        self.add_button.setEnabled(False)
        button_layout.addWidget(self.add_button)
        
        cancel_button = QPushButton("Hủy")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Kết nối signal để enable/disable nút Add
        self.cookie_text.textChanged.connect(self.on_text_changed)
        self.name_input.textChanged.connect(self.on_text_changed)
    
    def on_text_changed(self):
        """Enable nút Add khi có đủ thông tin"""
        has_cookie = bool(self.cookie_text.toPlainText().strip())
        has_name = bool(self.name_input.text().strip())
        self.add_button.setEnabled(has_cookie and has_name)
    
    def test_cookie(self):
        """Kiểm tra cookie có hợp lệ không"""
        cookie = self.cookie_text.toPlainText().strip()
        if not cookie:
            self.status_label.setText("Vui lòng nhập cookie")
            self.status_label.setStyleSheet("color: red;")
            return
        
        self.status_label.setText("Đang kiểm tra cookie...")
        self.status_label.setStyleSheet("color: blue;")
        self.test_button.setEnabled(False)
        
        # Test cookie trong thread riêng
        self.test_thread = CookieTestThread(cookie)
        self.test_thread.result.connect(self.on_test_result)
        self.test_thread.start()
    
    def on_test_result(self, success, message, user_info):
        """Xử lý kết quả test cookie"""
        self.test_button.setEnabled(True)
        
        if success:
            self.status_label.setText(f"✅ Cookie hợp lệ - {message}")
            self.status_label.setStyleSheet("color: green;")
            # Tự động điền tên nếu chưa có
            if not self.name_input.text().strip():
                self.name_input.setText(user_info.get('name', ''))
        else:
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet("color: red;")
    
    def get_cookie_data(self):
        """Lấy dữ liệu cookie từ dialog"""
        return {
            'cookie': self.cookie_text.toPlainText().strip(),
            'name': self.name_input.text().strip(),
            'validated': True,
            'user_info': {}
        }

class CookieTestThread(QThread):
    """Thread để test cookie"""
    result = pyqtSignal(bool, str, dict)
    
    def __init__(self, cookie):
        super().__init__()
        self.cookie = cookie
    
    def run(self):
        try:
            access_data = get_access_token(self.cookie)
            if access_data and access_data.get('access_token'):
                user_info = access_data.get('user', {})
                name = user_info.get('name', 'Unknown')
                email = user_info.get('email', 'Unknown')
                self.result.emit(True, f"{name} ({email})", user_info)
            else:
                self.result.emit(False, "Cookie không hợp lệ hoặc đã hết hạn", {})
        except Exception as e:
            self.result.emit(False, f"Lỗi khi kiểm tra: {str(e)}", {})

class AccountManagementTab(QWidget):
    """Tab quản lý tài khoản"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_cookies()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Accounts Group Box
        accounts_group = QGroupBox("Accounts")
        accounts_layout = QVBoxLayout()
        
        # Header buttons
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        
        # Buttons
        self.add_button = QPushButton("Add Cookie")
        self.add_button.clicked.connect(self.add_cookie)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-family: "Open Sans";
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        header_layout.addWidget(self.add_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_table)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-family: "Open Sans";
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        header_layout.addWidget(self.refresh_button)
        
        accounts_layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["NAME", "EMAIL", "STATUS", "ACTION"])
        
        # Styling table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 3px;
                gridline-color: #f0f0f0;
                font-family: "Open Sans";
                border: none;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-right: 1px solid #f0f0f0;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
                font-size: 12px;
                font-family: "Open Sans";
                color: #333;
            }
            QHeaderView::section:first {
                border-left: none;
            }
            QHeaderView::section:last {
                border-right: none;
            }
           
        """)
        
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(40)
        # Căn giữa header
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        
        # Căn giữa nội dung các cột
        self.table.setColumnWidth(0, 150)  # Tên
        self.table.setColumnWidth(1, 200)  # Email  
        self.table.setColumnWidth(2, 120)  # Trạng thái
        # Cột Thao tác sẽ tự động stretch
        
        accounts_layout.addWidget(self.table)
        accounts_group.setLayout(accounts_layout)
        
        layout.addWidget(accounts_group)
        self.setLayout(layout)
    
    def load_cookies(self):
        """Load cookies từ file cookies.json"""
        try:
            if os.path.exists('cookies.json'):
                with open('cookies.json', 'r', encoding='utf-8') as f:
                    self.cookies_data = json.load(f)
            else:
                self.cookies_data = {}
            
            self.refresh_table()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể load cookies: {str(e)}")
            self.cookies_data = {}
    
    def refresh_table(self):
        """Làm mới bảng hiển thị"""
        self.table.setRowCount(len(self.cookies_data))
        
        for row, (account_name, data) in enumerate(self.cookies_data.items()):
            # Tên tài khoản
            name_item = QTableWidgetItem(account_name)
            name_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, name_item)
            
            # Email
            email = data.get('user_info', {}).get('email', 'N/A')
            email_item = QTableWidgetItem(email)
            email_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, email_item)
            
            # Trạng thái
            status = "✅ Hợp lệ" if data.get('validated', False) else "❌ Lỗi"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            if data.get('validated', False):
                status_item.setForeground(Qt.darkGreen)
                status_item.setFont(QFont("Roboto", 10, QFont.Bold))
            else:
                status_item.setForeground(Qt.darkRed)
                status_item.setFont(QFont("Roboto", 10, QFont.Bold))
            self.table.setItem(row, 2, status_item)
            
            # Thao tác
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(5, 2, 5, 2)
            action_layout.setAlignment(Qt.AlignCenter)
            
            test_btn = QPushButton("Checker")
            test_btn.setMaximumWidth(70)
            test_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-family: "Open Sans";
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            test_btn.clicked.connect(lambda checked, name=account_name: self.test_account(name))
            action_layout.addWidget(test_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.setMaximumWidth(60)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-family: "Open Sans";
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            delete_btn.clicked.connect(lambda checked, name=account_name: self.delete_account(name))
            action_layout.addWidget(delete_btn)
            
            action_widget.setLayout(action_layout)
            self.table.setCellWidget(row, 3, action_widget)
    
    def add_cookie(self):
        """Hiển thị dialog thêm cookie"""
        dialog = CookieDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            cookie_data = dialog.get_cookie_data()
            account_name = cookie_data['name']
            
            # Test cookie một lần nữa để lấy user_info
            try:
                access_data = get_access_token(cookie_data['cookie'])
                if access_data and access_data.get('access_token'):
                    cookie_data['user_info'] = access_data.get('user', {})
                    cookie_data['validated'] = True
                    
                    # Lưu vào cookies.json
                    self.cookies_data[account_name] = cookie_data
                    self.save_cookies()
                    self.refresh_table()
                    
                    QMessageBox.information(self, "Thành công", f"Đã thêm tài khoản {account_name}")
                else:
                    QMessageBox.warning(self, "Lỗi", "Cookie không hợp lệ")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể xác thực cookie: {str(e)}")
    
    def test_account(self, account_name):
        """Test lại tài khoản"""
        if account_name not in self.cookies_data:
            return
        
        cookie = self.cookies_data[account_name]['cookie']
        
        # Test trong thread
        self.test_thread = CookieTestThread(cookie)
        self.test_thread.result.connect(lambda success, msg, info: self.on_test_complete(account_name, success, msg, info))
        self.test_thread.start()
    
    def on_test_complete(self, account_name, success, message, user_info):
        """Xử lý kết quả test"""
        if account_name in self.cookies_data:
            self.cookies_data[account_name]['validated'] = success
            if success:
                self.cookies_data[account_name]['user_info'] = user_info
                self.save_cookies()
                self.refresh_table()
                QMessageBox.information(self, "Kết quả", f"✅ {message}")
            else:
                QMessageBox.warning(self, "Kết quả", f"❌ {message}")
    
    def delete_account(self, account_name):
        """Xóa tài khoản"""
        reply = QMessageBox.question(self, "Xác nhận", 
                                   f"Bạn có chắc muốn xóa tài khoản '{account_name}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if account_name in self.cookies_data:
                del self.cookies_data[account_name]
                self.save_cookies()
                self.refresh_table()
                QMessageBox.information(self, "Thành công", f"Đã xóa tài khoản {account_name}")
    
    def save_cookies(self):
        """Lưu cookies vào file"""
        try:
            with open('cookies.json', 'w', encoding='utf-8') as f:
                json.dump(self.cookies_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể lưu cookies: {str(e)}")

class ImageGenerationTab(QWidget):
    """Tab tạo ảnh"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Generation Image Group Box
        generation_group = QGroupBox("Generation Image")
        generation_layout = QVBoxLayout()
        
        # Splitter để chia 2 phần
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel trái - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)
        
        # Chọn tài khoản
        account_group = QGroupBox("Chọn Tài khoản")
        account_layout = QVBoxLayout()
        
        self.account_combo = QComboBox()
        self.load_accounts()
        account_layout.addWidget(self.account_combo)
        
        account_group.setLayout(account_layout)
        left_layout.addWidget(account_group)
        
        # Chọn chế độ
        mode_group = QGroupBox("Chế độ Tạo Ảnh")
        mode_layout = QVBoxLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Prompt to Image", "Image to Image", "Import Excel"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        
        mode_group.setLayout(mode_layout)
        left_layout.addWidget(mode_group)
        
        # Prompt (chỉ hiện khi không phải Excel mode)
        self.prompt_group = QGroupBox("Prompt")
        prompt_layout = QVBoxLayout()
        
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("Nhập mô tả ảnh bạn muốn tạo...")
        prompt_layout.addWidget(self.prompt_text)
        
        self.prompt_group.setLayout(prompt_layout)
        left_layout.addWidget(self.prompt_group, 1)  # Stretch factor = 1
        
        # Excel file selection (chỉ hiện khi Excel mode)
        self.excel_group = QGroupBox("File Excel")
        excel_layout = QVBoxLayout()
        
        self.excel_path_label = QLabel("Chưa chọn file Excel")
        self.excel_path_label.setStyleSheet("color: gray; font-style: italic;")
        excel_layout.addWidget(self.excel_path_label)
        
        self.select_excel_btn = QPushButton("Chọn File Excel")
        self.select_excel_btn.clicked.connect(self.select_excel_file)
        excel_layout.addWidget(self.select_excel_btn)
        
        # Preview Excel data
        self.excel_preview_label = QLabel("")
        self.excel_preview_label.setStyleSheet("color: blue; font-size: 12px;")
        self.excel_preview_label.setWordWrap(True)
        excel_layout.addWidget(self.excel_preview_label)
        
        # Excel data table
        self.excel_table = QTableWidget()
        self.excel_table.setColumnCount(8)
        self.excel_table.setHorizontalHeaderLabels(["STT", "PROMPT", "SUBJECT", "SUBJECT_CAPTION", "SCENE", "SCENE_CAPTION", "STYLE", "STYLE_CAPTION"])
        self.excel_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 3px;
                gridline-color: #f0f0f0;
                font-family: "Open Sans";
                border: none;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-right: 1px solid #f0f0f0;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
                font-size: 12px;
                font-family: "Open Sans";
                color: #333;
            }
            QHeaderView::section:first {
                border-left: none;
            }
            QHeaderView::section:last {
                border-right: none;
            }
        """)
        self.excel_table.setAlternatingRowColors(True)
        self.excel_table.horizontalHeader().setStretchLastSection(True)
        self.excel_table.verticalHeader().setDefaultSectionSize(35)
        
        # Căn giữa header
        header = self.excel_table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        
        excel_layout.addWidget(self.excel_table)
        
        self.excel_group.setLayout(excel_layout)
        left_layout.addWidget(self.excel_group, 2)  # Stretch factor = 2 (lớn nhất)
        self.excel_group.setVisible(False)  # Ẩn ban đầu
        
        # Image upload (chỉ hiện khi chọn Image to Image)
        self.image_group = QGroupBox("Ảnh Gốc")
        image_layout = QVBoxLayout()
        
        # Subject Image
        subject_layout = QVBoxLayout()
        subject_header = QHBoxLayout()
        subject_header.addWidget(QLabel("Subject:"))
        self.subject_path_label = QLabel("Chưa chọn")
        self.subject_path_label.setStyleSheet("color: gray; font-style: italic;")
        subject_header.addWidget(self.subject_path_label)
        self.select_subject_btn = QPushButton("Chọn")
        self.select_subject_btn.clicked.connect(lambda: self.select_image("subject"))
        subject_header.addWidget(self.select_subject_btn)
        subject_layout.addLayout(subject_header)
        
        self.subject_caption_input = QLineEdit()
        self.subject_caption_input.setPlaceholderText("Nhập caption cho ảnh Subject...")
        self.subject_caption_input.setEnabled(False)
        subject_layout.addWidget(self.subject_caption_input)
        image_layout.addLayout(subject_layout)
        
        # Scene Image
        scene_layout = QVBoxLayout()
        scene_header = QHBoxLayout()
        scene_header.addWidget(QLabel("Scene:"))
        self.scene_path_label = QLabel("Chưa chọn")
        self.scene_path_label.setStyleSheet("color: gray; font-style: italic;")
        scene_header.addWidget(self.scene_path_label)
        self.select_scene_btn = QPushButton("Chọn")
        self.select_scene_btn.clicked.connect(lambda: self.select_image("scene"))
        scene_header.addWidget(self.select_scene_btn)
        scene_layout.addLayout(scene_header)
        
        self.scene_caption_input = QLineEdit()
        self.scene_caption_input.setPlaceholderText("Nhập caption cho ảnh Scene...")
        self.scene_caption_input.setEnabled(False)
        scene_layout.addWidget(self.scene_caption_input)
        image_layout.addLayout(scene_layout)
        
        # Style Image
        style_layout = QVBoxLayout()
        style_header = QHBoxLayout()
        style_header.addWidget(QLabel("Style:"))
        self.style_path_label = QLabel("Chưa chọn")
        self.style_path_label.setStyleSheet("color: gray; font-style: italic;")
        style_header.addWidget(self.style_path_label)
        self.select_style_btn = QPushButton("Chọn")
        self.select_style_btn.clicked.connect(lambda: self.select_image("style"))
        style_header.addWidget(self.select_style_btn)
        style_layout.addLayout(style_header)
        
        self.style_caption_input = QLineEdit()
        self.style_caption_input.setPlaceholderText("Nhập caption cho ảnh Style...")
        self.style_caption_input.setEnabled(False)
        style_layout.addWidget(self.style_caption_input)
        image_layout.addLayout(style_layout)
        
        self.image_group.setLayout(image_layout)
        left_layout.addWidget(self.image_group, 1)  # Stretch factor = 1
        self.image_group.setVisible(False)  # Ẩn ban đầu
        
        # Settings
        settings_group = QGroupBox("Cài đặt")
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Seed:"), 0, 0)
        self.seed_spinbox = QSpinBox()
        self.seed_spinbox.setRange(0, 999999)
        self.seed_spinbox.setValue(0)
        settings_layout.addWidget(self.seed_spinbox, 0, 1)
        
        settings_layout.addWidget(QLabel("Số lượng:"), 1, 0)
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setRange(1, 10)
        self.count_spinbox.setValue(1)
        settings_layout.addWidget(self.count_spinbox, 1, 1)
        
        # Thread count cho Excel mode
        settings_layout.addWidget(QLabel("Số luồng:"), 2, 0)
        self.thread_spinbox = QSpinBox()
        self.thread_spinbox.setRange(1, 5)  # Tối đa 5 luồng
        self.thread_spinbox.setValue(5)     # Mặc định 5 luồng
        settings_layout.addWidget(self.thread_spinbox, 2, 1)
        
        # Aspect ratio
        settings_layout.addWidget(QLabel("Tỷ lệ:"), 3, 0)
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems([
            "1:1 (Square)", 
            "16:9 (Landscape)", 
            "9:16 (Portrait)"
        ])
        self.aspect_combo.setCurrentText("16:9 (Landscape)")  # Mặc định
        settings_layout.addWidget(self.aspect_combo, 3, 1)
        
        settings_group.setLayout(settings_layout)
        left_layout.addWidget(settings_group, 0)  # Stretch factor = 0 (không mở rộng)
        
        # Generate button
        self.generate_btn = QPushButton("Tạo Ảnh")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_image)
        left_layout.addWidget(self.generate_btn, 0)  # Stretch factor = 0 (không mở rộng)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(40)  # Cùng chiều cao với button
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
                font-family: "Open Sans";
                font-size: 12px;
                background-color: #f5f5f5;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 4px;
            }
        """)
        left_layout.addWidget(self.progress_bar, 0)  # Stretch factor = 0 (không mở rộng)
        
        left_panel.setLayout(left_layout)
        
        # Panel phải - Log
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        log_label = QLabel("Nhật ký")
        log_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(log_label)
        
        self.log_text = QTextBrowser()
        self.log_text.setStyleSheet("""
            QTextBrowser {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        right_layout.addWidget(self.log_text)
        
        right_panel.setLayout(right_layout)
        
        # Thêm panels vào splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 300])
        
        generation_layout.addWidget(splitter)
        generation_group.setLayout(generation_layout)
        
        layout.addWidget(generation_group)
        self.setLayout(layout)
        
        # Biến lưu trữ
        self.selected_subject_path = None
        self.selected_scene_path = None
        self.selected_style_path = None
        self.selected_excel_path = None
        self.generation_thread = None
    
    def load_accounts(self):
        """Load danh sách tài khoản"""
        self.account_combo.clear()
        
        try:
            if os.path.exists('cookies.json'):
                with open('cookies.json', 'r', encoding='utf-8') as f:
                    cookies_data = json.load(f)
                
                for account_name, data in cookies_data.items():
                    if data.get('validated', False):
                        email = data.get('user_info', {}).get('email', 'N/A')
                        self.account_combo.addItem(f"{account_name} ({email})", account_name)
        except Exception as e:
            self.log_message(f"Lỗi khi load tài khoản: {str(e)}")
    
    def on_mode_changed(self, mode):
        """Xử lý khi thay đổi chế độ"""
        is_excel_mode = "Excel" in mode
        is_img2img_mode = "Image to Image" in mode
        
        # Hiện/ẩn các group tương ứng
        self.prompt_group.setVisible(not is_excel_mode)
        self.excel_group.setVisible(is_excel_mode)
        self.image_group.setVisible(is_img2img_mode and not is_excel_mode)
        
        # Reset data khi thay đổi mode
        if not is_excel_mode:
            self.selected_excel_path = None
            self.excel_path_label.setText("Chưa chọn file Excel")
            self.excel_preview_label.setText("")
            self.excel_table.setRowCount(0)
            # Reset về 8 cột cho Image to Image mode
            self.excel_table.setColumnCount(8)
            self.excel_table.setHorizontalHeaderLabels(["STT", "PROMPT", "SUBJECT", "SUBJECT_CAPTION", "SCENE", "SCENE_CAPTION", "STYLE", "STYLE_CAPTION"])
        
        if not is_img2img_mode:
            self.selected_subject_path = None
            self.selected_scene_path = None
            self.selected_style_path = None
            self.subject_path_label.setText("Chưa chọn")
            self.scene_path_label.setText("Chưa chọn")
            self.style_path_label.setText("Chưa chọn")
            self.subject_caption_input.setEnabled(False)
            self.subject_caption_input.setText("")
            self.scene_caption_input.setEnabled(False)
            self.scene_caption_input.setText("")
            self.style_caption_input.setEnabled(False)
            self.style_caption_input.setText("")
    
    def select_image(self, image_type):
        """Chọn ảnh gốc theo loại"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Chọn ảnh {image_type}", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        
        if file_path:
            if image_type == "subject":
                self.selected_subject_path = file_path
                self.subject_path_label.setText(os.path.basename(file_path))
                self.subject_path_label.setStyleSheet("color: black;")
                self.subject_caption_input.setEnabled(True)
                self.subject_caption_input.setText("Subject")  # Default caption
            elif image_type == "scene":
                self.selected_scene_path = file_path
                self.scene_path_label.setText(os.path.basename(file_path))
                self.scene_path_label.setStyleSheet("color: black;")
                self.scene_caption_input.setEnabled(True)
                self.scene_caption_input.setText("Scene")  # Default caption
            elif image_type == "style":
                self.selected_style_path = file_path
                self.style_path_label.setText(os.path.basename(file_path))
                self.style_path_label.setStyleSheet("color: black;")
                self.style_caption_input.setEnabled(True)
                self.style_caption_input.setText("Style")  # Default caption
    
    def select_excel_file(self):
        """Chọn file Excel"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Excel", "", "Excel Files (*.xlsx *.xls)")
        
        if file_path:
            self.selected_excel_path = file_path
            self.excel_path_label.setText(os.path.basename(file_path))
            self.excel_path_label.setStyleSheet("color: black;")
            
            # Preview Excel data
            self.preview_excel_data(file_path)
    
    def preview_excel_data(self, file_path):
        """Preview dữ liệu Excel"""
        try:
            import pandas as pd
            
            mode = self.mode_combo.currentText()
            df = pd.read_excel(file_path)
            
            if "Excel" in mode:
                # Excel: STT, PROMPT, SUBJECT, SUBJECT_CAPTION, SCENE, SCENE_CAPTION, STYLE, STYLE_CAPTION
                if len(df.columns) >= 2:
                    stt_list = df.iloc[:, 0].tolist()
                    prompt_list = df.iloc[:, 1].tolist()
                    
                    # Lấy các cột ảnh và caption (có thể để trống)
                    subject_list = df.iloc[:, 2].fillna("").tolist() if len(df.columns) > 2 else [""] * len(stt_list)
                    subject_caption_list = df.iloc[:, 3].fillna("").tolist() if len(df.columns) > 3 else [""] * len(stt_list)
                    scene_list = df.iloc[:, 4].fillna("").tolist() if len(df.columns) > 4 else [""] * len(stt_list)
                    scene_caption_list = df.iloc[:, 5].fillna("").tolist() if len(df.columns) > 5 else [""] * len(stt_list)
                    style_list = df.iloc[:, 6].fillna("").tolist() if len(df.columns) > 6 else [""] * len(stt_list)
                    style_caption_list = df.iloc[:, 7].fillna("").tolist() if len(df.columns) > 7 else [""] * len(stt_list)
                    
                    # Tự động detect mode dựa trên dữ liệu
                    has_images = any(
                        str(subject).strip() and str(subject).strip().lower() != 'nan' or
                        str(scene).strip() and str(scene).strip().lower() != 'nan' or
                        str(style).strip() and str(style).strip().lower() != 'nan'
                        for subject, scene, style in zip(subject_list, scene_list, style_list)
                    )
                    
                    detected_mode = "Image to Image" if has_images else "Prompt to Image"
                    preview_text = f"📊 Đã đọc {len(stt_list)} dòng dữ liệu - Tự động detect: {detected_mode}"
                    self.excel_preview_label.setText(preview_text)
                    
                    # Hiển thị trong table (8 cột)
                    self.excel_table.setColumnCount(8)
                    self.excel_table.setHorizontalHeaderLabels(["STT", "PROMPT", "SUBJECT", "SUBJECT_CAPTION", "SCENE", "SCENE_CAPTION", "STYLE", "STYLE_CAPTION"])
                    self.excel_table.setRowCount(len(stt_list))
                    
                    for i, (stt, prompt, subject, subject_caption, scene, scene_caption, style, style_caption) in enumerate(zip(
                        stt_list, prompt_list, subject_list, subject_caption_list, 
                        scene_list, scene_caption_list, style_list, style_caption_list)):
                        
                        # STT
                        stt_item = QTableWidgetItem(str(stt))
                        stt_item.setTextAlignment(Qt.AlignCenter)
                        self.excel_table.setItem(i, 0, stt_item)
                        
                        # Prompt
                        prompt_item = QTableWidgetItem(str(prompt))
                        self.excel_table.setItem(i, 1, prompt_item)
                        
                        # Subject
                        subject_item = QTableWidgetItem(str(subject))
                        self.excel_table.setItem(i, 2, subject_item)
                        
                        # Subject Caption
                        subject_caption_item = QTableWidgetItem(str(subject_caption))
                        self.excel_table.setItem(i, 3, subject_caption_item)
                        
                        # Scene
                        scene_item = QTableWidgetItem(str(scene))
                        self.excel_table.setItem(i, 4, scene_item)
                        
                        # Scene Caption
                        scene_caption_item = QTableWidgetItem(str(scene_caption))
                        self.excel_table.setItem(i, 5, scene_caption_item)
                        
                        # Style
                        style_item = QTableWidgetItem(str(style))
                        self.excel_table.setItem(i, 6, style_item)
                        
                        # Style Caption
                        style_caption_item = QTableWidgetItem(str(style_caption))
                        self.excel_table.setItem(i, 7, style_caption_item)
                else:
                    preview_text = "❌ File Excel cần có ít nhất 2 cột: STT, PROMPT"
                    self.excel_preview_label.setText(preview_text)
                    self.excel_table.setRowCount(0)
            
        except Exception as e:
            self.excel_preview_label.setText(f"❌ Lỗi khi đọc file Excel: {str(e)}")
            self.excel_preview_label.setStyleSheet("color: red; font-size: 12px;")
            self.excel_table.setRowCount(0)
    
    def get_aspect_ratio(self):
        """Lấy aspect ratio từ combo box"""
        aspect_text = self.aspect_combo.currentText()
        if "Square" in aspect_text:
            return "IMAGE_ASPECT_RATIO_SQUARE"
        elif "Portrait" in aspect_text:
            return "IMAGE_ASPECT_RATIO_PORTRAIT"
        else:  # Landscape
            return "IMAGE_ASPECT_RATIO_LANDSCAPE"
    
    def log_message(self, message):
        """Thêm message vào log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Scroll xuống cuối
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def generate_image(self):
        """Tạo ảnh"""
        # Kiểm tra dữ liệu đầu vào
        if self.account_combo.count() == 0:
            QMessageBox.warning(self, "Lỗi", "Chưa có tài khoản nào")
            return
        
        mode = self.mode_combo.currentText()
        is_excel_mode = "Excel" in mode
        
        # Kiểm tra dữ liệu theo mode
        if is_excel_mode:
            if not self.selected_excel_path:
                QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file Excel")
                return
        else:
            prompt = self.prompt_text.toPlainText().strip()
            if not prompt:
                QMessageBox.warning(self, "Lỗi", "Vui lòng nhập prompt")
                return
            
            if mode == "Image to Image":
                if not self.selected_subject_path and not self.selected_scene_path and not self.selected_style_path:
                    QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ít nhất một ảnh (Subject, Scene, hoặc Style)")
                    return
        
        # Lấy thông tin tài khoản
        account_name = self.account_combo.currentData()
        try:
            with open('cookies.json', 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            
            if account_name not in cookies_data:
                QMessageBox.warning(self, "Lỗi", "Tài khoản không tồn tại")
                return
            
            cookie_data = cookies_data[account_name]
            cookie = cookie_data['cookie']
            
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể đọc thông tin tài khoản: {str(e)}")
            return
        
        # Disable button và hiện progress
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Tạo thread để generate
        aspect_ratio = self.get_aspect_ratio()
        if is_excel_mode:
            self.generation_thread = ExcelGenerationThread(
                cookie, mode, self.selected_excel_path, 
                self.seed_spinbox.value(), self.thread_spinbox.value(), aspect_ratio
            )
        else:
            prompt = self.prompt_text.toPlainText().strip()
            self.generation_thread = ImageGenerationThread(
                cookie, prompt, mode, 
                self.selected_subject_path, self.selected_scene_path, self.selected_style_path,
                self.subject_caption_input.text(), self.scene_caption_input.text(), self.style_caption_input.text(),
                self.seed_spinbox.value(), self.count_spinbox.value(), aspect_ratio
            )
        
        self.generation_thread.progress.connect(self.log_message)
        self.generation_thread.finished.connect(self.on_generation_finished)
        self.generation_thread.start()
    
    def on_generation_finished(self, success, message):
        """Xử lý khi hoàn thành tạo ảnh"""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Thành công", message)
        else:
            QMessageBox.warning(self, "Lỗi", message)

class ExcelGenerationThread(QThread):
    """Thread để tạo ảnh từ Excel"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, cookie, mode, excel_path, seed, thread_count, aspect_ratio):
        super().__init__()
        self.cookie = cookie
        self.mode = mode
        self.excel_path = excel_path
        self.seed = seed
        self.thread_count = thread_count
        self.aspect_ratio = aspect_ratio
    
    def run(self):
        try:
            import pandas as pd
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            # Lấy access token
            self.progress.emit("Đang xác thực tài khoản...")
            access_data = get_access_token(self.cookie)
            
            if not access_data or not access_data.get('access_token'):
                self.finished.emit(False, "Không thể xác thực tài khoản")
                return
            
            access_token = access_data.get('access_token')
            self.progress.emit("✅ Xác thực thành công")
            
            # Tạo thư mục output
            output_folder = "generated_images"
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            # Đọc dữ liệu Excel
            self.progress.emit("Đang đọc file Excel...")
            
            if "Excel" in self.mode:
                # Excel: STT, PROMPT, SUBJECT, SUBJECT_CAPTION, SCENE, SCENE_CAPTION, STYLE, STYLE_CAPTION
                df = pd.read_excel(self.excel_path)
                if len(df.columns) < 2:
                    self.finished.emit(False, "File Excel cần có ít nhất 2 cột: STT, PROMPT")
                    return
                
                stt_list = df.iloc[:, 0].tolist()
                prompt_list = df.iloc[:, 1].tolist()
                
                # Lấy các cột ảnh và caption (có thể để trống)
                subject_list = df.iloc[:, 2].fillna("").tolist() if len(df.columns) > 2 else [""] * len(stt_list)
                subject_caption_list = df.iloc[:, 3].fillna("").tolist() if len(df.columns) > 3 else [""] * len(stt_list)
                scene_list = df.iloc[:, 4].fillna("").tolist() if len(df.columns) > 4 else [""] * len(stt_list)
                scene_caption_list = df.iloc[:, 5].fillna("").tolist() if len(df.columns) > 5 else [""] * len(stt_list)
                style_list = df.iloc[:, 6].fillna("").tolist() if len(df.columns) > 6 else [""] * len(stt_list)
                style_caption_list = df.iloc[:, 7].fillna("").tolist() if len(df.columns) > 7 else [""] * len(stt_list)
                
                # Tự động detect mode và validate dữ liệu
                valid_data = []
                prompt_to_image_count = 0
                image_to_image_count = 0
                
                for i, (stt, prompt, subject, subject_caption, scene, scene_caption, style, style_caption) in enumerate(zip(
                    stt_list, prompt_list, subject_list, subject_caption_list, 
                    scene_list, scene_caption_list, style_list, style_caption_list)):
                    
                    # Kiểm tra prompt có hợp lệ không
                    if not str(prompt).strip() or str(prompt).strip().lower() == 'nan':
                        continue
                    
                    # Kiểm tra có ảnh nào không
                    has_images = (
                        str(subject).strip() and str(subject).strip().lower() != 'nan' or
                        str(scene).strip() and str(scene).strip().lower() != 'nan' or
                        str(style).strip() and str(style).strip().lower() != 'nan'
                    )
                    
                    if has_images:
                        # Image to Image: cần ít nhất 1 ảnh
                        image_to_image_count += 1
                        valid_data.append((stt, prompt, subject, subject_caption, scene, scene_caption, style, style_caption, "Image to Image"))
                    else:
                        # Prompt to Image: chỉ cần prompt
                        prompt_to_image_count += 1
                        valid_data.append((stt, prompt, subject, subject_caption, scene, scene_caption, style, style_caption, "Prompt to Image"))
                
                # Thống kê
                total_valid = len(valid_data)
                self.progress.emit(f"📊 Validation: {total_valid} dòng hợp lệ ({prompt_to_image_count} Prompt to Image, {image_to_image_count} Image to Image)")
                
                excel_data = valid_data
            
            if not excel_data:
                self.finished.emit(False, "Không có dữ liệu trong file Excel")
                return
            
            self.progress.emit(f"✅ Đã đọc {len(excel_data)} dòng dữ liệu từ Excel")
            self.progress.emit(f"Bắt đầu tạo ảnh với {self.thread_count} luồng...")
            
            # Tạo danh sách tasks
            tasks = []
            for i, data in enumerate(excel_data):
                stt, prompt, subject, subject_caption, scene, scene_caption, style, style_caption, mode = data
                if mode == "Image to Image":
                    task_data = (stt, prompt, subject, subject_caption, scene, scene_caption, style, style_caption, 
                               access_token, self.cookie, output_folder, self.seed + i, self.aspect_ratio, "img2img")
                else:
                    task_data = (stt, prompt, subject, subject_caption, scene, scene_caption, style, style_caption, 
                               access_token, output_folder, self.seed + i, self.aspect_ratio, "prompt")
                tasks.append(task_data)
            
            success_count = 0
            
            # Sử dụng ThreadPoolExecutor để xử lý multi-threading
            with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
                # Submit tất cả tasks theo mode riêng
                future_to_task = {}
                for task in tasks:
                    # Lấy mode từ task data (phần tử cuối cùng)
                    task_mode = task[-1]
                    if task_mode == "img2img":
                        future_to_task[executor.submit(self.process_single_img2img_task, task)] = task
                    else:
                        future_to_task[executor.submit(self.process_single_image_task, task)] = task
                
                # Xử lý kết quả khi hoàn thành
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    stt = task[0]
                    
                    try:
                        result = future.result()
                        if result:
                            self.progress.emit(f"✅ Hoàn thành STT {stt}")
                            success_count += 1
                        else:
                            self.progress.emit(f"❌ Lỗi STT {stt}")
                    except Exception as e:
                        self.progress.emit(f"❌ Exception STT {stt}: {str(e)}")
            
            if success_count > 0:
                self.finished.emit(True, f"Tạo thành công {success_count}/{len(excel_data)} ảnh trong thư mục '{output_folder}'")
            else:
                self.finished.emit(False, "Không tạo được ảnh nào")
                
        except Exception as e:
            self.finished.emit(False, f"Lỗi: {str(e)}")
    
    def process_single_image_task(self, task_data):
        """Xử lý một task tạo ảnh trong thread"""
        stt, prompt, subject, subject_caption, scene, scene_caption, style, style_caption, access_token, output_folder, seed, aspect_ratio, task_mode = task_data
        
        try:
            # Gọi API tạo ảnh (chỉ dùng prompt)
            result = generate_image(access_token, prompt, seed, aspect_ratio)
            
            if result and 'imagePanels' in result:
                for panel in result['imagePanels']:
                    if 'generatedImages' in panel:
                        for img in panel['generatedImages']:
                            if 'encodedImage' in img:
                                filename = sanitize_filename(stt, prompt)
                                if save_base64_image(img['encodedImage'], filename, output_folder):
                                    return True
                                else:
                                    return False
            return False
            
        except Exception as e:
            return False
    
    def process_single_img2img_task(self, task_data):
        """Xử lý một task tạo ảnh từ nhiều ảnh trong thread"""
        stt, prompt, subject, subject_caption, scene, scene_caption, style, style_caption, access_token, cookie, output_folder, seed, aspect_ratio, task_mode = task_data
        
        try:
            # Upload các ảnh đã chọn
            upload_data_list = []
            
            if subject and str(subject).strip() and str(subject).strip().lower() != 'nan':
                upload_data = upload_image_to_google_labs(cookie, str(subject).strip())
                if upload_data:
                    upload_data_list.append({
                        'caption': str(subject_caption).strip() or 'Subject',
                        'mediaCategory': 'MEDIA_CATEGORY_SUBJECT',
                        'uploadMediaGenerationId': upload_data['uploadMediaGenerationId'],
                        'workflowId': upload_data['workflowId'],
                        'sessionId': upload_data['sessionId']
                    })
            
            if scene and str(scene).strip() and str(scene).strip().lower() != 'nan':
                upload_data = upload_image_to_google_labs(cookie, str(scene).strip())
                if upload_data:
                    upload_data_list.append({
                        'caption': str(scene_caption).strip() or 'Scene',
                        'mediaCategory': 'MEDIA_CATEGORY_SCENE',
                        'uploadMediaGenerationId': upload_data['uploadMediaGenerationId'],
                        'workflowId': upload_data['workflowId'],
                        'sessionId': upload_data['sessionId']
                    })
            
            if style and str(style).strip() and str(style).strip().lower() != 'nan':
                upload_data = upload_image_to_google_labs(cookie, str(style).strip())
                if upload_data:
                    upload_data_list.append({
                        'caption': str(style_caption).strip() or 'Style',
                        'mediaCategory': 'MEDIA_CATEGORY_STYLE',
                        'uploadMediaGenerationId': upload_data['uploadMediaGenerationId'],
                        'workflowId': upload_data['workflowId'],
                        'sessionId': upload_data['sessionId']
                    })
            
            if upload_data_list:
                result = generate_image_from_multiple_images(access_token, upload_data_list, prompt, seed, "IMAGEN_3_5", aspect_ratio)
                
                if result and 'imagePanels' in result:
                    for panel in result['imagePanels']:
                        if 'generatedImages' in panel:
                            for img in panel['generatedImages']:
                                if 'encodedImage' in img:
                                    filename = sanitize_filename(stt, prompt)
                                    if save_base64_image(img['encodedImage'], filename, output_folder):
                                        return True
                                    else:
                                        return False
            return False
            
        except Exception as e:
            return False

class ImageGenerationThread(QThread):
    """Thread để tạo ảnh"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, cookie, prompt, mode, subject_path, scene_path, style_path, subject_caption, scene_caption, style_caption, seed, count, aspect_ratio):
        super().__init__()
        self.cookie = cookie
        self.prompt = prompt
        self.mode = mode
        self.subject_path = subject_path
        self.scene_path = scene_path
        self.style_path = style_path
        self.subject_caption = subject_caption
        self.scene_caption = scene_caption
        self.style_caption = style_caption
        self.seed = seed
        self.count = count
        self.aspect_ratio = aspect_ratio
    
    def run(self):
        try:
            # Lấy access token
            self.progress.emit("Đang xác thực tài khoản...")
            access_data = get_access_token(self.cookie)
            
            if not access_data or not access_data.get('access_token'):
                self.finished.emit(False, "Không thể xác thực tài khoản")
                return
            
            access_token = access_data.get('access_token')
            self.progress.emit("✅ Xác thực thành công")
            
            # Tạo thư mục output
            output_folder = "generated_images"
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            success_count = 0
            
            for i in range(self.count):
                self.progress.emit(f"Đang tạo ảnh {i+1}/{self.count}...")
                
                if self.mode == "Prompt to Image":
                    # Prompt to Image
                    result = generate_image(access_token, self.prompt, self.seed + i, self.aspect_ratio)
                    
                    if result and 'imagePanels' in result:
                        for panel in result['imagePanels']:
                            if 'generatedImages' in panel:
                                for img in panel['generatedImages']:
                                    if 'encodedImage' in img:
                                        filename = sanitize_filename(i+1, self.prompt)
                                        if save_base64_image(img['encodedImage'], filename, output_folder):
                                            self.progress.emit(f"✅ Đã lưu: {filename}")
                                            success_count += 1
                                        else:
                                            self.progress.emit(f"❌ Lỗi khi lưu: {filename}")
                
                elif self.mode == "Image to Image":
                    # Image to Image với 3 loại ảnh
                    self.progress.emit("Đang upload ảnh...")
                    
                    # Upload các ảnh đã chọn
                    upload_data_list = []
                    
                    if self.subject_path:
                        self.progress.emit("Uploading Subject image...")
                        subject_data = upload_image_to_google_labs(self.cookie, self.subject_path)
                        if subject_data:
                            upload_data_list.append({
                                'caption': self.subject_caption or 'Subject',
                                'mediaCategory': 'MEDIA_CATEGORY_SUBJECT',
                                'uploadMediaGenerationId': subject_data['uploadMediaGenerationId'],
                                'workflowId': subject_data['workflowId'],
                                'sessionId': subject_data['sessionId']
                            })
                    
                    if self.scene_path:
                        self.progress.emit("Uploading Scene image...")
                        scene_data = upload_image_to_google_labs(self.cookie, self.scene_path)
                        if scene_data:
                            upload_data_list.append({
                                'caption': self.scene_caption or 'Scene',
                                'mediaCategory': 'MEDIA_CATEGORY_SCENE',
                                'uploadMediaGenerationId': scene_data['uploadMediaGenerationId'],
                                'workflowId': scene_data['workflowId'],
                                'sessionId': scene_data['sessionId']
                            })
                    
                    if self.style_path:
                        self.progress.emit("Uploading Style image...")
                        style_data = upload_image_to_google_labs(self.cookie, self.style_path)
                        if style_data:
                            upload_data_list.append({
                                'caption': self.style_caption or 'Style',
                                'mediaCategory': 'MEDIA_CATEGORY_STYLE',
                                'uploadMediaGenerationId': style_data['uploadMediaGenerationId'],
                                'workflowId': style_data['workflowId'],
                                'sessionId': style_data['sessionId']
                            })
                    
                    if upload_data_list:
                        self.progress.emit("✅ Upload thành công")
                        result = generate_image_from_multiple_images(access_token, upload_data_list, self.prompt, self.seed + i, "IMAGEN_3_5", self.aspect_ratio)
                        
                        if result and 'imagePanels' in result:
                            for panel in result['imagePanels']:
                                if 'generatedImages' in panel:
                                    for img in panel['generatedImages']:
                                        if 'encodedImage' in img:
                                            filename = sanitize_filename(i+1, self.prompt)
                                            if save_base64_image(img['encodedImage'], filename, output_folder):
                                                self.progress.emit(f"✅ Đã lưu: {filename}")
                                                success_count += 1
                                            else:
                                                self.progress.emit(f"❌ Lỗi khi lưu: {filename}")
                        else:
                            self.progress.emit("❌ Lỗi khi tạo ảnh")
                    else:
                        self.progress.emit("❌ Không có ảnh nào được upload thành công")
            
            if success_count > 0:
                self.finished.emit(True, f"Tạo thành công {success_count} ảnh trong thư mục '{output_folder}'")
            else:
                self.finished.emit(False, "Không tạo được ảnh nào")
                
        except Exception as e:
            self.finished.emit(False, f"Lỗi: {str(e)}")

class MainWindow(QMainWindow):
    """Cửa sổ chính"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Whisk AI Image Generator - @huyit32")
        self.setGeometry(100, 100, 1200, 800)
        
        # Tạo tab widget
        self.tab_widget = QTabWidget()
        
        # Tab quản lý tài khoản
        self.account_tab = AccountManagementTab()
        self.tab_widget.addTab(self.account_tab, "Quản lý Tài khoản")
        
        # Tab tạo ảnh
        self.image_tab = ImageGenerationTab()
        self.tab_widget.addTab(self.image_tab, "Tạo Ảnh")
        
        # Styling tab widget
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2196F3;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)
        
        self.setCentralWidget(self.tab_widget)
        
        # Status bar
        self.statusBar().showMessage("Sẵn sàng")
        
        # Menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        exit_action = file_menu.addAction('Thoát')
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = help_menu.addAction('Giới thiệu')
        about_action.triggered.connect(self.show_about)
    
    def show_about(self):
        """Hiển thị thông tin về ứng dụng"""
        QMessageBox.about(self, "Giới thiệu", 
                         "Whisk Cookie - AI Image Generator\n\n"
                         "Ứng dụng tạo ảnh AI sử dụng Google Labs Whisk\n"
                         "Phiên bản: 1.0\n"
                         "Phát triển bởi: @huyit32")

def main():
    app = QApplication(sys.argv)
    
    # Set font cho toàn bộ ứng dụng
    font = QFont("Open Sans", 9)
    app.setFont(font)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
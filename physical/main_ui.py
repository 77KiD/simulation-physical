"""
PCBA檢測系統主界面
整合所有模組的主要用戶界面
"""

import sys
import os
import cv2
import time
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                            QSlider, QTableWidget, QTableWidgetItem, QGroupBox,
                            QFrame, QScrollArea, QSplitter, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QImage

# 導入自定義模組
from hardware_controller import HardwareController
from detection_engine import DetectionThread, CameraThread
from data_manager import DataManager

# 嘗試導入機械手臂控制界面
try:
    from arm_control_ui import ArmControlWidget
    ARM_UI_AVAILABLE = True
except ImportError:
    print("機械手臂控制界面模組未找到")
    ARM_UI_AVAILABLE = False

# 檢查是否在Jetson環境中運行
JETSON_ENV = os.path.exists('/etc/nv_tegra_release')
if JETSON_ENV:
    print("✅ 檢測到Jetson環境，啟用最佳化設定")
    
    # 嘗試導入Jetson最佳化的影像處理器
    try:
        from jetson_image_processor import JetsonImageProcessor
        JETSON_PROCESSOR_AVAILABLE = True
    except ImportError:
        print("⚠️ Jetson最佳化處理器未找到，使用標準處理器")
        JETSON_PROCESSOR_AVAILABLE = False
else:
    JETSON_PROCESSOR_AVAILABLE = False

class PCBADetectionSystem(QMainWindow):
    """PCBA檢測系統主界面"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化模組
        self.hardware = HardwareController()
        self.data_manager = DataManager()
        
        # 初始化線程
        self.camera_thread = None
        self.detection_thread = None
        
        # 系統狀態
        self.is_running = False
        self.conveyor_running = False
        self.arm_control_window = None  # 機械手臂控制視窗
        
        # 初始化界面
        self.init_ui()
        self.setup_styles()
        self.setup_threads()
        self.update_status_displays()
        
        # 定時更新狀態
        self.status_timer = QTimer()        self.status_timer.start(500)  # 每500ms更新一次
        
    def init_ui(self):
        """初始化用戶界面"""
        title = "PCBA 智能檢測控制系統 v2.0 - 雙視窗AI版本"
        if JETSON_ENV:
            title += " (Jetson Orin Nano)"
        
        self.setWindowTitle(title)
        
        # Jetson環境下使用較小的視窗尺寸
        if JETSON_ENV:
            self.setGeometry(50, 50, 1200, 750)  # 較小尺寸適應Jetson螢幕
        else:
            self.setGeometry(100, 100, 1400, 900)
        
        # 創建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主佈局
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 創建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左側面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右側面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 設置分割器比例
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        
        # Jetson環境下使用較小的尺寸
        if JETSON_ENV:
            splitter.setSizes([720, 480])
        else:
            splitter.setSizes([840, 560])
    
    def create_left_panel(self):
        """創建左側面板（雙視窗相機影像和控制面板）"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # 雙視窗相機影像區域
        camera_group = QGroupBox("📷 即時影像監控")
        camera_layout = QVBoxLayout()
        
        # 影像顯示標籤
        image_label = QLabel("影像顯示控制")
        image_label.setFont(QFont("Microsoft JhengHei", 10, QFont.Bold))
        camera_layout.addWidget(image_label)
        
        # 雙視窗影像顯示區域
        image_container = QHBoxLayout()
        
        # 左側：原始即時影像
        original_group = QGroupBox("🎥 即時影像")
        original_layout = QVBoxLayout()
        
        self.original_image_display = QLabel("即時影像預覽區")
        # Jetson環境下使用較小的顯示區域
        display_height = 250 if JETSON_ENV else 300
        display_width = 300 if JETSON_ENV else 320
        
        self.original_image_display.setMinimumHeight(display_height)
        self.original_image_display.setMinimumWidth(display_width)
        self.original_image_display.setAlignment(Qt.AlignCenter)
        self.original_image_display.setStyleSheet("""
            QLabel {
                border: 2px solid #4CAF50;
                border-radius: 6px;
                background-color: #f8f9fa;
                font-size: 14px;
                font-weight: bold;
                color: #666;
            }
        """)
        original_layout.addWidget(self.original_image_display)
        original_group.setLayout(original_layout)
        
        # 右側：處理後影像 (邊緣檢測 + YOLOv12)
        processed_group = QGroupBox("🤖 AI分析影像")
        processed_layout = QVBoxLayout()
        
        self.processed_image_display = QLabel("AI分析影像\n(邊緣檢測 + YOLOv12推論)")
        self.processed_image_display.setMinimumHeight(display_height)
        self.processed_image_display.setMinimumWidth(display_width)
        self.processed_image_display.setAlignment(Qt.AlignCenter)
        self.processed_image_display.setStyleSheet("""
            QLabel {
                border: 2px solid #2196F3;
                border-radius: 6px;
                background-color: #f0f8ff;
                font-size: 14px;
                font-weight: bold;
                color: #666;
            }
        """)
        processed_layout.addWidget(self.processed_image_display)
        processed_group.setLayout(processed_layout)
        
        image_container.addWidget(original_group)
        image_container.addWidget(processed_group)
        camera_layout.addLayout(image_container)
        
        # 影像處理控制區域
        processing_control_group = QGroupBox("🔧 影像處理控制")
        processing_layout = QGridLayout()
        
        # 邊緣檢測參數
        processing_layout.addWidget(QLabel("邊緣檢測低閾值:"), 0, 0)
        self.canny_low_slider = QSlider(Qt.Horizontal)
        self.canny_low_slider.setRange(10, 100)
        self.canny_low_slider.setValue(50)
        self.canny_low_value = QLabel("50")
        self.canny_low_slider.valueChanged.connect(self.update_canny_low)
        processing_layout.addWidget(self.canny_low_slider, 0, 1)
        processing_layout.addWidget(self.canny_low_value, 0, 2)
        
        processing_layout.addWidget(QLabel("邊緣檢測高閾值:"), 1, 0)
        self.canny_high_slider = QSlider(Qt.Horizontal)
        self.canny_high_slider.setRange(100, 300)
        self.canny_high_slider.setValue(150)
        self.canny_high_value = QLabel("150")
        self.canny_high_slider.valueChanged.connect(self.update_canny_high)
        processing_layout.addWidget(self.canny_high_slider, 1, 1)
        processing_layout.addWidget(self.canny_high_value, 1, 2)
        
        # 對比度增強參數
        processing_layout.addWidget(QLabel("對比度增強:"), 2, 0)
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(50, 300)
        self.contrast_slider.setValue(150)
        self.contrast_value = QLabel("1.5")
        self.contrast_slider.valueChanged.connect(self.update_contrast)
        processing_layout.addWidget(self.contrast_slider, 2, 1)
        processing_layout.addWidget(self.contrast_value, 2, 2)
        
        # YOLO信心閾值
        processing_layout.addWidget(QLabel("YOLO信心閾值:"), 3, 0)
        self.yolo_conf_slider = QSlider(Qt.Horizontal)
        self.yolo_conf_slider.setRange(10, 95)
        self.yolo_conf_slider.setValue(50)
        self.yolo_conf_value = QLabel("0.50")
        self.yolo_conf_slider.valueChanged.connect(self.update_yolo_conf)
        processing_layout.addWidget(self.yolo_conf_slider, 3, 1)
        processing_layout.addWidget(self.yolo_conf_value, 3, 2)
        
        processing_control_group.setLayout(processing_layout)
        camera_layout.addWidget(processing_control_group)
        
        camera_group.setLayout(camera_layout)
        left_layout.addWidget(camera_group)
        
        # 控制面板 (原有控制項)
        control_group = QGroupBox("⚙️ 系統控制面板")
        control_layout = QVBoxLayout()
        
        # 主要控制按鈕
        main_button_layout = QHBoxLayout()
        self.start_btn = QPushButton("📷 開始自動檢測")
        self.start_btn.clicked.connect(self.start_auto_detection)
        self.stop_btn = QPushButton("⛔ 停止")
        self.stop_btn.clicked.connect(self.stop_auto_detection)
        self.stop_btn.setEnabled(False)
        
        main_button_layout.addWidget(self.start_btn)
        main_button_layout.addWidget(self.stop_btn)
        control_layout.addLayout(main_button_layout)
        
        # 檢測門檻值控制
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("PCBA檢測門檻值:"))
        self.threshold_value = QLabel("0.80")
        threshold_layout.addWidget(self.threshold_value)
        
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(80)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        threshold_layout.addWidget(self.threshold_slider)
        control_layout.addLayout(threshold_layout)
        
        # 伺服角度控制 (保留傳統控制，同時支援機械手臂)
        servo_layout = QHBoxLayout()
        if hasattr(self.hardware, 'robotic_arm') and self.hardware.robotic_arm:
            servo_layout.addWidget(QLabel("機械手臂模式:"))
            self.servo_value = QLabel("六軸控制")
            servo_layout.addWidget(self.servo_value)
            
            # 機械手臂控制按鈕
            arm_control_btn = QPushButton("🤖 機械手臂控制")
            arm_control_btn.clicked.connect(self.show_arm_control_window)
            servo_layout.addWidget(arm_control_btn)
        else:
            servo_layout.addWidget(QLabel("SG90 伺服角度:"))
            self.servo_value = QLabel("90°")
            servo_layout.addWidget(self.servo_value)
            
            self.servo_slider = QSlider(Qt.Horizontal)
            self.servo_slider.setRange(0, 180)
            self.servo_slider.setValue(90)
            self.servo_slider.valueChanged.connect(self.update_servo)
            servo_layout.addWidget(self.servo_slider)
        
        control_layout.addLayout(servo_layout)
        
        # 輸送帶速度控制
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("輸送帶速度:"))
        self.speed_value = QLabel("50%")
        speed_layout.addWidget(self.speed_value)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 100)
        self.speed_slider.setValue(50)
        self.speed_slider.valueChanged.connect(self.update_conveyor_speed)
        speed_layout.addWidget(self.speed_slider)
        control_layout.addLayout(speed_layout)
        
        # 系統控制按鈕
        system_layout = QHBoxLayout()
        self.conveyor_btn = QPushButton("▶️ 啟動輸送帶")
        self.conveyor_btn.clicked.connect(self.toggle_conveyor)
        self.reset_btn = QPushButton("🔄 重設系統")
        self.reset_btn.clicked.connect(self.reset_system)
        
        system_layout.addWidget(self.conveyor_btn)
        system_layout.addWidget(self.reset_btn)
        control_layout.addLayout(system_layout)
        
        # 繼電器控制
        relay_layout = QHBoxLayout()
        self.relay_btn = QPushButton("🔌 繼電器開關")
        self.relay_btn.clicked.connect(self.toggle_relay)
        self.relay_status = QLabel("繼電器狀態：🔴 關閉")
        relay_layout.addWidget(self.relay_btn)
        relay_layout.addWidget(self.relay_status)
        control_layout.addLayout(relay_layout)
        
        control_group.setLayout(control_layout)
        left_layout.addWidget(control_group)
        
        return left_widget
        
    def create_right_panel(self):
        """創建右側面板（狀態監控和檢測記錄）"""
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        # 創建垂直分割器
        right_splitter = QSplitter(Qt.Vertical)
        right_layout.addWidget(right_splitter)
        
        # 狀態監控區域
        status_widget = self.create_status_widget()
        right_splitter.addWidget(status_widget)
        
        # 檢測記錄區域
        log_widget = self.create_log_widget()
        right_splitter.addWidget(log_widget)
        
        # 設置分割器比例
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 1)
        right_splitter.setSizes([400, 400])
        
        return right_widget
        
    def create_status_widget(self):
        """創建狀態監控組件"""
        status_group = QGroupBox("📊 狀態監控")
        status_layout = QVBoxLayout()
        
        # 系統狀態顯示
        self.system_status = QLabel("系統狀態：🔴 停止")
        self.conveyor_status = QLabel("輸送帶狀態：🔴 停止")
        self.servo_status = QLabel("伺服控制：🟢 就緒 (90°)")        self.camera_status = QLabel("相機狀態：🟢 正常")
        
        status_layout.addWidget(self.system_status)
        status_layout.addWidget(self.conveyor_status)
        status_layout.addWidget(self.servo_status)        status_layout.addWidget(self.camera_status)
        
        # 生產統計
        stats_label = QLabel("生產統計")
        stats_label.setFont(QFont("Microsoft JhengHei", 10, QFont.Bold))
        status_layout.addWidget(stats_label)
        
        stats_widget = QWidget()
        stats_layout = QGridLayout()
        
        self.total_label = QLabel("總檢測數：0")
        self.pass_label = QLabel("合格數：0")
        self.defect_label = QLabel("缺陷數：0")
        self.pass_rate_label = QLabel("合格率：0.0%")
        
        stats_layout.addWidget(self.total_label, 0, 0)
        stats_layout.addWidget(self.pass_label, 0, 1)
        stats_layout.addWidget(self.defect_label, 1, 0)
        stats_layout.addWidget(self.pass_rate_label, 1, 1)
        
        stats_widget.setLayout(stats_layout)
        status_layout.addWidget(stats_widget)
        
        # 缺陷分析
        defect_label = QLabel("缺陷分析")
        defect_label.setFont(QFont("Microsoft JhengHei", 10, QFont.Bold))
        status_layout.addWidget(defect_label)
        
        defect_widget = QWidget()
        defect_layout = QGridLayout()
        
        self.short_label = QLabel("短路: 0")
        self.open_label = QLabel("斷路: 0")
        self.bridge_label = QLabel("橋接: 0")
        self.missing_label = QLabel("缺件: 0")
        
        defect_layout.addWidget(self.short_label, 0, 0)
        defect_layout.addWidget(self.open_label, 0, 1)
        defect_layout.addWidget(self.bridge_label, 1, 0)
        defect_layout.addWidget(self.missing_label, 1, 1)
        
        defect_widget.setLayout(defect_layout)
        status_layout.addWidget(defect_widget)
        
        # 快速操作按鈕
        quick_label = QLabel("快速操作")
        quick_label.setFont(QFont("Microsoft JhengHei", 10, QFont.Bold))
        status_layout.addWidget(quick_label)
        
        quick_layout1 = QHBoxLayout()
        export_txt_btn = QPushButton("📄 匯出TXT報告")
        export_txt_btn.clicked.connect(self.export_txt_report)
        export_csv_btn = QPushButton("📊 匯出CSV數據")
        export_csv_btn.clicked.connect(self.export_csv_data)
        
        quick_layout1.addWidget(export_txt_btn)
        quick_layout1.addWidget(export_csv_btn)
        status_layout.addLayout(quick_layout1)
        
        quick_layout2 = QHBoxLayout()
        clear_btn = QPushButton("🗑️ 清除記錄")
        clear_btn.clicked.connect(self.clear_records)
        refresh_btn = QPushButton("🔄 刷新狀態")
        refresh_btn.clicked.connect(self.update_status_displays)
        
        quick_layout2.addWidget(clear_btn)
        quick_layout2.addWidget(refresh_btn)
        status_layout.addLayout(quick_layout2)
        
        status_layout.addStretch()
        status_group.setLayout(status_layout)
        return status_group
        
    def create_log_widget(self):
        """創建檢測記錄組件"""
        log_group = QGroupBox("🧾 檢測記錄")
        log_layout = QVBoxLayout()
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(["時間", "結果", "缺陷", "信心度", "動作"])
        
        # 設置表格屬性
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.log_table.resizeColumnsToContents()
        self.log_table.horizontalHeader().setStretchLastSection(True)
        
        # 設置列寬
        self.log_table.setColumnWidth(0, 140)  # 時間
        self.log_table.setColumnWidth(1, 60)   # 結果
        self.log_table.setColumnWidth(2, 60)   # 缺陷
        self.log_table.setColumnWidth(3, 70)   # 信心度
        
        log_layout.addWidget(self.log_table)
        log_group.setLayout(log_layout)
        return log_group
        
    def setup_styles(self):
        """設置樣式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #333;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLabel {
                color: #333;
                font-size: 12px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 10px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        
    def setup_threads(self):
        """設置工作線程"""
        # 相機線程
        self.camera_thread = CameraThread(self.hardware)
        self.camera_thread.frame_ready.connect(self.update_camera_display)
        
        # 檢測線程
        self.detection_thread = DetectionThread(self.hardware, self)
        self.detection_thread.detection_result.connect(self.handle_detection_result)    @pyqtSlot(np.ndarray)
    def update_camera_display(self, frame):
        """更新原始相機顯示"""
        try:
            # 轉換OpenCV格式到Qt格式
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # 縮放圖像以適應顯示區域
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(self.original_image_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.original_image_display.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"原始相機顯示更新錯誤: {e}")
    
    @pyqtSlot(str, str, float)
    def handle_detection_result(self, result, defect_type, confidence):
        """處理檢測結果"""
        # 添加記錄到數據管理器
        record = self.data_manager.add_record(result, defect_type, confidence)
        
        # 更新表格顯示
        self.add_log_entry_to_table(record)
        
        # 更新統計顯示
        self.update_statistics_display()
        
        print(f"檢測結果: {result}, 缺陷: {defect_type}, 信心度: {confidence:.2f}")
    
    # 影像處理參數更新方法
    def update_canny_low(self):
        """更新Canny低閾值"""
        value = self.canny_low_slider.value()
        self.canny_low_value.setText(str(value))
    
    def update_canny_high(self):
        """更新Canny高閾值"""
        value = self.canny_high_slider.value()
        self.canny_high_value.setText(str(value))
    
    def update_contrast(self):
        """更新對比度增強"""
        value = self.contrast_slider.value() / 100.0
        self.contrast_value.setText(f"{value:.1f}")
    
    def update_yolo_conf(self):
        """更新YOLO信心閾值"""
        value = self.yolo_conf_slider.value() / 100.0
        self.yolo_conf_value.setText(f"{value:.2f}")
    def add_log_entry_to_table(self, record):
        """添加記錄到表格"""
        row_count = self.log_table.rowCount()
        self.log_table.insertRow(row_count)
        
        self.log_table.setItem(row_count, 0, QTableWidgetItem(record.timestamp))
        self.log_table.setItem(row_count, 1, QTableWidgetItem(record.result))
        self.log_table.setItem(row_count, 2, QTableWidgetItem(record.defect_type or "-"))
        self.log_table.setItem(row_count, 3, QTableWidgetItem(f"{record.confidence:.2f}"))
        self.log_table.setItem(row_count, 4, QTableWidgetItem(record.action))
        
        # 自動滾動到最新記錄
        self.log_table.scrollToBottom()
        
        # 限制顯示記錄數量（保持最新200條）
        if self.log_table.rowCount() > 200:
            self.log_table.removeRow(0)
    
    def start_auto_detection(self):
        """開始自動檢測"""
        self.is_running = True
        self.system_status.setText("系統狀態：🟢 執行中")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # 啟動相機線程
        if not self.camera_thread.isRunning():
            self.camera_thread.start()
        
        # 啟動檢測線程
        if not self.detection_thread.isRunning():
            self.detection_thread.start()
        
        print("自動檢測已啟動")
        
    def stop_auto_detection(self):
        """停止自動檢測"""
        self.is_running = False
        self.system_status.setText("系統狀態：🔴 停止")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # 停止檢測線程
        if self.detection_thread.isRunning():
            self.detection_thread.stop()
        
        print("自動檢測已停止")
        
    def reset_system(self):
        """重設系統"""
        self.stop_auto_detection()
        
        # 重設輸送帶
        self.conveyor_running = False
        self.conveyor_status.setText("輸送帶狀態：🔴 停止")
        self.conveyor_btn.setText("▶️ 啟動輸送帶")
        
        # 重設硬體到初始狀態
        self.hardware.stop_conveyor()
        self.hardware.set_servo_angle(90)
        self.hardware.control_relay(False)
        
        # 重設UI控制項
        if hasattr(self, 'servo_slider'):
            self.servo_slider.setValue(90)
            self.update_servo()
        
        self.speed_slider.setValue(50)
        self.threshold_slider.setValue(80)
        
        self.update_conveyor_speed()
        self.update_threshold()
        
        self.update_status_displays()
        
        print("系統已重設")
        
    def toggle_conveyor(self):
        """切換輸送帶狀態"""
        if not self.conveyor_running:
            self.conveyor_running = True
            self.conveyor_status.setText("輸送帶狀態：🟢 執行中")
            self.conveyor_btn.setText("⏸️ 停止輸送帶")
            
            # 啟動輸送帶
            speed = self.speed_slider.value()
            self.hardware.set_conveyor_speed(speed, 'forward')
        else:
            self.conveyor_running = False
            self.conveyor_status.setText("輸送帶狀態：🔴 停止")
            self.conveyor_btn.setText("▶️ 啟動輸送帶")
            
            # 停止輸送帶
            self.hardware.stop_conveyor()
            
    def toggle_relay(self):
        """切換繼電器狀態"""
        current_state = self.hardware.get_relay_state()
        new_state = not current_state
        
        if self.hardware.control_relay(new_state):
            if new_state:
                self.relay_status.setText("繼電器狀態：🟢 開啟")
            else:
                self.relay_status.setText("繼電器狀態：🔴 關閉")
        
    def update_threshold(self):
        """更新檢測門檻值"""
        value = self.threshold_slider.value() / 100.0
        self.threshold_value.setText(f"{value:.2f}")
        
        # 更新檢測線程的門檻值
        if self.detection_thread:
            self.detection_thread.set_threshold(value)
        
    def update_servo(self):
        """更新伺服角度 (傳統SG90模式)"""
        if hasattr(self, 'servo_slider'):
            angle = self.servo_slider.value()
            self.servo_value.setText(f"{angle}°")
            self.servo_status.setText(f"伺服控制：🟢 就緒 ({angle}°)")
            
            # 控制實際硬體
            self.hardware.set_servo_angle(angle)
    
    def show_arm_control_window(self):
        """顯示機械手臂控制視窗"""
        if not ARM_UI_AVAILABLE:
            QMessageBox.warning(self, "功能不可用", "機械手臂控制界面模組未找到")
            return
            
        if self.arm_control_window is None:
            self.arm_control_window = ArmControlWidget()
            self.arm_control_window.setWindowTitle("六軸機械手臂控制系統")
            self.arm_control_window.setGeometry(200, 200, 900, 700)
            
            # 連接信號
            self.arm_control_window.action_completed.connect(self.on_arm_action_completed)
        
        self.arm_control_window.show()
        self.arm_control_window.raise_()
        self.arm_control_window.activateWindow()
    
    @pyqtSlot(str, bool)
    def on_arm_action_completed(self, target, success):
        """機械手臂動作完成回調"""
        target_name = "合格品" if target == 'pass' else "缺陷品"
        if success:
            self.add_log_entry_to_table({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'result': f"機械手臂分揀",
                'defect_type': target_name,
                'confidence': 1.0,
                'action': f"🤖 {target_name}分揀完成"
            })
        else:
            print(f"機械手臂分揀失敗: {target_name}")
        
    def update_conveyor_speed(self):
        """更新輸送帶速度"""
        speed = self.speed_slider.value()
        self.speed_value.setText(f"{speed}%")
        
        # 如果輸送帶正在運行，更新速度
        if self.conveyor_running:
            self.hardware.set_conveyor_speed(speed, 'forward')
    def update_status_displays(self):
        """更新所有狀態顯示"""
        # 更新硬體狀態
        hardware_status = self.hardware.get_hardware_status()
        
        if hardware_status['camera_available']:
            self.camera_status.setText("相機狀態：🟢 正常")
        else:
            self.camera_status.setText("相機狀態：🔴 離線")
        
        # 更新分揀系統狀態
        if hasattr(self.hardware, 'robotic_arm') and self.hardware.robotic_arm:
            arm_status = self.hardware.get_arm_status()
            if arm_status.get('hardware_available', False):
                self.servo_status.setText("分揀系統：🤖 六軸機械手臂就緒")
            else:
                self.servo_status.setText("分揀系統：🤖 六軸機械手臂(模擬模式)")
        else:
            if hasattr(self, 'servo_slider'):
                angle = self.servo_slider.value()
            else:
                angle = 90
            self.servo_status.setText(f"分揀系統：🟢 SG90伺服 ({angle}°)")
        
        # 更新繼電器狀態顯示
        if hardware_status['relay_state']:
            self.relay_status.setText("繼電器狀態：🟢 開啟")
        else:
            self.relay_status.setText("繼電器狀態：🔴 關閉")
        
        # 更新統計顯示
        self.update_statistics_display()
        
        # 更新記錄表格
        self.refresh_log_table()
    
    def update_statistics_display(self):
        """更新統計數據顯示"""
        stats = self.data_manager.get_statistics()
        defect_dist = stats.get_defect_distribution()
        
        self.total_label.setText(f"總檢測數：{stats.total_count}")
        self.pass_label.setText(f"合格數：{stats.pass_count}")
        self.defect_label.setText(f"缺陷數：{stats.defect_count}")
        self.pass_rate_label.setText(f"合格率：{stats.get_pass_rate():.1f}%")
        
        self.short_label.setText(f"短路: {defect_dist['短路']}")
        self.open_label.setText(f"斷路: {defect_dist['斷路']}")
        self.bridge_label.setText(f"橋接: {defect_dist['橋接']}")
        self.missing_label.setText(f"缺件: {defect_dist['缺件']}")
    
    def refresh_log_table(self):
        """刷新記錄表格"""
        self.log_table.setRowCount(0)
        records = self.data_manager.get_recent_records(200)
        
        for record in records:
            self.add_log_entry_to_table(record)
    
    def export_txt_report(self):
        """匯出TXT報告"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "匯出TXT報告", 
                f"PCBA_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "文字檔案 (*.txt)"
            )
            
            if file_path:
                saved_path = self.data_manager.export_report(file_path)
                if saved_path:
                    QMessageBox.information(self, "匯出成功", f"報告已匯出至：{saved_path}")
                else:
                    QMessageBox.warning(self, "匯出失敗", "匯出報告時發生錯誤")
                    
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"匯出報告時發生錯誤：{str(e)}")
    
    def export_csv_data(self):
        """匯出CSV數據"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "匯出CSV數據", 
                f"PCBA_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV檔案 (*.csv)"
            )
            
            if file_path:
                saved_path = self.data_manager.export_csv(file_path)
                if saved_path:
                    QMessageBox.information(self, "匯出成功", f"數據已匯出至：{saved_path}")
                else:
                    QMessageBox.warning(self, "匯出失敗", "匯出數據時發生錯誤")
                    
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"匯出數據時發生錯誤：{str(e)}")
        
    def clear_records(self):
        """清除記錄"""
        reply = QMessageBox.question(self, "清除記錄", "確定要清除所有記錄嗎？",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.data_manager.clear_records()
            self.log_table.setRowCount(0)
            self.update_statistics_display()
            QMessageBox.information(self, "清除完成", "所有記錄已清除")
    
    def closeEvent(self, event):
        """程序關閉事件"""
        # 停止檢測
        if self.is_running:
            self.stop_auto_detection()
        
        # 關閉機械手臂控制視窗
        if self.arm_control_window:
            self.arm_control_window.close()
        
        # 停止所有線程
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
        
        if self.detection_thread and self.detection_thread.isRunning():
            self.detection_thread.stop()
        
        # 停止定時器
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # 清理硬體資源
        self.hardware.cleanup()
        
        event.accept()

def main():
    """主程序入口"""
    app = QApplication(sys.argv)
    
    # 設置應用程式樣式
    app.setStyle('Fusion')
    
    # 設置字體
    font = QFont("Microsoft JhengHei", 9)
    app.setFont(font)
    
    # 檢查硬體環境
    try:
        from hardware_controller import GPIO_AVAILABLE
        if not GPIO_AVAILABLE:
            print("⚠️  警告：GPIO模組未安裝，程序將以模擬模式運行")
            print("若要使用實際硬體，請安裝以下模組：")
            print("- Jetson.GPIO")
            print("- adafruit-circuitpython-pca9685")
            print("- adafruit-circuitpython-motor")
    except ImportError:
        print("⚠️  無法導入硬體控制模組")
    
    # 創建並顯示主窗口
    try:
        window = PCBADetectionSystem()
        window.show()
        
        print("🚀 PCBA檢測系統已啟動")
        print("📋 系統功能：")
        print("   - 即時影像檢測")
        print("   - 自動分類控制")
        print("   - 數據記錄與分析")
        print("   - 報告匯出")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ 程序啟動失敗: {e}")
        QMessageBox.critical(None, "啟動錯誤", f"程序啟動失敗：{str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
        
"""
機械手臂控制界面
提供六軸機械手臂的圖形化控制界面
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                            QPushButton, QLabel, QSlider, QGroupBox, QTextEdit,
                            QComboBox, QSpinBox, QProgressBar, QTabWidget,
                            QMessageBox, QInputDialog, QListWidget, QSplitter)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont

try:
    from robotic_arm_controller import RoboticArmController, Position
    ARM_CONTROLLER_AVAILABLE = True
except ImportError:
    print("機械手臂控制模組未找到")
    ARM_CONTROLLER_AVAILABLE = False

class ArmControlWidget(QWidget):
    """機械手臂控制界面組件"""
    
    # 信號定義
    position_changed = pyqtSignal(str)  # 位置變更信號
    action_completed = pyqtSignal(str, bool)  # 動作完成信號
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化機械手臂控制器
        if ARM_CONTROLLER_AVAILABLE:
            self.arm_controller = RoboticArmController()
        else:
            self.arm_controller = None
        
        self.init_ui()
        self.setup_connections()
        self.start_status_update_timer()
        
    def init_ui(self):
        """初始化用戶界面"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 創建標籤頁
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 手動控制標籤頁
        manual_tab = self.create_manual_control_tab()
        tab_widget.addTab(manual_tab, "🎮 手動控制")
        
        # 預設位置標籤頁
        preset_tab = self.create_preset_position_tab()
        tab_widget.addTab(preset_tab, "📍 預設位置")
        
        # 自動序列標籤頁
        sequence_tab = self.create_sequence_control_tab()
        tab_widget.addTab(sequence_tab, "🤖 自動序列")
        
        # 狀態監控標籤頁
        status_tab = self.create_status_monitor_tab()
        tab_widget.addTab(status_tab, "📊 狀態監控")
        
    def create_manual_control_tab(self):
        """創建手動控制標籤頁"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # 關節控制組
        joint_group = QGroupBox("🔧 關節控制")
        joint_layout = QGridLayout()
        
        self.joint_sliders = {}
        self.joint_labels = {}
        
        # 六軸關節控制
        joint_configs = [
            ("joint1", "基座旋轉", -180, 180, 0),
            ("joint2", "肩部俯仰", -90, 90, 0),
            ("joint3", "手肘彎曲", -120, 120, -90),
            ("joint4", "腕部俯仰", -90, 90, 0),
            ("joint5", "腕部旋轉", -180, 180, 0),
            ("joint6", "末端夾爪", -45, 45, 0)
        ]
        
        for i, (joint_id, joint_name, min_val, max_val, default_val) in enumerate(joint_configs):
            # 關節名稱標籤
            name_label = QLabel(joint_name)
            name_label.setFont(QFont("Microsoft JhengHei", 9, QFont.Bold))
            joint_layout.addWidget(name_label, i, 0)
            
            # 角度顯示標籤
            angle_label = QLabel(f"{default_val}°")
            angle_label.setMinimumWidth(50)
            joint_layout.addWidget(angle_label, i, 1)
            self.joint_labels[joint_id] = angle_label
            
            # 角度滑桿
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(default_val)
            slider.valueChanged.connect(lambda v, jid=joint_id: self.on_joint_slider_changed(jid, v))
            joint_layout.addWidget(slider, i, 2)
            self.joint_sliders[joint_id] = slider
            
            # 快速控制按鈕
            btn_layout = QHBoxLayout()
            min_btn = QPushButton("Min")
            min_btn.setMaximumWidth(40)
            min_btn.clicked.connect(lambda _, jid=joint_id, val=min_val: self.set_joint_angle(jid, val))
            
            home_btn = QPushButton("Home")
            home_btn.setMaximumWidth(50)
            home_btn.clicked.connect(lambda _, jid=joint_id, val=default_val: self.set_joint_angle(jid, val))
            
            max_btn = QPushButton("Max")
            max_btn.setMaximumWidth(40)
            max_btn.clicked.connect(lambda _, jid=joint_id, val=max_val: self.set_joint_angle(jid, val))
            
            btn_layout.addWidget(min_btn)
            btn_layout.addWidget(home_btn)
            btn_layout.addWidget(max_btn)
            joint_layout.addLayout(btn_layout, i, 3)
        
        joint_group.setLayout(joint_layout)
        layout.addWidget(joint_group)
        
        # 速度控制
        speed_group = QGroupBox("⚡ 運動控制")
        speed_layout = QHBoxLayout()
        
        speed_layout.addWidget(QLabel("運動時間:"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 10)
        self.duration_spin.setValue(2)
        self.duration_spin.setSuffix(" 秒")
        speed_layout.addWidget(self.duration_spin)
        
        speed_layout.addStretch()
        
        # 執行按鈕
        execute_btn = QPushButton("🎯 執行移動")
        execute_btn.clicked.connect(self.execute_manual_move)
        speed_layout.addWidget(execute_btn)
        
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)
        
        return widget
        
    def create_preset_position_tab(self):
        """創建預設位置標籤頁"""
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        
        # 左側：位置列表
        left_group = QGroupBox("📋 預設位置")
        left_layout = QVBoxLayout()
        
        self.position_list = QListWidget()
        self.update_position_list()
        left_layout.addWidget(self.position_list)
        
        # 位置控制按鈕
        pos_btn_layout = QHBoxLayout()
        
        go_to_btn = QPushButton("🎯 移動到選定位置")
        go_to_btn.clicked.connect(self.move_to_selected_position)
        pos_btn_layout.addWidget(go_to_btn)
        
        save_btn = QPushButton("💾 儲存當前位置")
        save_btn.clicked.connect(self.save_current_position)
        pos_btn_layout.addWidget(save_btn)
        
        left_layout.addLayout(pos_btn_layout)
        left_group.setLayout(left_layout)
        layout.addWidget(left_group)
        
        # 右側：位置詳細資訊
        right_group = QGroupBox("📊 位置資訊")
        right_layout = QVBoxLayout()
        
        self.position_info_text = QTextEdit()
        self.position_info_text.setMaximumHeight(150)
        self.position_info_text.setReadOnly(True)
        right_layout.addWidget(self.position_info_text)
        
        # 檔案操作
        file_btn_layout = QHBoxLayout()
        
        load_btn = QPushButton("📂 載入位置檔案")
        load_btn.clicked.connect(self.load_positions_from_file)
        file_btn_layout.addWidget(load_btn)
        
        save_file_btn = QPushButton("💾 儲存位置檔案")
        save_file_btn.clicked.connect(self.save_positions_to_file)
        file_btn_layout.addWidget(save_file_btn)
        
        right_layout.addLayout(file_btn_layout)
        right_group.setLayout(right_layout)
        layout.addWidget(right_group)
        
        return widget
        
    def create_sequence_control_tab(self):
        """創建自動序列標籤頁"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # 分揀序列控制
        sorting_group = QGroupBox("🤖 自動分揀序列")
        sorting_layout = QGridLayout()
        
        # 合格品分揀
        pass_btn = QPushButton("✅ 執行合格品分揀")
        pass_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        pass_btn.clicked.connect(lambda: self.execute_sorting_sequence('pass'))
        sorting_layout.addWidget(pass_btn, 0, 0)
        
        # 缺陷品分揀
        fail_btn = QPushButton("❌ 執行缺陷品分揀")
        fail_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 10px;")
        fail_btn.clicked.connect(lambda: self.execute_sorting_sequence('fail'))
        sorting_layout.addWidget(fail_btn, 0, 1)
        
        # 回到原點
        home_btn = QPushButton("🏠 回到原點位置")
        home_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        home_btn.clicked.connect(self.move_to_home)
        sorting_layout.addWidget(home_btn, 1, 0)
        
        # 緊急停止
        stop_btn = QPushButton("🚨 緊急停止")
        stop_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 10px;")
        stop_btn.clicked.connect(self.emergency_stop)
        sorting_layout.addWidget(stop_btn, 1, 1)
        
        sorting_group.setLayout(sorting_layout)
        layout.addWidget(sorting_group)
        
        # 校正控制
        calibration_group = QGroupBox("🔧 校正功能")
        calib_layout = QHBoxLayout()
        
        calib_layout.addWidget(QLabel("選擇關節:"))
        self.calib_joint_combo = QComboBox()
        self.calib_joint_combo.addItems([
            "joint1 (基座)", "joint2 (肩部)", "joint3 (手肘)", 
            "joint4 (腕部俯仰)", "joint5 (腕部旋轉)", "joint6 (夾爪)"
        ])
        calib_layout.addWidget(self.calib_joint_combo)
        
        calib_btn = QPushButton("🔧 校正關節")
        calib_btn.clicked.connect(self.calibrate_selected_joint)
        calib_layout.addWidget(calib_btn)
        
        calib_all_btn = QPushButton("🔧 校正所有關節")
        calib_all_btn.clicked.connect(self.calibrate_all_joints)
        calib_layout.addWidget(calib_all_btn)
        
        calibration_group.setLayout(calib_layout)
        layout.addWidget(calibration_group)
        
        # 序列執行狀態
        self.sequence_progress = QProgressBar()
        self.sequence_progress.setVisible(False)
        layout.addWidget(self.sequence_progress)
        
        layout.addStretch()
        
        return widget
        
    def create_status_monitor_tab(self):
        """創建狀態監控標籤頁"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # 系統狀態顯示
        status_group = QGroupBox("📊 系統狀態")
        status_layout = QGridLayout()
        
        self.arm_status_label = QLabel("機械手臂：🟢 就緒")
        status_layout.addWidget(self.arm_status_label, 0, 0)
        
        self.hardware_status_label = QLabel("硬體狀態：🟢 正常")
        status_layout.addWidget(self.hardware_status_label, 0, 1)
        
        self.movement_status_label = QLabel("運動狀態：⏸️ 停止")
        status_layout.addWidget(self.movement_status_label, 1, 0)
        
        self.position_status_label = QLabel("當前位置：原點")
        status_layout.addWidget(self.position_status_label, 1, 1)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 關節狀態詳細資訊
        joint_status_group = QGroupBox("🔧 關節狀態")
        joint_status_layout = QVBoxLayout()
        
        self.joint_status_text = QTextEdit()
        self.joint_status_text.setMaximumHeight(200)
        self.joint_status_text.setReadOnly(True)
        joint_status_layout.addWidget(self.joint_status_text)
        
        # 刷新按鈕
        refresh_btn = QPushButton("🔄 刷新狀態")
        refresh_btn.clicked.connect(self.update_status_display)
        joint_status_layout.addWidget(refresh_btn)
        
        joint_status_group.setLayout(joint_status_layout)
        layout.addWidget(joint_status_group)
        
        # 日誌區域
        log_group = QGroupBox("📝 操作日誌")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("🗑️ 清除日誌")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        return widget
        
    def setup_connections(self):
        """設置信號連接"""
        # 位置列表選擇變更
        self.position_list.currentItemChanged.connect(self.on_position_selection_changed)
        
    def start_status_update_timer(self):
        """啟動狀態更新定時器"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_display)
        self.status_timer.start(1000)  # 每秒更新一次
        
    def on_joint_slider_changed(self, joint_id, value):
        """關節滑桿值變更處理"""
        self.joint_labels[joint_id].setText(f"{value}°")
        
    def set_joint_angle(self, joint_id, angle):
        """設置關節角度"""
        self.joint_sliders[joint_id].setValue(angle)
        
    def execute_manual_move(self):
        """執行手動移動"""
        if not self.arm_controller:
            self.add_log("❌ 機械手臂控制器不可用")
            return
            
        # 獲取所有關節角度
        angles = []
        for joint_id in ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']:
            angles.append(self.joint_sliders[joint_id].value())
        
        # 創建目標位置
        target_position = Position.from_list(angles)
        duration = self.duration_spin.value()
        
        # 執行移動
        success = self.arm_controller.move_to_position(target_position, duration)
        
        if success:
            self.add_log(f"✅ 手動移動完成: {angles}")
        else:
            self.add_log(f"❌ 手動移動失敗")
            
    def update_position_list(self):
        """更新預設位置列表"""
        self.position_list.clear()
        
        if self.arm_controller:
            positions = self.arm_controller.predefined_positions
            for name in positions.keys():
                self.position_list.addItem(name)
                
    def move_to_selected_position(self):
        """移動到選定的預設位置"""
        current_item = self.position_list.currentItem()
        if not current_item:
            self.add_log("⚠️ 請先選擇一個位置")
            return
            
        position_name = current_item.text()
        
        if self.arm_controller:
            success = self.arm_controller.move_to_predefined(position_name)
            if success:
                self.add_log(f"✅ 移動到位置: {position_name}")
            else:
                self.add_log(f"❌ 移動失敗: {position_name}")
                
    def save_current_position(self):
        """儲存當前位置"""
        name, ok = QInputDialog.getText(self, '儲存位置', '請輸入位置名稱:')
        
        if ok and name.strip():
            if self.arm_controller:
                self.arm_controller.save_position(name.strip())
                self.update_position_list()
                self.add_log(f"💾 位置已儲存: {name.strip()}")
            else:
                self.add_log("❌ 機械手臂控制器不可用")
                
    def execute_sorting_sequence(self, target):
        """執行分揀序列"""
        if not self.arm_controller:
            self.add_log("❌ 機械手臂控制器不可用")
            return
            
        target_name = "合格品" if target == 'pass' else "缺陷品"
        self.add_log(f"🤖 開始執行{target_name}分揀序列...")
        
        # 顯示進度條
        self.sequence_progress.setVisible(True)
        self.sequence_progress.setRange(0, 0)  # 不確定進度
        
        # 執行序列
        success = self.arm_controller.execute_pick_and_place_sequence(target)
        
        # 隱藏進度條
        self.sequence_progress.setVisible(False)
        
        if success:
            self.add_log(f"✅ {target_name}分揀序列完成")
            self.action_completed.emit(target, True)
        else:
            self.add_log(f"❌ {target_name}分揀序列失敗")
            self.action_completed.emit(target, False)
            
    def move_to_home(self):
        """移動到原點"""
        if self.arm_controller:
            success = self.arm_controller.move_to_home()
            if success:
                self.add_log("✅ 已移動到原點位置")
            else:
                self.add_log("❌ 移動到原點失敗")
        else:
            self.add_log("❌ 機械手臂控制器不可用")
            
    def emergency_stop(self):
        """緊急停止"""
        if self.arm_controller:
            self.arm_controller.emergency_stop()
            self.add_log("🚨 緊急停止已執行")
        else:
            self.add_log("❌ 機械手臂控制器不可用")
            
    def calibrate_selected_joint(self):
        """校正選定的關節"""
        joint_index = self.calib_joint_combo.currentIndex()
        joint_names = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
        
        if joint_index >= 0 and joint_index < len(joint_names):
            joint_name = joint_names[joint_index]
            
            if self.arm_controller:
                success = self.arm_controller.calibrate_joint(joint_name)
                if success:
                    self.add_log(f"✅ 關節 {joint_name} 校正完成")
                else:
                    self.add_log(f"❌ 關節 {joint_name} 校正失敗")
            else:
                self.add_log("❌ 機械手臂控制器不可用")
                
    def calibrate_all_joints(self):
        """校正所有關節"""
        if not self.arm_controller:
            self.add_log("❌ 機械手臂控制器不可用")
            return
            
        self.add_log("🔧 開始校正所有關節...")
        
        joint_names = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
        success_count = 0
        
        for joint_name in joint_names:
            if self.arm_controller.calibrate_joint(joint_name):
                success_count += 1
                
        self.add_log(f"✅ 校正完成，成功: {success_count}/{len(joint_names)}")
        
    def load_positions_from_file(self):
        """從檔案載入位置"""
        if self.arm_controller:
            self.arm_controller.load_positions_from_file()
            self.update_position_list()
            self.add_log("📂 位置檔案載入完成")
        else:
            self.add_log("❌ 機械手臂控制器不可用")
            
    def save_positions_to_file(self):
        """儲存位置到檔案"""
        if self.arm_controller:
            self.arm_controller.save_positions_to_file()
            self.add_log("💾 位置檔案儲存完成")
        else:
            self.add_log("❌ 機械手臂控制器不可用")
            
    def on_position_selection_changed(self, current, previous):
        """位置選擇變更處理"""
        if current and self.arm_controller:
            position_name = current.text()
            if position_name in self.arm_controller.predefined_positions:
                position = self.arm_controller.predefined_positions[position_name]
                info_text = f"位置: {position_name}\n"
                info_text += f"關節角度: {position.to_list()}\n"
                info_text += "各關節詳細:\n"
                
                joint_names = ["基座", "肩部", "手肘", "腕部俯仰", "腕部旋轉", "夾爪"]
                angles = position.to_list()
                
                for i, (name, angle) in enumerate(zip(joint_names, angles)):
                    info_text += f"  {name}: {angle:.1f}°\n"
                
                self.position_info_text.setPlainText(info_text)
                
    def update_status_display(self):
        """更新狀態顯示"""
        if not self.arm_controller:
            self.arm_status_label.setText("機械手臂：🔴 不可用")
            self.hardware_status_label.setText("硬體狀態：🔴 離線")
            self.movement_status_label.setText("運動狀態：🔴 無法控制")
            return
            
        # 獲取狀態
        status = self.arm_controller.get_status()
        
        # 更新狀態標籤
        if status['hardware_available']:
            self.arm_status_label.setText("機械手臂：🟢 就緒")
            self.hardware_status_label.setText("硬體狀態：🟢 正常")
        else:
            self.arm_status_label.setText("機械手臂：🟡 模擬模式")
            self.hardware_status_label.setText("硬體狀態：🟡 模擬")
            
        if status['is_moving']:
            self.movement_status_label.setText("運動狀態：🟡 移動中")
        else:
            self.movement_status_label.setText("運動狀態：🟢 停止")
            
        # 更新關節狀態
        joint_info = self.arm_controller.get_joint_info()
        joint_text = ""
        
        for joint_id, info in joint_info.items():
            joint_text += f"{info['name']}: {info['current_angle']:.1f}° "
            joint_text += f"[{info['min_angle']}° ~ {info['max_angle']}°] "
            joint_text += f"(Ch{info['channel']})\n"
            
        self.joint_status_text.setPlainText(joint_text)
        
    def add_log(self, message):
        """添加日誌"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def clear_log(self):
        """清除日誌"""
        self.log_text.clear()
        
    def closeEvent(self, event):
        """關閉事件"""
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
            
        if self.arm_controller:
            self.arm_controller.cleanup()
            
        event.accept()


# 獨立視窗測試
def main():
    """主函數 - 獨立測試機械手臂控制界面"""
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 設置字體
    font = QFont("Microsoft JhengHei", 9)
    app.setFont(font)
    
    # 創建主視窗
    window = ArmControlWidget()
    window.setWindowTitle("六軸機械手臂控制系統")
    window.setGeometry(100, 100, 800, 600)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
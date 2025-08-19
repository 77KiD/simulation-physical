"""
配置管理模組 - 修復版本
負責系統配置的儲存和載入
"""

import os
import json
from datetime import datetime  # 添加缺失的導入
from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class HardwareConfig:
    """硬體配置"""
    # GPIO引腳配置
    motor_in1: int = 18
    motor_in2: int = 19
    motor_in3: int = 20
    motor_in4: int = 21
    motor_ena: int = 12
    motor_enb: int = 13
    sensor_pin: int = 24
    relay_pin: int = 25
    
    # 相機配置
    camera_index: int = 0
    camera_width: int = 640
    camera_height: int = 480
    camera_fps: int = 30
    
    # PCA9685配置
    pca9685_address: int = 0x40
    pca9685_frequency: int = 50
    
    # 機械手臂配置
    use_robotic_arm: bool = True  # 是否使用機械手臂
    arm_channels: list = None     # 機械手臂通道配置
    
    # 傳統伺服馬達配置 (備用)
    servo_channel: int = 0
    
    # PWM配置
    pwm_frequency: int = 1000
    
    def __post_init__(self):
        if self.arm_channels is None:
            # 預設六軸機械手臂通道配置
            self.arm_channels = [0, 1, 2, 3, 4, 5]

@dataclass
class DetectionConfig:
    """檢測配置"""
    threshold: float = 0.8
    processing_delay: float = 0.1
    sorting_delay: float = 0.5
    
    # 機械手臂分揀配置
    use_arm_sorting: bool = True
    arm_sequence_timeout: float = 10.0  # 分揀序列超時時間
    
    # 傳統伺服分揀配置 (備用)
    servo_pass_angle: int = 45
    servo_fail_angle: int = 135
    servo_neutral_angle: int = 90

@dataclass
class UIConfig:
    """界面配置"""
    window_width: int = 1400
    window_height: int = 900
    window_x: int = 100
    window_y: int = 100
    theme: str = "default"
    font_family: str = "Microsoft JhengHei"
    font_size: int = 9
    max_log_records: int = 200

@dataclass
class SystemConfig:
    """系統配置"""
    data_directory: str = "data"
    max_records: int = 10000
    auto_save_interval: int = 60  # 秒
    debug_mode: bool = False
    language: str = "zh-TW"

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.hardware = HardwareConfig()
        self.detection = DetectionConfig()
        self.ui = UIConfig()
        self.system = SystemConfig()
        
        # 載入配置
        self.load_config()
    
    def load_config(self):
        """載入配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新各個配置對象
                if 'hardware' in config_data:
                    self._update_dataclass(self.hardware, config_data['hardware'])
                if 'detection' in config_data:
                    self._update_dataclass(self.detection, config_data['detection'])
                if 'ui' in config_data:
                    self._update_dataclass(self.ui, config_data['ui'])
                if 'system' in config_data:
                    self._update_dataclass(self.system, config_data['system'])
                
                print("✅ 配置載入成功")
                
            except Exception as e:
                print(f"⚠️  配置載入失敗，使用預設值: {e}")
                self.save_config()  # 保存預設配置
        else:
            print("📝 未找到配置檔案，創建預設配置")
            self.save_config()
    
    def save_config(self):
        """保存配置"""
        try:
            config_data = {
                'hardware': asdict(self.hardware),
                'detection': asdict(self.detection),
                'ui': asdict(self.ui),
                'system': asdict(self.system)
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print("✅ 配置保存成功")
            
        except Exception as e:
            print(f"❌ 配置保存失敗: {e}")
    
    def _update_dataclass(self, obj, data):
        """更新dataclass對象的字段"""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    def get_hardware_config(self) -> HardwareConfig:
        """獲取硬體配置"""
        return self.hardware
    
    def get_detection_config(self) -> DetectionConfig:
        """獲取檢測配置"""
        return self.detection
    
    def get_ui_config(self) -> UIConfig:
        """獲取界面配置"""
        return self.ui
    
    def get_system_config(self) -> SystemConfig:
        """獲取系統配置"""
        return self.system
    
    def update_hardware_config(self, **kwargs):
        """更新硬體配置"""
        for key, value in kwargs.items():
            if hasattr(self.hardware, key):
                setattr(self.hardware, key, value)
        self.save_config()
    
    def update_detection_config(self, **kwargs):
        """更新檢測配置"""
        for key, value in kwargs.items():
            if hasattr(self.detection, key):
                setattr(self.detection, key, value)
        self.save_config()
    
    def update_ui_config(self, **kwargs):
        """更新界面配置"""
        for key, value in kwargs.items():
            if hasattr(self.ui, key):
                setattr(self.ui, key, value)
        self.save_config()
    
    def update_system_config(self, **kwargs):
        """更新系統配置"""
        for key, value in kwargs.items():
            if hasattr(self.system, key):
                setattr(self.system, key, value)
        self.save_config()
    
    def reset_to_defaults(self):
        """重設為預設值"""
        self.hardware = HardwareConfig()
        self.detection = DetectionConfig()
        self.ui = UIConfig()
        self.system = SystemConfig()
        self.save_config()
        print("🔄 配置已重設為預設值")
    
    def export_config(self, file_path: str):
        """匯出配置"""
        try:
            config_data = {
                'hardware': asdict(self.hardware),
                'detection': asdict(self.detection),
                'ui': asdict(self.ui),
                'system': asdict(self.system),
                'export_time': datetime.now().isoformat()  # 修復：使用 isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 配置已匯出至: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 配置匯出失敗: {e}")
            return False
    
    def import_config(self, file_path: str):
        """導入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 備份當前配置
            backup_file = f"{self.config_file}.backup"
            self.export_config(backup_file)
            
            # 導入新配置
            if 'hardware' in config_data:
                self._update_dataclass(self.hardware, config_data['hardware'])
            if 'detection' in config_data:
                self._update_dataclass(self.detection, config_data['detection'])
            if 'ui' in config_data:
                self._update_dataclass(self.ui, config_data['ui'])
            if 'system' in config_data:
                self._update_dataclass(self.system, config_data['system'])
            
            self.save_config()
            print(f"✅ 配置已從 {file_path} 導入")
            return True
            
        except Exception as e:
            print(f"❌ 配置導入失敗: {e}")
            return False
    
    def validate_config(self) -> Dict[str, list]:
        """驗證配置有效性"""
        errors = {
            'hardware': [],
            'detection': [],
            'ui': [],
            'system': []
        }
        
        # 驗證硬體配置
        gpio_pins = [
            self.hardware.motor_in1, self.hardware.motor_in2,
            self.hardware.motor_in3, self.hardware.motor_in4,
            self.hardware.motor_ena, self.hardware.motor_enb,
            self.hardware.sensor_pin, self.hardware.relay_pin
        ]
        
        if len(set(gpio_pins)) != len(gpio_pins):
            errors['hardware'].append("GPIO引腳配置有重複")
        
        for pin in gpio_pins:
            if not (0 <= pin <= 40):
                errors['hardware'].append(f"GPIO引腳 {pin} 超出範圍 (0-40)")
        
        # 驗證檢測配置
        if not (0.0 <= self.detection.threshold <= 1.0):
            errors['detection'].append("檢測閾值必須在0.0-1.0之間")
        
        if not (0 <= self.detection.servo_pass_angle <= 180):
            errors['detection'].append("合格品伺服角度必須在0-180之間")
        
        if not (0 <= self.detection.servo_fail_angle <= 180):
            errors['detection'].append("缺陷品伺服角度必須在0-180之間")
        
        # 驗證界面配置
        if self.ui.window_width <= 0 or self.ui.window_height <= 0:
            errors['ui'].append("視窗尺寸必須大於0")
        
        if self.ui.font_size <= 0:
            errors['ui'].append("字體大小必須大於0")
        
        # 驗證系統配置
        if self.system.max_records <= 0:
            errors['system'].append("最大記錄數必須大於0")
        
        if self.system.auto_save_interval <= 0:
            errors['system'].append("自動保存間隔必須大於0")
        
        return errors
    
    def get_config_summary(self) -> str:
        """獲取配置摘要"""
        return f"""
配置摘要
========

硬體配置:
- 馬達控制引腳: IN1={self.hardware.motor_in1}, IN2={self.hardware.motor_in2}, IN3={self.hardware.motor_in3}, IN4={self.hardware.motor_in4}
- PWM控制引腳: ENA={self.hardware.motor_ena}, ENB={self.hardware.motor_enb}
- 感測器引腳: {self.hardware.sensor_pin}
- 繼電器引腳: {self.hardware.relay_pin}
- 相機設定: 索引={self.hardware.camera_index}, 解析度={self.hardware.camera_width}x{self.hardware.camera_height}

檢測配置:
- 檢測閾值: {self.detection.threshold}
- 合格品角度: {self.detection.servo_pass_angle}°
- 缺陷品角度: {self.detection.servo_fail_angle}°
- 中性角度: {self.detection.servo_neutral_angle}°

界面配置:
- 視窗尺寸: {self.ui.window_width}x{self.ui.window_height}
- 字體: {self.ui.font_family} {self.ui.font_size}pt
- 主題: {self.ui.theme}

系統配置:
- 數據目錄: {self.system.data_directory}
- 最大記錄數: {self.system.max_records}
- 自動保存間隔: {self.system.auto_save_interval}秒
- 偵錯模式: {'開啟' if self.system.debug_mode else '關閉'}
"""

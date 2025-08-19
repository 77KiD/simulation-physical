"""
六軸機械手臂控制模組
使用PCA9685控制器控制六個360°MG996R伺服馬達組成的機械手臂
"""

import time
import math
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo
    HARDWARE_AVAILABLE = True
except ImportError:
    print("PCA9685硬體模組未安裝，將使用模擬模式")
    HARDWARE_AVAILABLE = False

@dataclass
class JointConfig:
    """關節配置"""
    channel: int        # PCA9685通道
    min_angle: float    # 最小角度
    max_angle: float    # 最大角度
    home_angle: float   # 原點角度
    speed: float = 1.0  # 運動速度 (0.1-2.0)
    name: str = ""      # 關節名稱

@dataclass  
class Position:
    """機械手臂位置"""
    joint1: float = 0.0  # 基座旋轉
    joint2: float = 0.0  # 肩部
    joint3: float = 0.0  # 手肘
    joint4: float = 0.0  # 腕部俯仰
    joint5: float = 0.0  # 腕部翻滾
    joint6: float = 0.0  # 末端夾爪
    
    def to_list(self) -> List[float]:
        """轉換為列表"""
        return [self.joint1, self.joint2, self.joint3, 
                self.joint4, self.joint5, self.joint6]
    
    @classmethod
    def from_list(cls, values: List[float]):
        """從列表創建"""
        return cls(*values[:6])

class RoboticArmController:
    """六軸機械手臂控制器"""
    
    def __init__(self, i2c_address=0x40):
        self.hardware_available = HARDWARE_AVAILABLE
        self.i2c_address = i2c_address
        self.pca = None
        self.servos = {}
        self.current_position = Position()
        self.is_moving = False
        
        # 定義六軸關節配置 (MG996R 360度伺服馬達)
        self.joint_configs = {
            'joint1': JointConfig(0, -180, 180, 0, 1.0, "基座旋轉"),      # 基座
            'joint2': JointConfig(1, -90, 90, 0, 0.8, "肩部俯仰"),        # 肩部
            'joint3': JointConfig(2, -120, 120, -90, 0.8, "手肘彎曲"),    # 手肘
            'joint4': JointConfig(3, -90, 90, 0, 1.2, "腕部俯仰"),        # 腕部俯仰
            'joint5': JointConfig(4, -180, 180, 0, 1.5, "腕部旋轉"),      # 腕部旋轉
            'joint6': JointConfig(5, -45, 45, 0, 2.0, "末端夾爪")         # 夾爪
        }
        
        # 預定義位置
        self.predefined_positions = {
            'home': Position(0, 0, -90, 0, 0, 0),
            'pickup_ready': Position(0, -45, -45, -45, 0, 30),
            'pickup_down': Position(0, -60, -30, -60, 0, 30),
            'pickup_grab': Position(0, -60, -30, -60, 0, -30),
            'transfer_up': Position(0, -30, -60, -30, 0, -30),
            'pass_drop': Position(90, -45, -45, -45, 0, -30),
            'pass_release': Position(90, -45, -45, -45, 0, 30),
            'fail_drop': Position(-90, -45, -45, -45, 0, -30),
            'fail_release': Position(-90, -45, -45, -45, 0, 30),
            'standby': Position(0, -20, -70, -20, 0, 0)
        }
        
        self.init_hardware()
        
    def init_hardware(self):
        """初始化硬體"""
        if self.hardware_available:
            try:
                # 初始化I2C和PCA9685
                i2c = busio.I2C(board.SCL, board.SDA)
                self.pca = PCA9685(i2c, address=self.i2c_address)
                self.pca.frequency = 50  # 50Hz for servo control
                
                # 初始化六個伺服馬達
                for joint_name, config in self.joint_configs.items():
                    # 為MG996R設定適當的脈衝寬度範圍
                    servo_obj = servo.ContinuousServo(
                        self.pca.channels[config.channel],
                        min_pulse=500,   # 0.5ms
                        max_pulse=2500   # 2.5ms
                    )
                    self.servos[joint_name] = servo_obj
                
                print("✅ 六軸機械手臂硬體初始化完成")
                
                # 移動到原點位置
                time.sleep(1)
                self.move_to_home()
                
            except Exception as e:
                print(f"❌ 機械手臂硬體初始化失敗: {e}")
                self.hardware_available = False
        else:
            print("⚠️ 機械手臂以模擬模式運行")
    
    def angle_to_throttle(self, angle: float, joint_config: JointConfig) -> float:
        """
        將角度轉換為MG996R連續伺服馬達的油門值
        
        Args:
            angle: 目標角度
            joint_config: 關節配置
            
        Returns:
            throttle值 (-1.0 到 1.0)
        """
        # 限制角度範圍
        angle = max(joint_config.min_angle, min(joint_config.max_angle, angle))
        
        # 將角度映射到油門值 (-1.0 到 1.0)
        angle_range = joint_config.max_angle - joint_config.min_angle
        normalized = (angle - joint_config.min_angle) / angle_range
        throttle = (normalized * 2.0) - 1.0
        
        return throttle
    
    def move_joint(self, joint_name: str, angle: float, duration: float = 1.0) -> bool:
        """
        移動單一關節
        
        Args:
            joint_name: 關節名稱
            angle: 目標角度
            duration: 運動時間
            
        Returns:
            是否成功
        """
        if joint_name not in self.joint_configs:
            print(f"❌ 未知關節: {joint_name}")
            return False
        
        config = self.joint_configs[joint_name]
        
        if not self.hardware_available:
            print(f"🤖 模擬模式: {config.name} 移動到 {angle:.1f}°")
            setattr(self.current_position, joint_name, angle)
            return True
        
        try:
            # 計算油門值
            throttle = self.angle_to_throttle(angle, config)
            
            # 設定伺服馬達運動
            servo_obj = self.servos[joint_name]
            servo_obj.throttle = throttle * config.speed
            
            # 等待運動時間
            time.sleep(duration)
            
            # 停止馬達
            servo_obj.throttle = 0
            
            # 更新當前位置
            setattr(self.current_position, joint_name, angle)
            
            print(f"✅ {config.name} 移動到 {angle:.1f}°")
            return True
            
        except Exception as e:
            print(f"❌ 關節 {joint_name} 移動失敗: {e}")
            return False
    
    def move_to_position(self, position: Position, duration: float = 2.0) -> bool:
        """
        移動到指定位置
        
        Args:
            position: 目標位置
            duration: 總運動時間
            
        Returns:
            是否成功
        """
        if self.is_moving:
            print("⚠️ 機械手臂正在運動中，請稍後...")
            return False
        
        self.is_moving = True
        
        try:
            joint_names = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
            target_angles = position.to_list()
            
            print(f"🤖 機械手臂移動到目標位置...")
            
            if not self.hardware_available:
                print(f"🤖 模擬模式: 移動到位置 {target_angles}")
                self.current_position = position
                time.sleep(duration)
                return True
            
            # 同步移動所有關節
            for joint_name, target_angle in zip(joint_names, target_angles):
                config = self.joint_configs[joint_name]
                
                # 限制角度範圍
                target_angle = max(config.min_angle, min(config.max_angle, target_angle))
                
                # 計算油門值並設定
                throttle = self.angle_to_throttle(target_angle, config)
                servo_obj = self.servos[joint_name]
                servo_obj.throttle = throttle * config.speed
            
            # 等待運動完成
            time.sleep(duration)
            
            # 停止所有馬達
            for joint_name in joint_names:
                self.servos[joint_name].throttle = 0
            
            # 更新當前位置
            self.current_position = position
            print(f"✅ 機械手臂已到達目標位置")
            
            return True
            
        except Exception as e:
            print(f"❌ 機械手臂移動失敗: {e}")
            return False
        finally:
            self.is_moving = False
    
    def move_to_predefined(self, position_name: str, duration: float = 2.0) -> bool:
        """
        移動到預定義位置
        
        Args:
            position_name: 預定義位置名稱
            duration: 運動時間
            
        Returns:
            是否成功
        """
        if position_name not in self.predefined_positions:
            print(f"❌ 未知預定義位置: {position_name}")
            return False
        
        target_position = self.predefined_positions[position_name]
        return self.move_to_position(target_position, duration)
    
    def move_to_home(self) -> bool:
        """移動到原點位置"""
        print("🏠 機械手臂回到原點位置")
        return self.move_to_predefined('home', 3.0)
    
    def execute_pick_and_place_sequence(self, target: str = 'pass') -> bool:
        """
        執行完整的分揀動作序列
        
        Args:
            target: 'pass' 為合格品, 'fail' 為缺陷品
            
        Returns:
            是否成功
        """
        if self.is_moving:
            print("⚠️ 機械手臂忙碌中...")
            return False
        
        print(f"🤖 開始執行分揀序列: {target}")
        
        try:
            # 1. 移動到拾取準備位置
            if not self.move_to_predefined('pickup_ready', 1.5):
                return False
            
            # 2. 下降到拾取位置
            if not self.move_to_predefined('pickup_down', 1.0):
                return False
            
            # 3. 夾取物件
            if not self.move_to_predefined('pickup_grab', 0.5):
                return False
            
            # 4. 提升物件
            if not self.move_to_predefined('transfer_up', 1.0):
                return False
            
            # 5. 移動到目標位置
            if target == 'pass':
                if not self.move_to_predefined('pass_drop', 1.5):
                    return False
                # 6. 釋放物件
                if not self.move_to_predefined('pass_release', 0.5):
                    return False
            else:  # fail
                if not self.move_to_predefined('fail_drop', 1.5):
                    return False
                # 6. 釋放物件
                if not self.move_to_predefined('fail_release', 0.5):
                    return False
            
            # 7. 回到待命位置
            if not self.move_to_predefined('standby', 1.5):
                return False
            
            print(f"✅ 分揀序列完成: {target}")
            return True
            
        except Exception as e:
            print(f"❌ 分揀序列執行失敗: {e}")
            return False
    
    def get_current_position(self) -> Position:
        """獲取當前位置"""
        return self.current_position
    
    def get_joint_info(self) -> Dict:
        """獲取關節資訊"""
        info = {}
        for joint_name, config in self.joint_configs.items():
            current_angle = getattr(self.current_position, joint_name)
            info[joint_name] = {
                'name': config.name,
                'current_angle': current_angle,
                'min_angle': config.min_angle,
                'max_angle': config.max_angle,
                'channel': config.channel
            }
        return info
    
    def calibrate_joint(self, joint_name: str) -> bool:
        """
        關節校正
        
        Args:
            joint_name: 關節名稱
            
        Returns:
            是否成功
        """
        if joint_name not in self.joint_configs:
            return False
        
        config = self.joint_configs[joint_name]
        print(f"🔧 校正關節: {config.name}")
        
        # 移動到最小位置
        self.move_joint(joint_name, config.min_angle, 1.0)
        time.sleep(1)
        
        # 移動到最大位置
        self.move_joint(joint_name, config.max_angle, 2.0)
        time.sleep(1)
        
        # 回到原點
        self.move_joint(joint_name, config.home_angle, 1.0)
        
        print(f"✅ 關節 {config.name} 校正完成")
        return True
    
    def emergency_stop(self):
        """緊急停止"""
        print("🚨 緊急停止機械手臂")
        
        if self.hardware_available and self.servos:
            try:
                for servo_obj in self.servos.values():
                    servo_obj.throttle = 0
                print("✅ 所有關節已停止")
            except Exception as e:
                print(f"❌ 緊急停止失敗: {e}")
        
        self.is_moving = False
    
    def save_position(self, name: str, position: Position = None):
        """儲存位置"""
        if position is None:
            position = self.current_position
        
        self.predefined_positions[name] = position
        print(f"💾 位置 '{name}' 已儲存: {position.to_list()}")
    
    def load_positions_from_file(self, filename: str = "arm_positions.json"):
        """從檔案載入位置"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for name, pos_data in data.items():
                if isinstance(pos_data, list) and len(pos_data) >= 6:
                    self.predefined_positions[name] = Position.from_list(pos_data)
            
            print(f"✅ 從 {filename} 載入位置設定")
            
        except FileNotFoundError:
            print(f"⚠️ 位置檔案 {filename} 不存在")
        except Exception as e:
            print(f"❌ 載入位置失敗: {e}")
    
    def save_positions_to_file(self, filename: str = "arm_positions.json"):
        """儲存位置到檔案"""
        try:
            data = {}
            for name, position in self.predefined_positions.items():
                data[name] = position.to_list()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 位置設定已儲存到 {filename}")
            
        except Exception as e:
            print(f"❌ 儲存位置失敗: {e}")
    
    def get_status(self) -> Dict:
        """獲取機械手臂狀態"""
        return {
            'hardware_available': self.hardware_available,
            'is_moving': self.is_moving,
            'current_position': self.current_position.to_list(),
            'joint_count': len(self.joint_configs),
            'predefined_positions': len(self.predefined_positions)
        }
    
    def cleanup(self):
        """清理資源"""
        if self.hardware_available:
            try:
                # 停止所有馬達
                for servo_obj in self.servos.values():
                    servo_obj.throttle = 0
                
                # 關閉PCA9685
                if self.pca:
                    self.pca.deinit()
                
                print("✅ 機械手臂資源清理完成")
                
            except Exception as e:
                print(f"❌ 機械手臂資源清理失敗: {e}")
    
    def __del__(self):
        """析構函數"""
        self.cleanup()


# 測試函數
def test_robotic_arm():
    """測試機械手臂功能"""
    print("🧪 開始測試六軸機械手臂")
    
    arm = RoboticArmController()
    
    # 測試基本移動
    print("\n📍 測試基本位置移動...")
    arm.move_to_predefined('standby')
    time.sleep(1)
    
    # 測試分揀序列
    print("\n🤖 測試合格品分揀序列...")
    arm.execute_pick_and_place_sequence('pass')
    
    print("\n🤖 測試缺陷品分揀序列...")
    arm.execute_pick_and_place_sequence('fail')
    
    # 回到原點
    print("\n🏠 回到原點...")
    arm.move_to_home()
    
    # 顯示狀態
    status = arm.get_status()
    print(f"\n📊 機械手臂狀態: {status}")
    
    arm.cleanup()
    print("\n✅ 測試完成")


if __name__ == '__main__':
    test_robotic_arm()

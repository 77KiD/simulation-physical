"""
硬體控制模組
負責所有硬體設備的控制和管理
"""

import cv2
import time
import numpy as np

# 硬體控制模組
try:
    import Jetson.GPIO as GPIO
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo
    GPIO_AVAILABLE = True
except ImportError:
    print("GPIO模組未安裝，將使用模擬模式")
    GPIO_AVAILABLE = False

class HardwareController:
    """硬體控制器類"""
    
    def __init__(self):
        self.gpio_available = GPIO_AVAILABLE
        self.camera = None
        self.pca = None
        self.servo_motor = None
        self.relay_state = False
        self.init_hardware()
        
    def init_hardware(self):
        """初始化硬體設備"""
        if self.gpio_available:
            try:
                # GPIO初始化
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                
                # 定義GPIO引腳
                self.MOTOR_IN1 = 18  # L298N控制引腳
                self.MOTOR_IN2 = 19
                self.MOTOR_IN3 = 20
                self.MOTOR_IN4 = 21
                self.MOTOR_ENA = 12  # PWM控制引腳
                self.MOTOR_ENB = 13
                
                self.SENSOR_PIN = 24  # TCRT5000光電感測器
                self.RELAY_PIN = 25   # 繼電器控制引腳
                
                # 設置GPIO引腳模式
                GPIO.setup([self.MOTOR_IN1, self.MOTOR_IN2, self.MOTOR_IN3, self.MOTOR_IN4], GPIO.OUT)
                GPIO.setup([self.MOTOR_ENA, self.MOTOR_ENB], GPIO.OUT)
                GPIO.setup(self.SENSOR_PIN, GPIO.IN)
                GPIO.setup(self.RELAY_PIN, GPIO.OUT)
                
                # PWM初始化
                self.pwm_a = GPIO.PWM(self.MOTOR_ENA, 1000)  # 1kHz頻率
                self.pwm_b = GPIO.PWM(self.MOTOR_ENB, 1000)
                self.pwm_a.start(0)
                self.pwm_b.start(0)
                
                # PCA9685初始化 (用於SG90伺服馬達)
                i2c = busio.I2C(board.SCL, board.SDA)
                self.pca = PCA9685(i2c)
                self.pca.frequency = 50  # 50Hz for servo
                self.servo_motor = servo.Servo(self.pca.channels[0])
                
                # 初始化繼電器
                GPIO.output(self.RELAY_PIN, GPIO.LOW)
                self.relay_state = False
                
                print("硬體初始化完成")
                
            except Exception as e:
                print(f"硬體初始化失敗: {e}")
                self.gpio_available = False
        
        # USB相機初始化
        self.init_camera()
        
        # 嘗試初始化六軸機械手臂
        self.init_robotic_arm()
    
    def init_camera(self):
        """初始化USB相機"""
        try:
            self.camera = cv2.VideoCapture(0)  # 使用第一個相機
            if self.camera.isOpened():
                # 設置相機參數
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                print("相機初始化成功")
                return True
            else:
                print("相機初始化失敗")
                self.camera = None
                return False
        except Exception as e:
            print(f"相機初始化錯誤: {e}")
            self.camera = None
            return False
    
    def get_camera_frame(self):
        """獲取相機畫面"""
        if self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                return frame
        return None
    
    def is_camera_available(self):
        """檢查相機是否可用"""
        return self.camera is not None and self.camera.isOpened()
    
    def set_conveyor_speed(self, speed, direction='forward'):
        """設置輸送帶速度和方向"""
        if not self.gpio_available:
            print(f"模擬模式：輸送帶速度設置為 {speed}%，方向：{direction}")
            return True
            
        try:
            speed = max(0, min(100, speed))  # 限制速度範圍 0-100%
            
            if direction == 'forward':
                GPIO.output(self.MOTOR_IN1, GPIO.HIGH)
                GPIO.output(self.MOTOR_IN2, GPIO.LOW)
                GPIO.output(self.MOTOR_IN3, GPIO.HIGH)
                GPIO.output(self.MOTOR_IN4, GPIO.LOW)
            elif direction == 'backward':
                GPIO.output(self.MOTOR_IN1, GPIO.LOW)
                GPIO.output(self.MOTOR_IN2, GPIO.HIGH)
                GPIO.output(self.MOTOR_IN3, GPIO.LOW)
                GPIO.output(self.MOTOR_IN4, GPIO.HIGH)
            else:  # stop
                GPIO.output([self.MOTOR_IN1, self.MOTOR_IN2, self.MOTOR_IN3, self.MOTOR_IN4], GPIO.LOW)
                speed = 0
            
            # 設置PWM速度
            self.pwm_a.ChangeDutyCycle(speed)
            self.pwm_b.ChangeDutyCycle(speed)
            return True
            
        except Exception as e:
            print(f"輸送帶控制錯誤: {e}")
            return False
    
    def stop_conveyor(self):
        """停止輸送帶"""
        return self.set_conveyor_speed(0)
    
    def set_servo_angle(self, angle):
        """設置伺服馬達角度 (舊版本相容性保留)"""
        if not self.gpio_available:
            print(f"模擬模式：伺服馬達角度設置為 {angle}°")
            return True
            
        try:
            angle = max(0, min(180, angle))  # 限制角度範圍 0-180°
            if self.servo_motor:
                self.servo_motor.angle = angle
                return True
            return False
        except Exception as e:
            print(f"伺服馬達控制錯誤: {e}")
            return False
    
    def init_robotic_arm(self):
        """初始化六軸機械手臂"""
        try:
            from robotic_arm_controller import RoboticArmController
            self.robotic_arm = RoboticArmController()
            print("✅ 六軸機械手臂初始化完成")
            return True
        except ImportError:
            print("⚠️ 機械手臂控制模組未找到，使用傳統SG90伺服馬達")
            self.robotic_arm = None
            return False
        except Exception as e:
            print(f"❌ 機械手臂初始化失敗: {e}")
            self.robotic_arm = None
            return False
    
    def execute_sorting_action(self, result: str):
        """執行分揀動作"""
        if hasattr(self, 'robotic_arm') and self.robotic_arm:
            # 使用六軸機械手臂進行分揀
            target = 'pass' if result == "合格" else 'fail'
            return self.robotic_arm.execute_pick_and_place_sequence(target)
        else:
            # 回退到傳統SG90伺服馬達控制
            if result == "合格":
                return self.set_servo_angle(45)
            else:
                return self.set_servo_angle(135)
    
    def get_arm_status(self):
        """獲取機械手臂狀態"""
        if hasattr(self, 'robotic_arm') and self.robotic_arm:
            return self.robotic_arm.get_status()
        else:
            return {
                'hardware_available': False,
                'is_moving': False,
                'arm_type': 'SG90_servo'
            }
    
    def read_sensor(self):
        """讀取光電感測器狀態"""
        if not self.gpio_available:
            # 模擬模式：隨機返回感測器狀態
            import random
            return random.choice([True, False])
            
        try:
            return GPIO.input(self.SENSOR_PIN) == GPIO.HIGH
        except Exception as e:
            print(f"感測器讀取錯誤: {e}")
            return False
    
    def control_relay(self, state):
        """控制繼電器"""
        if not self.gpio_available:
            print(f"模擬模式：繼電器狀態設置為 {'開啟' if state else '關閉'}")
            self.relay_state = state
            return True
            
        try:
            GPIO.output(self.RELAY_PIN, GPIO.HIGH if state else GPIO.LOW)
            self.relay_state = state
            return True
        except Exception as e:
            print(f"繼電器控制錯誤: {e}")
            return False
    
    def get_relay_state(self):
        """獲取繼電器狀態"""
        return self.relay_state
    
    def get_hardware_status(self):
        """獲取硬體狀態"""
        return {
            'gpio_available': self.gpio_available,
            'camera_available': self.is_camera_available(),
            'relay_state': self.relay_state
        }
    
    def cleanup(self):
        """清理硬體資源"""
        if self.camera:
            self.camera.release()
        
        # 清理機械手臂資源
        if hasattr(self, 'robotic_arm') and self.robotic_arm:
            self.robotic_arm.cleanup()
        
        if self.gpio_available:
            try:
                self.stop_conveyor()
                self.control_relay(False)
                if self.pca:
                    self.pca.deinit()
                GPIO.cleanup()
            except Exception as e:
                print(f"硬體清理錯誤: {e}")
    
    def __del__(self):
        """析構函數"""
        self.cleanup()

"""
檢測引擎模組 - 修復版本
添加了缺失的cv2導入和修復了相關問題
"""

import time
import random
import cv2  # 添加缺失的導入
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

class DetectionEngine:
    """檢測引擎類"""
    
    def __init__(self):
        self.threshold = 0.8
        self.defect_types = ["短路", "斷路", "橋接", "缺件"]
        
    def detect_pcba(self, frame):
        """
        PCBA檢測邏輯（簡化版本）
        
        Args:
            frame: OpenCV影像幀
            
        Returns:
            tuple: (檢測結果, 缺陷類型, 信心分數)
        """
        if frame is None:
            return "錯誤", "", 0.0
            
        # 這裡可以加入實際的AI檢測邏輯
        # 目前使用簡化的檢測邏輯作為示例
        
        # 模擬檢測過程
        time.sleep(0.1)  # 模擬處理時間
        
        # 基於閾值和隨機因素決定檢測結果
        detection_score = random.random()
        
        if detection_score > self.threshold:
            return "合格", "", detection_score
        else:
            defect_type = random.choice(self.defect_types)
            return "缺陷", defect_type, detection_score
    
    def set_threshold(self, threshold):
        """設置檢測閾值"""
        self.threshold = max(0.0, min(1.0, threshold))
    
    def get_threshold(self):
        """獲取當前閾值"""
        return self.threshold
    
    def analyze_image(self, frame):
        """
        分析影像品質和特徵
        
        Args:
            frame: OpenCV影像幀
            
        Returns:
            dict: 分析結果
        """
        if frame is None:
            return {"error": "無效影像"}
        
        # 計算影像基本特徵
        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        
        # 計算統計特徵
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        # 計算邊緣密度（作為複雜度指標）
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (width * height)
        
        return {
            "width": width,
            "height": height,
            "mean_brightness": float(mean_brightness),
            "std_brightness": float(std_brightness),
            "edge_density": float(edge_density),
            "quality_score": self._calculate_quality_score(mean_brightness, std_brightness, edge_density)
        }
    
    def _calculate_quality_score(self, brightness, std, edge_density):
        """計算影像品質分數"""
        # 簡化的品質評估
        brightness_score = 1.0 - abs(brightness - 127.5) / 127.5  # 理想亮度約127.5
        contrast_score = min(std / 50.0, 1.0)  # 標準差越大對比度越好
        detail_score = min(edge_density * 10, 1.0)  # 適度的邊緣密度
        
        return (brightness_score + contrast_score + detail_score) / 3.0

class DetectionThread(QThread):
    """檢測線程"""
    detection_result = pyqtSignal(str, str, float)  # result, defect_type, confidence
    sensor_triggered = pyqtSignal()
    
    def __init__(self, hardware_controller, system_ref):
        super().__init__()
        self.hardware = hardware_controller
        self.system_ref = system_ref  # 引用主程式對象以讀取狀態
        self.detection_engine = DetectionEngine()
        self.running = False
        self.processing = False
        
    def run(self):
        """運行檢測邏輯"""
        self.running = True
        last_sensor_state = False
        
        while self.running:
            try:
                # 檢查系統是否啟動檢測
                if not hasattr(self.system_ref, 'is_running') or not self.system_ref.is_running:
                    time.sleep(0.1)
                    continue
                
                # 檢查輸送帶是否運行
                if not hasattr(self.system_ref, 'conveyor_running') or not self.system_ref.conveyor_running:
                    time.sleep(0.1)
                    continue
                
                # 讀取感測器狀態
                current_sensor_state = self.hardware.read_sensor()
                
                # 檢測到物體（感測器從低電平變為高電平）
                if current_sensor_state and not last_sensor_state and not self.processing:
                    self.processing = True
                    self.sensor_triggered.emit()
                    
                    # 獲取相機畫面進行檢測
                    frame = self.hardware.get_camera_frame()
                    if frame is not None:
                        result, defect, confidence = self.detection_engine.detect_pcba(frame)
                        self.detection_result.emit(result, defect, confidence)
                        
                        # 控制分類機構
                        self._control_sorting(result)
                    
                    # 處理完成後等待一段時間
                    time.sleep(1.0)
                    self.processing = False
                
                last_sensor_state = current_sensor_state
                time.sleep(0.05)  # 20Hz檢測頻率
                
            except Exception as e:
                print(f"檢測線程錯誤: {e}")
                time.sleep(0.1)
    
    def _control_sorting(self, result):
        """控制分類機構"""
        try:
            # 使用硬體控制器的新分揀方法
            success = self.hardware.execute_sorting_action(result)
            
            if success:
                print(f"✅ 分揀動作完成: {result}")
            else:
                print(f"⚠️ 分揀動作失敗: {result}")
            
            # 等待分揀完成 (機械手臂需要更長時間)
            if hasattr(self.hardware, 'robotic_arm') and self.hardware.robotic_arm:
                time.sleep(0.5)  # 機械手臂有自己的時序控制
            else:
                # 傳統伺服馬達控制
                time.sleep(0.5)
                self.hardware.set_servo_angle(90)  # 回到中間位置
            
        except Exception as e:
            print(f"分類控制錯誤: {e}")
    
    def set_threshold(self, threshold):
        """設置檢測閾值"""
        self.detection_engine.set_threshold(threshold)
    
    def get_threshold(self):
        """獲取檢測閾值"""
        return self.detection_engine.get_threshold()
    
    def stop(self):
        """停止檢測"""
        self.running = False
        self.quit()
        self.wait(3000)  # 等待3秒後強制退出

class CameraThread(QThread):
    """相機線程"""
    frame_ready = pyqtSignal(np.ndarray)
    
    def __init__(self, hardware_controller):
        super().__init__()
        self.hardware = hardware_controller
        self.running = False
        
    def run(self):
        """線程運行"""
        self.running = True
        while self.running:
            try:
                frame = self.hardware.get_camera_frame()
                if frame is not None:
                    self.frame_ready.emit(frame)
                time.sleep(0.033)  # ~30 FPS
            except Exception as e:
                print(f"相機線程錯誤: {e}")
                time.sleep(0.1)
    
    def stop(self):
        """停止線程"""
        self.running = False
        self.quit()
        self.wait(3000)  # 等待3秒後強制退出
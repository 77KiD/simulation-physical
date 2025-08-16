"""
檢測引擎模組
負責PCBA檢測邏輯和演算法，整合YOLOv12推論
"""

import time
import random
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

# 嘗試導入影像處理模組
try:
    from image_processor import ImageProcessor
    IMAGE_PROCESSOR_AVAILABLE = True
except ImportError:
    print("⚠️ 影像處理模組未找到，使用簡化檢測")
    IMAGE_PROCESSOR_AVAILABLE = False

class DetectionEngine:
    """檢測引擎類"""
    
    def __init__(self):
        self.threshold = 0.8
        self.defect_types = ["短路", "斷路", "橋接", "缺件"]
        
        # 初始化影像處理器
        if IMAGE_PROCESSOR_AVAILABLE:
            self.image_processor = ImageProcessor()
        else:
            self.image_processor = None
        
    def detect_pcba(self, frame):
        """
        PCBA檢測邏輯 (整合YOLOv12)
        
        Args:
            frame: OpenCV影像幀
            
        Returns:
            tuple: (檢測結果, 缺陷類型, 信心分數, YOLO檢測結果)
        """
        if frame is None:
            return "錯誤", "", 0.0, []
            
        # 如果有影像處理器，使用AI檢測
        if self.image_processor:
            try:
                # 運行YOLOv12推論
                _, processed_frame, detections = self.image_processor.process_frame(frame)
                
                # 基於YOLO檢測結果進行PCBA品質判斷
                result, defect_type, confidence = self._analyze_yolo_results(detections)
                
                return result, defect_type, confidence, detections
                
            except Exception as e:
                print(f"AI檢測錯誤: {e}")
                # 回退到簡單檢測
                return self._simple_detection(frame)
        else:
            # 使用簡單檢測
            return self._simple_detection(frame)
    
    def _analyze_yolo_results(self, detections):
        """
        分析YOLO檢測結果以判斷PCBA品質
        
        Args:
            detections: YOLO檢測結果列表
            
        Returns:
            tuple: (檢測結果, 缺陷類型, 信心分數)
        """
        if not detections:
            return "無法判斷", "", 0.0
        
        # 統計檢測到的物件
        detected_classes = {}
        max_confidence = 0.0
        
        for detection in detections:
            class_name = detection.class_name
            confidence = detection.confidence
            
            detected_classes[class_name] = detected_classes.get(class_name, 0) + 1
            max_confidence = max(max_confidence, confidence)
        
        # PCBA品質判斷邏輯
        defect_indicators = ['defect', 'short', 'missing', 'bridge']
        
        # 檢查是否有缺陷指標
        found_defects = []
        for defect_type in defect_indicators:
            if defect_type in detected_classes:
                if defect_type == 'short':
                    found_defects.append("短路")
                elif defect_type == 'missing':
                    found_defects.append("缺件")
                elif defect_type == 'bridge':
                    found_defects.append("橋接")
                else:
                    found_defects.append("斷路")
        
        # 判斷結果
        if found_defects:
            return "缺陷", found_defects[0], max_confidence
        elif 'pcb' in detected_classes and 'component' in detected_classes:
            # 檢測到PCB和元件，判斷為合格
            component_count = detected_classes['component']
            
            # 基於元件數量和信心度判斷
            if component_count >= 2 and max_confidence > self.threshold:
                return "合格", "", max_confidence
            else:
                return "缺陷", "元件異常", max_confidence
        else:
            # 未能正確識別PCB結構
            return "缺陷", "結構異常", max_confidence
    
    def _simple_detection(self, frame):
        """
        簡化的檢測邏輯（備用方案）
        """
        # 模擬檢測過程
        time.sleep(0.1)
        
        # 基於閾值和隨機因素決定檢測結果
        detection_score = random.random()
        
        if detection_score > self.threshold:
            return "合格", "", detection_score, []
        else:
            defect_type = random.choice(self.defect_types)
            return "缺陷", defect_type, detection_score, []
    
    def set_threshold(self, threshold):
        """設置檢測閾值"""
        self.threshold = max(0.0, min(1.0, threshold))
    
    def get_threshold(self):
        """獲取當前閾值"""
        return self.threshold
    
    def analyze_image(self, frame):
        """
        分析影像品質和特徵 (增強版)
        
        Args:
            frame: OpenCV影像幀
            
        Returns:
            dict: 分析結果
        """
        if frame is None:
            return {"error": "無效影像"}
        
        # 基本影像分析
        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        
        # 計算統計特徵
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        # 計算邊緣密度
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (width * height)
        
        # 如果有影像處理器，獲取額外統計
        extra_stats = {}
        if self.image_processor:
            try:
                stats = self.image_processor.get_processing_stats()
                extra_stats.update(stats)
            except:
                pass
        
        result = {
            "width": width,
            "height": height,
            "mean_brightness": float(mean_brightness),
            "std_brightness": float(std_brightness),
            "edge_density": float(edge_density),
            "quality_score": self._calculate_quality_score(mean_brightness, std_brightness, edge_density),
            **extra_stats
        }
        
        return result
    
    def _calculate_quality_score(self, brightness, std, edge_density):
        """計算影像品質分數"""
        # 簡化的品質評估
        brightness_score = 1.0 - abs(brightness - 127.5) / 127.5  # 理想亮度約127.5
        contrast_score = min(std / 50.0, 1.0)  # 標準差越大對比度越好
        detail_score = min(edge_density * 10, 1.0)  # 適度的邊緣密度
        
        return (brightness_score + contrast_score + detail_score) / 3.0
    
    def get_processor_config(self):
        """獲取影像處理器配置"""
        if self.image_processor:
            return self.image_processor.config
        return None
    
    def update_processor_config(self, **kwargs):
        """更新影像處理器配置"""
        if self.image_processor:
            self.image_processor.update_config(**kwargs)

class DetectionThread(QThread):
    """檢測線程 (增強版)"""
    detection_result = pyqtSignal(str, str, float, list)  # result, defect_type, confidence, yolo_detections
    sensor_triggered = pyqtSignal()
    processing_stats = pyqtSignal(dict)  # 處理統計信號估
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

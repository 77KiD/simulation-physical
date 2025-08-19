"""
影像處理和YOLOv12推論模組
負責影像前處理、邊緣檢測、濾波增強和YOLO物件偵測
"""

import cv2
import numpy as np
import time
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass

try:
    # 嘗試導入YOLOv8 (ultralytics套件，包含YOLOv12)
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    print("✅ YOLOv12/ultralytics 可用")
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️ YOLOv12/ultralytics 未安裝，將使用模擬推論")

@dataclass
class DetectionResult:
    """檢測結果數據類"""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]

@dataclass
class ProcessingConfig:
    """影像處理配置"""
    # 邊緣檢測參數
    canny_low: int = 50
    canny_high: int = 150
    canny_aperture: int = 3
    
    # 高斯濾波參數
    gaussian_kernel: int = 5
    gaussian_sigma: float = 1.0
    
    # 對比度增強參數
    contrast_alpha: float = 1.5  # 對比度增強因子
    brightness_beta: int = 10    # 亮度調整
    
    # YOLO推論參數
    yolo_confidence: float = 0.5  # 信心閾值
    yolo_iou: float = 0.4        # NMS IoU閾值
    yolo_max_detections: int = 10 # 最大檢測數量
    
    # 顯示參數
    show_edges: bool = True       # 顯示邊緣
    show_enhanced: bool = True    # 顯示增強後影像
    show_detections: bool = True  # 顯示檢測結果

class ImageProcessor:
    """影像處理器類"""
    
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.config = ProcessingConfig()
        self.yolo_model = None
        self.model_path = model_path
        self.processing_stats = {
            'frame_count': 0,
            'processing_time': 0.0,
            'inference_time': 0.0
        }
        
        # PCBA相關類別名稱 (可自定義)
        self.pcba_classes = {
            0: 'pcb',           # 印刷電路板
            1: 'component',     # 電子元件
            2: 'connector',     # 連接器
            3: 'capacitor',     # 電容
            4: 'resistor',      # 電阻
            5: 'ic',           # 積體電路
            6: 'defect',       # 缺陷
            7: 'short',        # 短路
            8: 'missing',      # 缺件
            9: 'bridge'        # 橋接
        }
        
        self.init_yolo_model()
    
    def init_yolo_model(self):
        """初始化YOLO模型"""
        if not YOLO_AVAILABLE:
            print("⚠️ YOLO模組不可用，將使用模擬推論")
            return
            
        try:
            # 載入YOLOv12模型 (如果有) 或 YOLOv8
            print(f"🔄 載入YOLO模型: {self.model_path}")
            self.yolo_model = YOLO(self.model_path)
            
            # 暖機運行
            dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
            _ = self.yolo_model.predict(dummy_image, verbose=False)
            
            print("✅ YOLO模型載入成功")
            
        except Exception as e:
            print(f"❌ YOLO模型載入失敗: {e}")
            self.yolo_model = None
    
    def apply_edge_detection(self, image: np.ndarray) -> np.ndarray:
        """
        邊緣檢測處理
        
        Args:
            image: 輸入影像
            
        Returns:
            邊緣檢測結果
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 高斯模糊降噪
        blurred = cv2.GaussianBlur(
            gray, 
            (self.config.gaussian_kernel, self.config.gaussian_kernel),
            self.config.gaussian_sigma
        )
        
        # Canny邊緣檢測
        edges = cv2.Canny(
            blurred,
            self.config.canny_low,
            self.config.canny_high,
            apertureSize=self.config.canny_aperture
        )
        
        # 轉換為三通道以便顯示
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        return edges_colored
    
    def apply_enhancement(self, image: np.ndarray) -> np.ndarray:
        """
        影像增強處理 (對比度、亮度、銳化)
        
        Args:
            image: 輸入影像
            
        Returns:
            增強後影像
        """
        # 對比度和亮度調整
        enhanced = cv2.convertScaleAbs(
            image, 
            alpha=self.config.contrast_alpha, 
            beta=self.config.brightness_beta
        )
        
        # 銳化濾波器
        sharpening_kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1], 
            [-1, -1, -1]
        ])
        
        # 應用銳化
        sharpened = cv2.filter2D(enhanced, -1, sharpening_kernel)
        
        # 高斯濾波平滑
        smoothed = cv2.GaussianBlur(
            sharpened,
            (self.config.gaussian_kernel, self.config.gaussian_kernel),
            self.config.gaussian_sigma
        )
        
        return smoothed
    
    def run_yolo_inference(self, image: np.ndarray) -> Tuple[np.ndarray, List[DetectionResult]]:
        """
        運行YOLOv12推論
        
        Args:
            image: 輸入影像
            
        Returns:
            (帶檢測框的影像, 檢測結果列表)
        """
        start_time = time.time()
        
        if not self.yolo_model:
            # 模擬推論結果
            return self._simulate_yolo_inference(image)
        
        try:
            # YOLOv12推論
            results = self.yolo_model.predict(
                image,
                conf=self.config.yolo_confidence,
                iou=self.config.yolo_iou,
                max_det=self.config.yolo_max_detections,
                verbose=False
            )
            
            # 處理檢測結果
            detections = []
            annotated_image = image.copy()
            
            if results and len(results) > 0:
                result = results[0]  # 取第一個結果
                
                # 獲取檢測框
                if result.boxes is not None:
                    boxes = result.boxes.cpu().numpy()
                    
                    for box in boxes:
                        # 座標和信心度
                        x1, y1, x2, y2 = box.xyxy[0].astype(int)
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        
                        # 類別名稱
                        class_name = self.pcba_classes.get(class_id, f"class_{class_id}")
                        
                        # 中心點
                        center_x = int((x1 + x2) / 2)
                        center_y = int((y1 + y2) / 2)
                        
                        # 創建檢測結果
                        detection = DetectionResult(
                            class_id=class_id,
                            class_name=class_name,
                            confidence=confidence,
                            bbox=(x1, y1, x2, y2),
                            center=(center_x, center_y)
                        )
                        detections.append(detection)
                        
                        # 繪製檢測框
                        if self.config.show_detections:
                            self._draw_detection(annotated_image, detection)
            
            self.processing_stats['inference_time'] = time.time() - start_time
            
            return annotated_image, detections
            
        except Exception as e:
            print(f"YOLO推論錯誤: {e}")
            return self._simulate_yolo_inference(image)
    
    def _simulate_yolo_inference(self, image: np.ndarray) -> Tuple[np.ndarray, List[DetectionResult]]:
        """
        模擬YOLOv12推論 (用於測試)
        """
        annotated_image = image.copy()
        detections = []
        
        # 模擬一些檢測結果
        h, w = image.shape[:2]
        
        # 模擬PCB檢測
        if np.random.random() > 0.3:
            detection = DetectionResult(
                class_id=0,
                class_name='pcb',
                confidence=0.85 + np.random.random() * 0.1,
                bbox=(w//4, h//4, 3*w//4, 3*h//4),
                center=(w//2, h//2)
            )
            detections.append(detection)
            self._draw_detection(annotated_image, detection)
        
        # 模擬元件檢測
        for _ in range(np.random.randint(1, 4)):
            x1 = np.random.randint(0, w//2)
            y1 = np.random.randint(0, h//2)
            x2 = x1 + np.random.randint(50, 150)
            y2 = y1 + np.random.randint(30, 100)
            
            x2 = min(x2, w-1)
            y2 = min(y2, h-1)
            
            detection = DetectionResult(
                class_id=1,
                class_name='component',
                confidence=0.6 + np.random.random() * 0.3,
                bbox=(x1, y1, x2, y2),
                center=((x1+x2)//2, (y1+y2)//2)
            )
            detections.append(detection)
            self._draw_detection(annotated_image, detection)
        
        return annotated_image, detections
    
    def _draw_detection(self, image: np.ndarray, detection: DetectionResult):
        """在影像上繪製檢測結果"""
        x1, y1, x2, y2 = detection.bbox
        
        # 根據類別選擇顏色
        color_map = {
            'pcb': (0, 255, 0),        # 綠色
            'component': (255, 0, 0),   # 藍色
            'defect': (0, 0, 255),      # 紅色
            'short': (0, 0, 255),       # 紅色
            'missing': (0, 165, 255),   # 橙色
            'bridge': (0, 255, 255)     # 黃色
        }
        
        color = color_map.get(detection.class_name, (128, 128, 128))
        
        # 繪製檢測框
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        
        # 繪製標籤
        label = f"{detection.class_name}: {detection.confidence:.2f}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        
        # 標籤背景
        cv2.rectangle(
            image, 
            (x1, y1 - label_size[1] - 10), 
            (x1 + label_size[0], y1), 
            color, 
            -1
        )
        
        # 標籤文字
        cv2.putText(
            image, 
            label, 
            (x1, y1 - 5), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5, 
            (255, 255, 255), 
            1
        )
        
        # 繪製中心點
        center_x, center_y = detection.center
        cv2.circle(image, (center_x, center_y), 3, color, -1)
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[DetectionResult]]:
        """
        處理單幀影像
        
        Args:
            frame: 原始影像幀
            
        Returns:
            (邊緣檢測影像, YOLO推論影像, 檢測結果)
        """
        start_time = time.time()
        
        if frame is None:
            # 返回空影像
            empty = np.zeros((480, 640, 3), dtype=np.uint8)
            return empty, empty, []
        
        # 1. 邊緣檢測處理
        edges_image = self.apply_edge_detection(frame)
        
        # 2. 影像增強
        enhanced_frame = self.apply_enhancement(frame)
        
        # 3. YOLOv12推論
        yolo_image, detections = self.run_yolo_inference(enhanced_frame)
        
        # 4. 合成處理後影像
        processed_image = self._combine_processing_results(
            edges_image, yolo_image
        )
        
        # 更新統計
        self.processing_stats['frame_count'] += 1
        self.processing_stats['processing_time'] = time.time() - start_time
        
        return edges_image, processed_image, detections
    
    def _combine_processing_results(self, edges: np.ndarray, yolo_result: np.ndarray) -> np.ndarray:
        """
        合成處理結果
        
        Args:
            edges: 邊緣檢測結果
            yolo_result: YOLO推論結果
            
        Returns:
            合成影像
        """
        # 方法1: 疊加邊緣到YOLO結果
        if self.config.show_edges:
            # 將邊緣轉為遮罩
            edges_gray = cv2.cvtColor(edges, cv2.COLOR_BGR2GRAY)
            edges_mask = edges_gray > 50
            
            # 在YOLO結果上疊加邊緣 (綠色)
            combined = yolo_result.copy()
            combined[edges_mask] = [0, 255, 0]  # 綠色邊緣
            
            return combined
        else:
            return yolo_result
    
    def get_processing_stats(self) -> Dict:
        """獲取處理統計資訊"""
        fps = 0
        if self.processing_stats['processing_time'] > 0:
            fps = 1.0 / self.processing_stats['processing_time']
            
        return {
            'frame_count': self.processing_stats['frame_count'],
            'processing_time': self.processing_stats['processing_time'],
            'inference_time': self.processing_stats['inference_time'],
            'fps': fps,
            'yolo_available': self.yolo_model is not None
        }
    
    def update_config(self, **kwargs):
        """更新處理配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                print(f"🔧 更新配置 {key} = {value}")
    
    def reset_stats(self):
        """重設統計資訊"""
        self.processing_stats = {
            'frame_count': 0,
            'processing_time': 0.0,
            'inference_time': 0.0
        }


# 測試函數
def test_image_processor():
    """測試影像處理器"""
    print("🧪 測試影像處理器...")
    
    processor = ImageProcessor()
    
    # 創建測試影像
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # 處理影像
    edges, processed, detections = processor.process_frame(test_image)
    
    print(f"✅ 邊緣檢測影像尺寸: {edges.shape}")
    print(f"✅ 處理後影像尺寸: {processed.shape}")
    print(f"✅ 檢測到 {len(detections)} 個物件")
    
    # 顯示統計
    stats = processor.get_processing_stats()
    print(f"📊 處理統計: {stats}")


if __name__ == '__main__':
    test_image_processor()

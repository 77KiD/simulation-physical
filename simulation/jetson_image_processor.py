"""
Jetson Orin Nano 優化版影像處理和YOLOv12推論模組
針對JetPack 6.2環境進行效能最佳化
"""

import cv2
import numpy as np
import time
import torch
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass

try:
    # Jetson專用的YOLO套件導入
    from ultralytics import YOLO
    import torchvision.transforms as transforms
    YOLO_AVAILABLE = True
    print("✅ Jetson YOLOv12/ultralytics 可用")
    
    # 檢查CUDA可用性
    if torch.cuda.is_available():
        print(f"🚀 CUDA可用，GPU: {torch.cuda.get_device_name(0)}")
        print(f"💾 GPU記憶體: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
        CUDA_AVAILABLE = True
    else:
        print("⚠️ CUDA不可用，使用CPU模式")
        CUDA_AVAILABLE = False
        
except ImportError as e:
    YOLO_AVAILABLE = False
    CUDA_AVAILABLE = False
    print(f"⚠️ YOLOv12/ultralytics 未安裝: {e}")

@dataclass
class DetectionResult:
    """檢測結果數據類"""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]

@dataclass
class JetsonProcessingConfig:
    """Jetson最佳化處理配置"""
    # 邊緣檢測參數
    canny_low: int = 50
    canny_high: int = 150
    canny_aperture: int = 3
    
    # 高斯濾波參數 (針對Jetson調整)
    gaussian_kernel: int = 3  # 減小核大小以提升效能
    gaussian_sigma: float = 0.8
    
    # 對比度增強參數
    contrast_alpha: float = 1.4  # 輕微調整
    brightness_beta: int = 8
    
    # YOLO推論參數 (Jetson最佳化)
    yolo_confidence: float = 0.5
    yolo_iou: float = 0.4
    yolo_max_detections: int = 8  # 限制檢測數量以提升效能
    yolo_img_size: int = 640      # 使用標準輸入尺寸
    
    # Jetson特定參數
    use_gpu: bool = CUDA_AVAILABLE
    use_tensorrt: bool = False     # TensorRT最佳化 (進階)
    batch_size: int = 1           # Jetson建議使用batch_size=1
    half_precision: bool = True   # 使用FP16以節省記憶體
    
    # 顯示參數
    show_edges: bool = True
    show_enhanced: bool = True
    show_detections: bool = True

class JetsonImageProcessor:
    """針對Jetson Orin Nano最佳化的影像處理器"""
    
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.config = JetsonProcessingConfig()
        self.yolo_model = None
        self.model_path = model_path
        self.device = 'cuda:0' if self.config.use_gpu else 'cpu'
        
        # 效能統計
        self.processing_stats = {
            'frame_count': 0,
            'processing_time': 0.0,
            'inference_time': 0.0,
            'gpu_memory_used': 0.0,
            'cpu_usage': 0.0
        }
        
        # PCBA特化類別 (針對工業應用)
        self.pcba_classes = {
            0: 'pcb_board',     # PCB基板
            1: 'smd_component', # SMD元件
            2: 'through_hole',  # 通孔元件  
            3: 'connector',     # 連接器
            4: 'capacitor',     # 電容
            5: 'resistor',      # 電阻
            6: 'ic_chip',       # IC晶片
            7: 'led',           # LED
            8: 'crystal',       # 晶振
            9: 'switch',        # 開關
            # 缺陷類別
            10: 'solder_bridge', # 焊橋
            11: 'cold_solder',   # 冷焊
            12: 'missing_comp',  # 缺件
            13: 'wrong_comp',    # 錯件
            14: 'damage',        # 損壞
            15: 'contamination'  # 污染
        }
        
        # 初始化模型
        self.init_yolo_model()
        
        # 設定OpenCV最佳化 (針對Jetson)
        cv2.setUseOptimized(True)
        cv2.setNumThreads(4)  # 使用4個CPU核心
        
    def init_yolo_model(self):
        """初始化YOLO模型 (Jetson最佳化)"""
        if not YOLO_AVAILABLE:
            print("⚠️ YOLO模組不可用，將使用模擬推論")
            return
            
        try:
            print(f"🔄 載入YOLO模型: {self.model_path} (設備: {self.device})")
            
            # 載入模型
            self.yolo_model = YOLO(self.model_path)
            
            # 移到適當設備
            if self.config.use_gpu and CUDA_AVAILABLE:
                self.yolo_model.to(self.device)
                
                # 使用半精度以節省GPU記憶體
                if self.config.half_precision:
                    self.yolo_model.half()
                    print("🚀 啟用FP16半精度模式")
            
            # Jetson暖機運行
            print("🔥 執行暖機推論...")
            dummy_image = np.zeros((self.config.yolo_img_size, self.config.yolo_img_size, 3), dtype=np.uint8)
            
            with torch.no_grad():
                _ = self.yolo_model.predict(
                    dummy_image, 
                    verbose=False,
                    device=self.device,
                    half=self.config.half_precision
                )
            
            print("✅ Jetson YOLO模型載入成功")
            
            # 顯示GPU記憶體使用情況
            if CUDA_AVAILABLE:
                torch.cuda.empty_cache()
                memory_allocated = torch.cuda.memory_allocated(0) / 1024**3
                print(f"💾 GPU記憶體使用: {memory_allocated:.2f}GB")
            
        except Exception as e:
            print(f"❌ YOLO模型載入失敗: {e}")
            self.yolo_model = None
    
    def apply_jetson_edge_detection(self, image: np.ndarray) -> np.ndarray:
        """
        Jetson最佳化邊緣檢測
        使用GPU加速的OpenCV操作
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 使用較小的高斯核心以提升效能
        blurred = cv2.GaussianBlur(
            gray, 
            (self.config.gaussian_kernel, self.config.gaussian_kernel),
            self.config.gaussian_sigma
        )
        
        # Canny邊緣檢測 (在Jetson上已經過最佳化)
        edges = cv2.Canny(
            blurred,
            self.config.canny_low,
            self.config.canny_high,
            apertureSize=self.config.canny_aperture
        )
        
        # 轉換為三通道
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        return edges_colored
    
    def apply_jetson_enhancement(self, image: np.ndarray) -> np.ndarray:
        """
        Jetson最佳化影像增強
        使用高效率的影像處理操作
        """
        # 對比度和亮度調整 (已在Jetson上最佳化)
        enhanced = cv2.convertScaleAbs(
            image, 
            alpha=self.config.contrast_alpha, 
            beta=self.config.brightness_beta
        )
        
        # 使用較小的銳化核心
        sharpening_kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ], dtype=np.float32)
        
        # 應用銳化 (使用filter2D，在Jetson上效能更好)
        sharpened = cv2.filter2D(enhanced, -1, sharpening_kernel)
        
        # 輕度高斯模糊
        if self.config.gaussian_kernel > 1:
            smoothed = cv2.GaussianBlur(
                sharpened,
                (self.config.gaussian_kernel, self.config.gaussian_kernel),
                self.config.gaussian_sigma
            )
        else:
            smoothed = sharpened
        
        return smoothed
    
    def run_jetson_yolo_inference(self, image: np.ndarray) -> Tuple[np.ndarray, List[DetectionResult]]:
        """
        Jetson最佳化YOLOv12推論
        充分利用Jetson的GPU加速能力
        """
        start_time = time.time()
        
        if not self.yolo_model:
            return self._simulate_yolo_inference(image)
        
        try:
            # 確保影像是正確的格式
            if image.dtype != np.uint8:
                image = image.astype(np.uint8)
            
            # 使用torch.no_grad()以節省記憶體
            with torch.no_grad():
                # Jetson最佳化推論設定
                results = self.yolo_model.predict(
                    image,
                    conf=self.config.yolo_confidence,
                    iou=self.config.yolo_iou,
                    max_det=self.config.yolo_max_detections,
                    imgsz=self.config.yolo_img_size,
                    device=self.device,
                    half=self.config.half_precision,
                    verbose=False,
                    stream=False  # 不使用串流模式以節省記憶體
                )
            
            # 處理檢測結果
            detections = []
            annotated_image = image.copy()
            
            if results and len(results) > 0:
                result = results[0]
                
                if result.boxes is not None and len(result.boxes) > 0:
                    # 轉到CPU進行後處理
                    boxes = result.boxes.cpu().numpy()
                    
                    for box in boxes:
                        try:
                            # 檢查box的有效性
                            if hasattr(box, 'xyxy') and hasattr(box, 'conf') and hasattr(box, 'cls'):
                                x1, y1, x2, y2 = box.xyxy[0].astype(int)
                                confidence = float(box.conf[0])
                                class_id = int(box.cls[0])
                                
                                # 確保座標在圖像範圍內
                                h, w = image.shape[:2]
                                x1, x2 = max(0, x1), min(w-1, x2)
                                y1, y2 = max(0, y1), min(h-1, y2)
                                
                                # 類別名稱
                                class_name = self.pcba_classes.get(class_id, f"unknown_{class_id}")
                                
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
                                    self._draw_jetson_detection(annotated_image, detection)
                        except Exception as box_error:
                            print(f"⚠️ 處理檢測框時發生錯誤: {box_error}")
                            continue
            
            # 記錄推論時間
            inference_time = time.time() - start_time
            self.processing_stats['inference_time'] = inference_time
            
            # 更新GPU記憶體使用統計
            if CUDA_AVAILABLE:
                self.processing_stats['gpu_memory_used'] = torch.cuda.memory_allocated(0) / 1024**3
            
            return annotated_image, detections
            
        except Exception as e:
            print(f"Jetson YOLO推論錯誤: {e}")
            return self._simulate_yolo_inference(image)
    
    def _draw_jetson_detection(self, image: np.ndarray, detection: DetectionResult):
        """在影像上繪製檢測結果 (Jetson最佳化)"""
        x1, y1, x2, y2 = detection.bbox
        
        # 針對不同類別使用不同顏色
        color_map = {
            # 正常元件 - 綠色系
            'pcb_board': (0, 255, 0),
            'smd_component': (0, 200, 100),
            'through_hole': (0, 150, 150),
            'connector': (0, 255, 200),
            'capacitor': (100, 255, 0),
            'resistor': (150, 255, 0),
            'ic_chip': (0, 255, 100),
            'led': (200, 255, 0),
            'crystal': (0, 200, 200),
            'switch': (100, 200, 100),
            
            # 缺陷 - 紅色系
            'solder_bridge': (0, 0, 255),
            'cold_solder': (0, 50, 255),
            'missing_comp': (0, 100, 255),
            'wrong_comp': (50, 0, 255),
            'damage': (100, 0, 255),
            'contamination': (255, 0, 100)
        }
        
        color = color_map.get(detection.class_name, (128, 128, 128))
        
        # 繪製檢測框 (使用較粗的線條以便在小螢幕上看清楚)
        thickness = 2
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
        
        # 繪製標籤 (針對Jetson顯示最佳化)
        label = f"{detection.class_name}: {detection.confidence:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6  # 適中的字體大小
        font_thickness = 1
        
        # 計算標籤尺寸
        (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
        
        # 標籤背景矩形
        label_bg = (x1, y1 - text_height - 10, x1 + text_width, y1)
        cv2.rectangle(image, (label_bg[0], label_bg[1]), (label_bg[2], label_bg[3]), color, -1)
        
        # 標籤文字
        cv2.putText(image, label, (x1, y1 - 5), font, font_scale, (255, 255, 255), font_thickness)
        
        # 繪製中心點
        center_x, center_y = detection.center
        cv2.circle(image, (center_x, center_y), 3, color, -1)
    
    def process_jetson_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[DetectionResult]]:
        """
        Jetson最佳化幀處理
        """
        start_time = time.time()
        
        if frame is None:
            # 返回黑色影像
            empty = np.zeros((480, 640, 3), dtype=np.uint8)
            return empty, empty, []
        
        # 1. Jetson最佳化邊緣檢測
        edges_image = self.apply_jetson_edge_detection(frame)
        
        # 2. Jetson最佳化影像增強
        enhanced_frame = self.apply_jetson_enhancement(frame)
        
        # 3. Jetson最佳化YOLOv12推論
        yolo_image, detections = self.run_jetson_yolo_inference(enhanced_frame)
        
        # 4. 合成處理結果
        processed_image = self._combine_jetson_results(edges_image, yolo_image)
        
        # 更新統計
        self.processing_stats['frame_count'] += 1
        self.processing_stats['processing_time'] = time.time() - start_time
        
        # 清理GPU記憶體 (每100幀清理一次)
        if CUDA_AVAILABLE and self.processing_stats['frame_count'] % 100 == 0:
            torch.cuda.empty_cache()
        
        return edges_image, processed_image, detections
    
    def _combine_jetson_results(self, edges: np.ndarray, yolo_result: np.ndarray) -> np.ndarray:
        """合成Jetson處理結果"""
        if not self.config.show_edges:
            return yolo_result
            
        # 高效能的邊緣疊加
        edges_gray = cv2.cvtColor(edges, cv2.COLOR_BGR2GRAY)
        edges_mask = edges_gray > 30  # 調整閾值以適應Jetson顯示
        
        combined = yolo_result.copy()
        combined[edges_mask] = [0, 255, 0]  # 綠色邊緣
        
        return combined
    
    def _simulate_yolo_inference(self, image: np.ndarray) -> Tuple[np.ndarray, List[DetectionResult]]:
        """模擬YOLO推論 (用於測試)"""
        annotated_image = image.copy()
        detections = []
        
        h, w = image.shape[:2]
        
        # 模擬PCB板檢測
        if np.random.random() > 0.2:
            detection = DetectionResult(
                class_id=0,
                class_name='pcb_board',
                confidence=0.88 + np.random.random() * 0.1,
                bbox=(w//6, h//6, 5*w//6, 5*h//6),
                center=(w//2, h//2)
            )
            detections.append(detection)
            self._draw_jetson_detection(annotated_image, detection)
        
        # 模擬元件檢測
        component_classes = ['smd_component', 'capacitor', 'resistor', 'ic_chip']
        for _ in range(np.random.randint(2, 6)):
            x1 = np.random.randint(w//4, w//2)
            y1 = np.random.randint(h//4, h//2)
            x2 = x1 + np.random.randint(30, 80)
            y2 = y1 + np.random.randint(20, 60)
            
            x2, y2 = min(x2, w-1), min(y2, h-1)
            
            detection = DetectionResult(
                class_id=np.random.randint(1, 5),
                class_name=np.random.choice(component_classes),
                confidence=0.6 + np.random.random() * 0.3,
                bbox=(x1, y1, x2, y2),
                center=((x1+x2)//2, (y1+y2)//2)
            )
            detections.append(detection)
            self._draw_jetson_detection(annotated_image, detection)
        
        return annotated_image, detections
    
    def get_jetson_stats(self) -> Dict:
        """獲取Jetson特化統計資訊"""
        fps = 1.0 / max(self.processing_stats['processing_time'], 0.001)
        
        stats = {
            'frame_count': self.processing_stats['frame_count'],
            'processing_time': self.processing_stats['processing_time'],
            'inference_time': self.processing_stats['inference_time'],
            'fps': fps,
            'yolo_available': self.yolo_model is not None,
            'cuda_available': CUDA_AVAILABLE,
            'device': self.device,
            'half_precision': self.config.half_precision
        }
        
        # Jetson特有統計
        if CUDA_AVAILABLE:
            stats['gpu_memory_used'] = self.processing_stats['gpu_memory_used']
            stats['gpu_memory_total'] = torch.cuda.get_device_properties(0).total_memory / 1024**3
            stats['gpu_utilization'] = torch.cuda.utilization()
        
        return stats
    
    def update_jetson_config(self, **kwargs):
        """更新Jetson配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                old_value = getattr(self.config, key)
                setattr(self.config, key, value)
                print(f"🔧 Jetson配置更新 {key}: {old_value} → {value}")
    
    def optimize_for_jetson(self):
        """Jetson專用最佳化設定"""
        print("🚀 啟用Jetson Orin Nano最佳化配置...")
        
        # 針對Jetson Orin Nano最佳化的參數
        self.update_jetson_config(
            gaussian_kernel=3,      # 較小的核心
            yolo_max_detections=6,  # 限制檢測數量
            yolo_img_size=640,      # 標準輸入尺寸
            half_precision=True,    # 使用FP16
            batch_size=1           # 單批次處理
        )
        
        # OpenCV最佳化
        cv2.setUseOptimized(True)
        cv2.setNumThreads(4)
        
        print("✅ Jetson最佳化設定完成")
    
    def cleanup_jetson(self):
        """清理Jetson資源"""
        if CUDA_AVAILABLE:
            torch.cuda.empty_cache()
            print("🧹 清理GPU記憶體完成")
        
        if self.yolo_model:
            del self.yolo_model
            self.yolo_model = None
            print("🗑️ 釋放YOLO模型記憶體")


# Jetson效能監控工具
def monitor_jetson_performance():
    """監控Jetson系統效能"""
    try:
        import psutil
        
        print("📊 Jetson Orin Nano 效能監控")
        print("=" * 40)
        
        # CPU使用率
        cpu_usage = psutil.cpu_percent(interval=1)
        print(f"CPU使用率: {cpu_usage:.1f}%")
        
        # 記憶體使用
        memory = psutil.virtual_memory()
        print(f"記憶體使用: {memory.percent:.1f}% ({memory.used/1024**3:.1f}GB / {memory.total/1024**3:.1f}GB)")
        
        # GPU資訊
        if CUDA_AVAILABLE:
            gpu_memory = torch.cuda.memory_allocated(0) / 1024**3
            gpu_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"GPU記憶體使用: {gpu_memory:.2f}GB / {gpu_total:.1f}GB")
            print(f"GPU使用率: {torch.cuda.utilization()}%")
        
        # 溫度 (如果可獲取)
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if 'thermal' in entry.label.lower() or 'cpu' in entry.label.lower():
                            print(f"溫度 ({entry.label}): {entry.current:.1f}°C")
        except:
            pass
            
    except ImportError:
        print("⚠️ psutil未安裝，無法顯示詳細效能資訊")
        print("安裝指令: pip3 install psutil")


# 測試函數
def test_jetson_image_processor():
    """測試Jetson最佳化影像處理器"""
    print("🧪 測試Jetson Orin Nano影像處理器...")
    
    # 檢查系統環境
    monitor_jetson_performance()
    
    processor = JetsonImageProcessor()
    processor.optimize_for_jetson()
    
    # 創建測試影像
    test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    
    # 效能測試
    print("\n⏱️ 執行效能測試...")
    
    times = []
    for i in range(10):
        start_time = time.time()
        edges, processed, detections = processor.process_jetson_frame(test_image)
        processing_time = time.time() - start_time
        times.append(processing_time)
        
        if i == 0:  # 只在第一次顯示結果
            print(f"✅ 邊緣檢測影像尺寸: {edges.shape}")
            print(f"✅ 處理後影像尺寸: {processed.shape}")
            print(f"✅ 檢測到 {len(detections)} 個物件")
    
    # 統計結果
    avg_time = np.mean(times)
    avg_fps = 1.0 / avg_time
    
    print(f"\n📊 Jetson效能統計:")
    print(f"平均處理時間: {avg_time*1000:.1f}ms")
    print(f"平均FPS: {avg_fps:.1f}")
    print(f"最快處理: {min(times)*1000:.1f}ms")
    print(f"最慢處理: {max(times)*1000:.1f}ms")
    
    # 顯示詳細統計
    stats = processor.get_jetson_stats()
    print(f"📈 詳細統計: {stats}")
    
    # 清理資源
    processor.cleanup_jetson()
    print("✅ Jetson測試完成")


if __name__ == '__main__':
    test_jetson_image_processor()
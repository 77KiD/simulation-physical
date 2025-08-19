"""
簡化版資料管理模組 - 修復版本
添加了缺失的datetime導入
"""

import json
import os
from datetime import datetime  # 添加缺失的導入
from dataclasses import dataclass, asdict
from typing import List, Dict

@dataclass
class DetectionRecord:
    timestamp: str
    result: str
    defect_type: str = ""
    confidence: float = 0.0
    action: str = ""

class Statistics:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.total_count = 0
        self.pass_count = 0
        self.defect_count = 0
        self.short_count = 0
        self.open_count = 0
        self.bridge_count = 0
        self.missing_count = 0
    
    def update_with_result(self, result: str, defect_type: str = ""):
        self.total_count += 1
        if result == "合格":
            self.pass_count += 1
        else:
            self.defect_count += 1
            if defect_type == "短路":
                self.short_count += 1
            elif defect_type == "斷路":
                self.open_count += 1
            elif defect_type == "橋接":
                self.bridge_count += 1
            elif defect_type == "缺件":
                self.missing_count += 1
    
    def get_pass_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return (self.pass_count / self.total_count) * 100
    
    def get_defect_distribution(self) -> dict:
        return {
            "短路": self.short_count,
            "斷路": self.open_count,
            "橋接": self.bridge_count,
            "缺件": self.missing_count
        }

class DataManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.records = []
        self.statistics = Statistics()
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def add_record(self, result: str, defect_type: str = "", confidence: float = 0.0):
        action = "✅ 入庫" if result == "合格" else "⚠️ 出庫"
        
        record = DetectionRecord(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            result=result,
            defect_type=defect_type,
            confidence=confidence,
            action=action
        )
        
        self.records.append(record)
        self.statistics.update_with_result(result, defect_type)
        
        return record
    
    def get_statistics(self):
        return self.statistics

    def get_recent_records(self, limit: int = 50):
        """取得最近的檢測記錄"""
        return self.records[-limit:]

    def clear_records(self):
        self.records.clear()
        self.statistics.reset()
    
    def export_report(self, file_path: str = None) -> str:
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"PCBA_Report_{timestamp}.txt"
        
        try:
            content = f"""PCBA檢測報告
生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
總檢測數: {self.statistics.total_count}
合格數: {self.statistics.pass_count}
缺陷數: {self.statistics.defect_count}
合格率: {self.statistics.get_pass_rate():.1f}%

缺陷分析:
- 短路: {self.statistics.short_count}
- 斷路: {self.statistics.open_count}
- 橋接: {self.statistics.bridge_count}
- 缺件: {self.statistics.missing_count}

詳細記錄:
"""
            
            # 添加最近50條記錄
            recent_records = self.get_recent_records(50)
            for record in recent_records:
                content += f"{record.timestamp} | {record.result} | {record.defect_type or '-'} | {record.confidence:.2f} | {record.action}\n"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return file_path
        except Exception as e:
            print(f"匯出失敗: {e}")
            return ""
    
    def export_csv(self, file_path: str = None) -> str:
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"PCBA_Records_{timestamp}.csv"
        
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['時間', '結果', '缺陷類型', '信心度', '動作']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for record in self.records:
                    writer.writerow({
                        '時間': record.timestamp,
                        '結果': record.result,
                        '缺陷類型': record.defect_type or '-',
                        '信心度': f"{record.confidence:.2f}",
                        '動作': record.action
                    })
            
            return file_path
        except Exception as e:
            print(f"CSV匯出失敗: {e}")
            return ""
    
    def save_to_json(self, file_path: str = None) -> bool:
        """保存記錄到JSON檔案"""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(self.data_dir, f"records_{timestamp}.json")
        
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'statistics': {
                    'total_count': self.statistics.total_count,
                    'pass_count': self.statistics.pass_count,
                    'defect_count': self.statistics.defect_count,
                    'pass_rate': self.statistics.get_pass_rate(),
                    'defect_distribution': self.statistics.get_defect_distribution()
                },
                'records': [asdict(record) for record in self.records]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"記錄已保存到: {file_path}")
            return True
        except Exception as e:
            print(f"保存記錄失敗: {e}")
            return False
    
    def load_from_json(self, file_path: str) -> bool:
        """從JSON檔案載入記錄"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 清空現有記錄
            self.clear_records()
            
            # 載入記錄
            for record_data in data.get('records', []):
                record = DetectionRecord(**record_data)
                self.records.append(record)
                self.statistics.update_with_result(record.result, record.defect_type)
            
            print(f"從 {file_path} 載入了 {len(self.records)} 條記錄")
            return True
        except Exception as e:
            print(f"載入記錄失敗: {e}")
            return False
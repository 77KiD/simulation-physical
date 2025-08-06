"""
簡化版資料管理模組
"""

import json
import os
from datetime import datetime
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
"""
            
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

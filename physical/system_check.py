#!/usr/bin/env python3
"""
系統檢查工具
檢查環境和檔案完整性，提供修復建議
"""

import os
import sys
import subprocess

def check_python_packages():
    """檢查Python套件"""
    print("📦 檢查Python套件...")
    
    required_packages = {
        'PyQt5': 'PyQt5',
        'cv2': 'opencv-python', 
        'numpy': 'numpy'
    }
    
    missing_packages = []
    problematic_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            if import_name == 'cv2':
                import cv2
                print(f"  ✅ OpenCV: {cv2.__version__}")
            elif import_name == 'numpy':
                import numpy as np
                print(f"  ✅ NumPy: {np.__version__}")
            elif import_name == 'PyQt5':
                from PyQt5.QtWidgets import QApplication
                print(f"  ✅ PyQt5: 已安裝")
                
        except ImportError as e:
            print(f"  ❌ {package_name}: 未安裝 - {e}")
            missing_packages.append(package_name)
        except Exception as e:
            print(f"  ⚠️  {package_name}: 有問題 - {e}")
            problematic_packages.append(package_name)
    
    return missing_packages, problematic_packages

def check_core_files():
    """檢查核心檔案"""
    print("\n📁 檢查核心檔案...")
    
    core_files = {
        'main_ui.py': '主界面程式',
        'hardware_controller.py': '硬體控制模組',
        'detection_engine.py': '檢測引擎模組', 
        'data_manager.py': '資料管理模組',
        'config_manager.py': '配置管理模組'
    }
    
    missing_files = []
    
    for filename, description in core_files.items():
        if os.path.exists(filename):
            # 檢查檔案大小
            size = os.path.getsize(filename)
            if size > 100:  # 至少100 bytes
                print(f"  ✅ {filename} ({description}) - {size} bytes")
            else:
                print(f"  ⚠️  {filename} ({description}) - 檔案太小 ({size} bytes)")
                missing_files.append(filename)
        else:
            print(f"  ❌ {filename} ({description}) - 檔案不存在")
            missing_files.append(filename)
    
    return missing_files

def check_optional_files():
    """檢查可選檔案"""
    print("\n🤖 檢查機械手臂相關檔案...")
    
    optional_files = {
        'robotic_arm_controller.py': '六軸機械手臂控制核心',
        'arm_control_ui.py': '機械手臂控制界面',
        'run.py': '啟動腳本'
    }
    
    for filename, description in optional_files.items():
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"  ✅ {filename} ({description}) - {size} bytes")
        else:
            print(f"  ⚠️  {filename} ({description}) - 檔案不存在 (可選)")

def create_minimal_files():
    """創建基本的缺失檔案"""
    print("\n🔧 創建基本的缺失檔案...")
    
    # 創建基本的 data_manager.py
    if not os.path.exists('data_manager.py'):
        data_manager_code = '''"""
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
'''
        
        with open('data_manager.py', 'w', encoding='utf-8') as f:
            f.write(data_manager_code)
        print("  ✅ 已創建 data_manager.py")

def fix_numpy_issue():
    """嘗試修復NumPy問題"""
    print("\n🔧 嘗試修復NumPy問題...")
    
    try:
        import numpy as np
        print(f"  ✅ NumPy已正常: {np.__version__}")
        return True
    except ImportError as e:
        print(f"  ❌ NumPy導入失敗: {e}")
        
        print("  🔄 嘗試重新安裝NumPy...")
        try:
            # 嘗試重新安裝
            subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', 'numpy', '-y'])
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'numpy==1.24.3'])
            
            import numpy as np
            print(f"  ✅ NumPy修復成功: {np.__version__}")
            return True
        except Exception as repair_error:
            print(f"  ❌ 自動修復失敗: {repair_error}")
            return False

def provide_solutions(missing_packages, problematic_packages, missing_files):
    """提供解決方案"""
    print("\n💡 解決方案建議:")
    
    if missing_packages or problematic_packages:
        print("\n📦 套件問題解決:")
        
        if 'numpy' in (missing_packages + problematic_packages):
            print("  NumPy問題解決方案:")
            print("    1. pip uninstall numpy")
            print("    2. pip install numpy==1.24.3")
            print("    3. 或使用: conda install numpy=1.24.3")
        
        if missing_packages:
            print(f"\n  安裝缺失套件:")
            print(f"    pip install {' '.join(missing_packages)}")
    
    if missing_files:
        print(f"\n📁 缺失檔案解決:")
        print("  請確保以下檔案存在於當前目錄:")
        for file in missing_files:
            print(f"    - {file}")
        print("  如需要檔案，請從完整的程式包中複製。")

def main():
    print("🔍 PCBA系統檢查工具")
    print("=" * 50)
    
    print(f"Python版本: {sys.version}")
    print(f"當前目錄: {os.getcwd()}")
    
    # 檢查套件
    missing_packages, problematic_packages = check_python_packages()
    
    # 嘗試修復NumPy
    if 'numpy' in (missing_packages + problematic_packages):
        fix_numpy_issue()
    
    # 檢查檔案
    missing_files = check_core_files()
    check_optional_files()
    
    # 創建缺失的基本檔案
    if missing_files:
        create_minimal_files()
    
    # 提供解決方案
    provide_solutions(missing_packages, problematic_packages, missing_files)
    
    # 最終狀態
    print("\n" + "=" * 50)
    if not missing_packages and not problematic_packages and not missing_files:
        print("✅ 系統檢查完成 - 一切正常!")
        print("可以運行: python main_ui.py")
    else:
        print("⚠️  發現問題，請按照上述建議解決。")
    
    input("\n按Enter鍵結束...")

if __name__ == '__main__':
    main()

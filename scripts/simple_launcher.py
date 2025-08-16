#!/usr/bin/env python
"""
PCBA系統簡單啟動器
自動檢測並啟動適當的程式
"""

import os
import sys
import subprocess
from pathlib import Path

def find_main_script():
    """尋找主程式腳本"""
    possible_scripts = [
        "simulation/main_ui.py",
        "simulation/run_script.py", 
        "launcher_app.py"
    ]
    
    for script in possible_scripts:
        if Path(script).exists():
            return script
    
    return None

def main():
    print("🚀 PCBA檢測系統啟動器")
    print("=" * 40)
    
    # 尋找可執行腳本
    main_script = find_main_script()
    
    if main_script:
        print(f"✅ 找到主程式: {main_script}")
        print("🔄 正在啟動...")
        
        try:
            # 啟動主程式
            subprocess.run([sys.executable, main_script])
        except KeyboardInterrupt:
            print("\n⏹️  程式已中斷")
        except Exception as e:
            print(f"❌ 啟動失敗: {e}")
    else:
        print("❌ 未找到可執行的主程式")
        print("請檢查以下檔案是否存在:")
        print("  - simulation/main_ui.py")
        print("  - simulation/run_script.py")
        print("  - launcher_app.py")

if __name__ == "__main__":
    main()

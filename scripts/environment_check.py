#!/usr/bin/env python
"""
PCBA環境檢查工具
檢查Python環境和依賴套件
"""

import sys
import platform
import subprocess

def check_python_version():
    """檢查Python版本"""
    version = sys.version_info
    print(f"🐍 Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python版本符合要求 (3.8+)")
        return True
    else:
        print("❌ Python版本過低，建議使用Python 3.8或更高版本")
        return False

def check_packages():
    """檢查必要套件"""
    required_packages = {
        'numpy': 'NumPy',
        'cv2': 'OpenCV',
        'PyQt5': 'PyQt5'
    }
    
    results = {}
    print("\n📦 檢查基礎套件:")
    
    for package, name in required_packages.items():
        try:
            if package == 'cv2':
                import cv2
                print(f"✅ {name}: {cv2.__version__}")
            elif package == 'numpy':
                import numpy as np
                print(f"✅ {name}: {np.__version__}")
            elif package == 'PyQt5':
                from PyQt5.QtWidgets import QApplication
                from PyQt5.QtCore import QT_VERSION_STR
                print(f"✅ {name}: {QT_VERSION_STR}")
            results[package] = True
        except ImportError:
            print(f"❌ {name}: 未安裝")
            results[package] = False
        except Exception as e:
            print(f"⚠️  {name}: 載入異常 - {e}")
            results[package] = False
    
    return results

def check_optional_packages():
    """檢查可選套件"""
    optional_packages = {
        'torch': 'PyTorch',
        'ultralytics': 'YOLOv8/Ultralytics'
    }
    
    print("\n🔬 檢查AI套件 (可選):")
    
    for package, name in optional_packages.items():
        try:
            if package == 'torch':
                import torch
                print(f"✅ {name}: {torch.__version__}")
            elif package == 'ultralytics':
                import ultralytics
                print(f"✅ {name}: 已安裝")
        except ImportError:
            print(f"⚠️  {name}: 未安裝 (可選)")

def main():
    print("🔍 PCBA環境檢查工具")
    print("=" * 40)
    
    # 系統資訊
    print(f"💻 作業系統: {platform.system()} {platform.release()}")
    print(f"🏗️  架構: {platform.machine()}")
    
    # Python檢查
    python_ok = check_python_version()
    
    # 套件檢查
    packages = check_packages()
    check_optional_packages()
    
    # 總結
    print("\n" + "=" * 40)
    print("📊 檢查結果:")
    
    missing_packages = [pkg for pkg, installed in packages.items() if not installed]
    
    if python_ok and not missing_packages:
        print("✅ 環境檢查完全通過！")
        print("🚀 可以開始使用PCBA檢測系統")
    else:
        print("⚠️  環境需要改善:")
        if not python_ok:
            print("  - 請升級Python到3.8或更高版本")
        if missing_packages:
            print("  - 請安裝缺失的套件:")
            print(f"    pip install {' '.join(missing_packages)}")
    
    print("\n💡 完整安裝指令:")
    print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()

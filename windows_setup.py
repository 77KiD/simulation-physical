#!/usr/bin/env python
"""
Windows專用PCBA專案設置腳本
適用於 C:\PCBAsimulations 目錄
"""

import os
import sys
import json
from pathlib import Path

def print_header():
    """打印標題"""
    print("=" * 60)
    print("🔧 PCBA檢測系統 - Windows設置工具")
    print("=" * 60)
    print(f"📁 當前目錄: {os.getcwd()}")
    print(f"🐍 Python版本: {sys.version.split()[0]}")
    print()

def check_existing_structure():
    """檢查現有結構"""
    print("🔍 檢查現有專案結構...")
    
    existing_items = {
        "launcher_app.py": "✅ 主啟動器",
        "simulation/": "✅ 模擬模式目錄", 
        "data/": "✅ 資料目錄",
        "physical/": "✅ 實體模式目錄",
        "logs/": "✅ 日誌目錄"
    }
    
    for item, description in existing_items.items():
        if os.path.exists(item):
            print(f"{description}")
        else:
            print(f"❌ 缺少: {item}")
    
    print()

def create_new_directories():
    """創建新的目錄結構"""
    print("📁 創建新的目錄結構...")
    
    new_directories = [
        "core",
        "config", 
        "scripts",
        "ui",
        "ui/widgets",
        "ai",
        "tests",
        "utils",
        "docs",
        "data/images",
        "data/models",
        "data/exports"
    ]
    
    created_count = 0
    existing_count = 0
    
    for directory in new_directories:
        dir_path = Path(directory)
        if dir_path.exists():
            print(f"⚠️  已存在: {directory}")
            existing_count += 1
        else:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ 創建: {directory}")
                created_count += 1
            except Exception as e:
                print(f"❌ 創建失敗 {directory}: {e}")
    
    print(f"\n📊 結果: 新創建 {created_count} 個，已存在 {existing_count} 個目錄")
    return created_count

def create_python_modules():
    """創建Python模組檔案"""
    print("\n📄 創建Python模組檔案...")
    
    modules = {
        "core/__init__.py": '''"""
PCBA系統核心模組
提供硬體抽象、配置管理等基礎功能
"""

__version__ = "2.0.0"
__author__ = "PCBA Team"

print("✅ PCBA核心模組已載入")
''',
        "scripts/__init__.py": '"""PCBA工具腳本模組"""\n',
        "ui/__init__.py": '"""PCBA用戶界面模組"""\n',
        "ai/__init__.py": '"""PCBA AI模組"""\n',
        "tests/__init__.py": '"""PCBA測試模組"""\n',
        "utils/__init__.py": '"""PCBA工具函數模組"""\n'
    }
    
    created_count = 0
    for file_path, content in modules.items():
        try:
            path = Path(file_path)
            if not path.exists():
                path.write_text(content, encoding='utf-8')
                print(f"✅ 創建: {file_path}")
                created_count += 1
            else:
                print(f"⚠️  已存在: {file_path}")
        except Exception as e:
            print(f"❌ 創建失敗 {file_path}: {e}")
    
    print(f"📊 創建了 {created_count} 個模組檔案")
    return created_count

def create_configuration_files():
    """創建配置檔案"""
    print("\n⚙️ 創建配置檔案...")
    
    # 硬體配置
    hardware_config = {
        "platform": "windows",
        "simulation_mode": True,
        "gpio": {
            "motor_in1": 18,
            "motor_in2": 19,
            "motor_in3": 20,
            "motor_in4": 21,
            "motor_ena": 12,
            "motor_enb": 13,
            "sensor_pin": 24,
            "relay_pin": 25
        },
        "camera": {
            "index": 0,
            "width": 640,
            "height": 480,
            "fps": 30
        },
        "robotic_arm": {
            "enabled": False,
            "simulation_mode": True,
            "channels": [0, 1, 2, 3, 4, 5]
        }
    }
    
    # UI配置
    ui_config = {
        "window": {
            "width": 1400,
            "height": 900,
            "title": "PCBA檢測系統 v2.0"
        },
        "theme": "default",
        "font": {
            "family": "Microsoft JhengHei",
            "size": 9
        },
        "language": "zh-TW"
    }
    
    # 檢測配置
    detection_config = {
        "threshold": 0.8,
        "yolo": {
            "model_path": "data/models/yolov8n.pt",
            "confidence": 0.5,
            "iou": 0.4
        },
        "processing": {
            "delay": 0.1,
            "max_records": 10000
        }
    }
    
    configs = {
        "config/hardware_config.json": hardware_config,
        "config/ui_config.json": ui_config,
        "config/detection_config.json": detection_config
    }
    
    created_count = 0
    for file_path, config_data in configs.items():
        try:
            path = Path(file_path)
            if not path.exists():
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                print(f"✅ 創建: {file_path}")
                created_count += 1
            else:
                print(f"⚠️  已存在: {file_path}")
        except Exception as e:
            print(f"❌ 創建失敗 {file_path}: {e}")
    
    print(f"📊 創建了 {created_count} 個配置檔案")
    return created_count

def create_requirements_file():
    """創建requirements.txt"""
    print("\n📋 創建requirements.txt...")
    
    requirements_content = """# PCBA檢測系統依賴套件清單
# 安裝指令: pip install -r requirements.txt

# 基礎套件
numpy>=1.21.0
opencv-python>=4.5.0
PyQt5>=5.15.0

# AI和機器學習
torch>=1.9.0
torchvision>=0.10.0
ultralytics>=8.0.0

# 資料處理和分析
pandas>=1.3.0
matplotlib>=3.4.0
pillow>=8.0.0

# 硬體控制套件 (可選 - 僅在有實際硬體時需要)
# 註解掉的套件需要時手動安裝
# adafruit-circuitpython-pca9685>=3.4.0
# adafruit-circuitpython-motor>=3.4.0
# adafruit-blinka>=6.0.0

# Jetson專用套件 (僅Jetson平台)
# Jetson.GPIO>=2.0.0

# 開發和測試工具
pytest>=6.0.0
pytest-qt>=4.0.0

# 代碼品質工具
black>=21.0.0
flake8>=3.9.0

# 文檔生成
sphinx>=4.0.0
"""
    
    try:
        req_path = Path("requirements.txt")
        if not req_path.exists():
            req_path.write_text(requirements_content, encoding='utf-8')
            print("✅ 創建 requirements.txt")
            return True
        else:
            print("⚠️  requirements.txt 已存在")
            return False
    except Exception as e:
        print(f"❌ 創建requirements.txt失敗: {e}")
        return False

def create_utility_scripts():
    """創建實用工具腳本"""
    print("\n🛠️ 創建工具腳本...")
    
    # 環境檢查腳本
    env_checker_content = '''#!/usr/bin/env python
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
    print("\\n📦 檢查基礎套件:")
    
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
    
    print("\\n🔬 檢查AI套件 (可選):")
    
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
    print("\\n" + "=" * 40)
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
    
    print("\\n💡 完整安裝指令:")
    print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()
'''
    
    # 簡單啟動器
    simple_launcher_content = '''#!/usr/bin/env python
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
            print("\\n⏹️  程式已中斷")
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
'''
    
    scripts = {
        "scripts/environment_check.py": env_checker_content,
        "scripts/simple_launcher.py": simple_launcher_content
    }
    
    created_count = 0
    for file_path, content in scripts.items():
        try:
            path = Path(file_path)
            if not path.exists():
                path.write_text(content, encoding='utf-8')
                print(f"✅ 創建: {file_path}")
                created_count += 1
            else:
                print(f"⚠️  已存在: {file_path}")
        except Exception as e:
            print(f"❌ 創建失敗 {file_path}: {e}")
    
    print(f"📊 創建了 {created_count} 個工具腳本")
    return created_count

def create_readme():
    """創建README.md"""
    print("\n📖 創建README.md...")
    
    readme_content = '''# PCBA檢測系統 v2.0

🔧 基於AI的印刷電路板自動檢測系統

## 🚀 快速開始

### 1. 安裝依賴套件
```bash
pip install -r requirements.txt
```

### 2. 檢查環境
```bash
python scripts/environment_check.py
```

### 3. 啟動系統
```bash
python scripts/simple_launcher.py
```

或使用原始啟動器：
```bash
python launcher_app.py
```

## 📁 專案結構

```
PCBAsimulations/
├── 📄 launcher_app.py           # 原始啟動器
├── 📄 requirements.txt          # 依賴套件清單
├── 📁 core/                     # 核心模組
├── 📁 simulation/               # 模擬模式
├── 📁 config/                   # 配置檔案
├── 📁 scripts/                  # 工具腳本
├── 📁 data/                     # 資料檔案
└── 📁 ui/                       # 用戶界面組件
```

## 🛠️ 功能特色

- 🤖 **AI檢測**: YOLOv8/YOLOv12 物件偵測
- 🖥️ **圖形界面**: PyQt5 現代化界面
- 🦾 **機械手臂**: 六軸機械手臂控制
- 📊 **資料分析**: 即時統計和報告
- 🔄 **雙模式**: 模擬和實體硬體模式
- 🌐 **跨平台**: Windows/Linux/Jetson支援

## 📋 系統需求

- **Python**: 3.8或更高版本
- **作業系統**: Windows 10/11, Linux, Jetson
- **記憶體**: 建議4GB以上
- **硬碟空間**: 2GB以上

### 必要套件
- OpenCV 4.5+
- PyQt5 5.15+
- NumPy 1.21+

### 可選套件 (AI功能)
- PyTorch 1.9+
- Ultralytics 8.0+

## 🔧 硬體支援

- **相機**: USB網路攝影機
- **控制器**: Jetson Orin Nano
- **PWM控制**: PCA9685
- **伺服馬達**: MG996R
- **感測器**: TCRT5000光電感測器

## 📚 使用說明

1. **模擬模式**: 無需實際硬體，用於開發和測試
2. **實體模式**: 連接實際硬體進行生產檢測
3. **AI檢測**: 使用訓練好的模型進行缺陷檢測
4. **資料管理**: 自動儲存檢測記錄和統計

## 🆘 故障排除

### 常見問題

**Q: 提示套件未安裝**
A: 執行 `pip install -r requirements.txt`

**Q: 相機無法啟動**
A: 檢查相機連接，確認沒有其他程式佔用

**Q: PyQt5安裝失敗**
A: 嘗試 `pip install PyQt5 --user`

### 取得協助

- 📧 檢查logs/目錄中的錯誤日誌
- 🔍 運行環境檢查: `python scripts/environment_check.py`
- 📋 提交Issue或聯繫開發團隊

## 📄 授權

MIT License - 詳見LICENSE檔案

## 🤝 貢獻

歡迎提交Issue和Pull Request！

---
*最後更新: 2025-08-16*
'''
    
    try:
        readme_path = Path("README.md")
        if not readme_path.exists():
            readme_path.write_text(readme_content, encoding='utf-8')
            print("✅ 創建 README.md")
            return True
        else:
            print("⚠️  README.md 已存在")
            return False
    except Exception as e:
        print(f"❌ 創建README.md失敗: {e}")
        return False

def print_summary_and_next_steps():
    """打印總結和後續步驟"""
    print("\n" + "=" * 60)
    print("🎉 PCBA專案設置完成！")
    print("=" * 60)
    print()
    print("📋 已創建的內容:")
    print("✅ 目錄結構 (core, config, scripts, ui, ai等)")
    print("✅ Python模組檔案 (__init__.py)")
    print("✅ 配置檔案 (config/*.json)")
    print("✅ 依賴清單 (requirements.txt)")
    print("✅ 工具腳本 (scripts/*.py)")
    print("✅ 說明文檔 (README.md)")
    print()
    print("🚀 建議的後續步驟:")
    print()
    print("1. 📦 安裝基礎套件:")
    print("   pip install numpy opencv-python PyQt5")
    print()
    print("2. 🔍 檢查環境:")
    print("   python scripts\\environment_check.py")
    print()
    print("3. 🚀 測試啟動:")
    print("   python scripts\\simple_launcher.py")
    print()
    print("4. 📋 檢查原有功能:")
    print("   python launcher_app.py")
    print()
    print("💡 提示:")
    print("- 所有新創建的檔案都不會影響現有功能")
    print("- 可以逐步整合新的模組和功能")
    print("- 如果遇到問題，可以查看logs/目錄")
    print()

def main():
    """主函數"""
    try:
        print_header()
        check_existing_structure()
        
        print("🔧 開始設置專案結構...")
        print("這個過程不會修改您現有的檔案")
        
        input("按Enter鍵繼續，或Ctrl+C取消...")
        print()
        
        # 執行設置步驟
        create_new_directories()
        create_python_modules()
        create_configuration_files()
        create_requirements_file()
        create_utility_scripts()
        create_readme()
        
        print_summary_and_next_steps()
        
    except KeyboardInterrupt:
        print("\n❌ 設置已取消")
    except Exception as e:
        print(f"\n❌ 設置過程中發生錯誤: {e}")
        print("請檢查檔案權限或重新運行腳本")
    
    input("\n按任意鍵退出...")

if __name__ == "__main__":
    main()

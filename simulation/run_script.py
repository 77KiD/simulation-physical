#!/usr/bin/env python3
"""
PCBA檢測系統啟動腳本
提供系統啟動、檢查和維護功能
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def check_python_version():
    """檢查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print("❌ Python版本過低，需要Python 3.6+")
        print(f"當前版本: {version.major}.{version.minor}.{version.micro}")
        return False
    else:
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True

def check_dependencies():
    """檢查依賴套件"""
    required_packages = [
        'PyQt5',
        'opencv-python', 
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
            print(f"✅ {package}: 已安裝")
        except ImportError:
            print(f"❌ {package}: 未安裝")
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies(packages):
    """安裝缺少的套件"""
    if not packages:
        return True
        
    print(f"\n📦 正在安裝缺少的套件: {', '.join(packages)}")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install'
        ] + packages)
        print("✅ 套件安裝完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 套件安裝失敗: {e}")
        return False

def check_hardware_availability():
    """檢查硬體可用性"""
    hardware_status = {
        'gpio': False,
        'camera': False,
        'i2c': False
    }
    
    # 檢查GPIO
    try:
        import Jetson.GPIO
        hardware_status['gpio'] = True
        print("✅ Jetson GPIO: 可用")
    except ImportError:
        print("⚠️  Jetson GPIO: 不可用 (將使用模擬模式)")
    
    # 檢查相機
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            hardware_status['camera'] = True
            print("✅ 相機: 可用")
            cap.release()
        else:
            print("⚠️  相機: 不可用")
    except:
        print("⚠️  相機: 檢查失敗")
    
    # 檢查I2C (PCA9685)
    if hardware_status['gpio']:
        try:
            import board
            import busio
            i2c = busio.I2C(board.SCL, board.SDA)
            hardware_status['i2c'] = True
            print("✅ I2C: 可用")
        except:
            print("⚠️  I2C: 不可用")
    
    return hardware_status

def create_directories():
    """建立必要的目錄"""
    directories = ['data', 'data/reports', 'logs']
    
    for dir_name in directories:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
        print(f"📁 建立目錄: {dir_name}")

def run_system():
    """啟動系統"""
    print("\n🚀 正在啟動PCBA檢測系統...")

    # 取得 run_script.py 檔案所在資料夾
    current_dir = os.path.dirname(os.path.abspath(__file__))
    main_ui_path = os.path.join(current_dir, 'main_ui.py')

    try:
        # 檢查主程式文件是否存在
        if not os.path.exists(main_ui_path):
            print(f"❌ 找不到 main_ui.py 文件：{main_ui_path}")
            return False

        # 使用絕對路徑執行 main_ui.py
        subprocess.run([sys.executable, main_ui_path])
        return True

    except KeyboardInterrupt:
        print("\n⏹️  用戶中斷程式")
        return True
    except Exception as e:
        print(f"❌ 系統啟動失敗: {e}")
        return False


def run_tests():
    """執行系統測試"""
    print("\n🧪 執行系統測試...")
    
    test_files = [
        'hardware_controller.py',
        'detection_engine.py', 
        'data_manager.py',
        'config_manager.py'
    ]
    
    all_passed = True
    
    for test_file in test_files:
        if os.path.exists(test_file):
            try:
                # 嘗試導入模組
                module_name = test_file[:-3]  # 移除.py
                __import__(module_name)
                print(f"✅ {test_file}: 測試通過")
            except Exception as e:
                print(f"❌ {test_file}: 測試失敗 - {e}")
                all_passed = False
        else:
            print(f"⚠️  {test_file}: 文件不存在")
            all_passed = False
    
    return all_passed

def show_system_info():
    """顯示系統資訊"""
    print("\n📊 系統資訊")
    print("=" * 50)
    print(f"Python版本: {sys.version}")
    print(f"作業系統: {os.name}")
    print(f"當前目錄: {os.getcwd()}")
    
    # 檢查文件
    core_files = [
        'main_ui.py',
        'hardware_controller.py',
        'detection_engine.py',
        'data_manager.py',
        'config_manager.py'
    ]
    
    print("\n📝 核心文件檢查:")
    for file in core_files:
        status = "✅" if os.path.exists(file) else "❌"
        print(f"  {status} {file}")
    
    # 顯示硬體狀態
    print("\n🔌 硬體狀態:")
    hardware = check_hardware_availability()
    for device, available in hardware.items():
        status = "✅" if available else "⚠️ "
        print(f"  {status} {device.upper()}")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='PCBA檢測系統啟動腳本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python run.py              # 正常啟動系統
  python run.py --check      # 檢查系統狀態
  python run.py --test       # 執行測試
  python run.py --install    # 安裝依賴套件
  python run.py --info       # 顯示系統資訊
        """
    )
    
    parser.add_argument('--check', action='store_true',
                       help='檢查系統狀態和依賴')
    parser.add_argument('--test', action='store_true',
                       help='執行系統測試')
    parser.add_argument('--install', action='store_true',
                       help='安裝缺少的依賴套件')
    parser.add_argument('--info', action='store_true',
                       help='顯示系統資訊')
    parser.add_argument('--force', action='store_true',
                       help='強制執行（忽略檢查錯誤）')
    
    args = parser.parse_args()
    
    print("🔧 PCBA檢測系統啟動器 v2.0")
    print("=" * 50)
    
    # 顯示系統資訊
    if args.info:
        show_system_info()
        return
    
    # 基本檢查
    if not check_python_version() and not args.force:
        sys.exit(1)
    
    # 建立必要目錄
    create_directories()
    
    # 檢查依賴
    missing = check_dependencies()
    
    # 安裝依賴
    if args.install or missing:
        if missing:
            if not install_dependencies(missing) and not args.force:
                sys.exit(1)
        else:
            print("✅ 所有依賴套件都已安裝")
    
    # 執行測試
    if args.test:
        if not run_tests() and not args.force:
            print("\n❌ 測試失敗，請檢查系統配置")
            sys.exit(1)
        else:
            print("\n✅ 所有測試通過")
    
    # 檢查模式
    if args.check:
        print("\n🔍 系統狀態檢查完成")
        hardware = check_hardware_availability()
        
        if not any(hardware.values()):
            print("\n⚠️  未檢測到任何硬體設備，系統將以模擬模式運行")
        
        return
    
    # 檢查硬體（僅提示，不阻止啟動）
    print("\n🔌 檢查硬體設備...")
    hardware = check_hardware_availability()
    
    if not any(hardware.values()):
        print("\n⚠️  未檢測到硬體設備，將以模擬模式運行")
        input("按Enter鍵繼續...")
    
    # 啟動系統
    success = run_system()
    
    if success:
        print("\n✅ 系統正常結束")
    else:
        print("\n❌ 系統異常結束")
        sys.exit(1)

if __name__ == '__main__':
    main()

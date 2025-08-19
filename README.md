# PCBA 檢測系統 – Simulation & Physical

基於 PyQt5 + OpenCV 的 PCBA 產線模擬 / 實體控制與（可選）AI 偵測框架。  
支援 **模擬模式**（不接硬體就能測試 UI 與流程）與 **實體模式**（相機 + 伺服 + I2C）。

> 本專案結構與啟動檔：`simulation/`、`physical/`、`launcher_app.py`。  
> 先安裝最小相依套件即可在模擬模式啟動；AI 偵測與硬體控制為選配功能。  
> （專案原有 README 提到的功能/結構已在本版整理與更新。） 

---

## 目錄
- [功能特色](#功能特色)
- [系統需求](#系統需求)
- [安裝與快速開始](#安裝與快速開始)
  - [Windows](#windows)
  - [Linux / Jetson Orin Nano](#linux--jetson-orin-nano)
  - [（選配）AI 偵測套件](#選配ai-偵測套件)
- [專案結構](#專案結構)
- [運行模式](#運行模式)
- [常見問題與排除](#常見問題與排除)
- [開發建議](#開發建議)
- [授權與貢獻](#授權與貢獻)

---

## 功能特色
- **雙模式工作流**
  - **模擬模式**：不連硬體即可驗證 GUI、流程與資料輸出
  - **實體模式**：相機擷取、輸送帶節拍控制、PCA9685 伺服控制
- **（選配）AI 偵測**：可接 YOLOv8/YOLOv12 流程（需另行安裝 PyTorch / Ultralytics）
- **GUI**：PyQt5 現代化介面、狀態監控與提示音
- **資料輸出**：支援 CSV / YAML（依實作）
- **跨平台**：Windows / Linux / Jetson Orin Nano

> 原始 README 的功能點（PyQt5、OpenCV、雙模式、硬體支援等）已整合到此處並補完安裝細節與排錯。  
> （來源：repo 首頁 README 頁面內容摘要） 

---

## 系統需求
- **Python**：3.10–3.12（建議）  
- **RAM**：≥ 4 GB  
- **儲存**：≥ 2 GB
- **作業系統**：Windows 10/11、Ubuntu 20.04/22.04、Jetson Orin Nano（JetPack 6.x）

> 若使用 **AI 偵測**：需依平台安裝對應版本的 **PyTorch** 與 **Ultralytics**。

---

## 安裝與快速開始

### Windows
```bash
# 進入專案資料夾
cd simulation-physical

# 安裝最小相依（GUI + 影像）
pip install -r requirements.txt

# 啟動（預設提供啟動器）
python launcher_app.py
Linux / Jetson Orin Nano
bash
複製
編輯
# 基本系統套件（Jetson I2C 必備）
sudo apt update
sudo apt install -y python3-pip python3-smbus i2c-tools

# 進入專案並安裝 Python 套件（最小相依）
cd simulation-physical
pip3 install -r requirements.txt

# 以模擬模式測試 GUI
python3 launcher_app.py
OpenCV 注意：無桌面或最小化環境請使用 opencv-python-headless；
Jetson 上常建議優先使用系統 OpenCV（或 headless 版本）以避免 Qt 插件衝突。

（選配）AI 偵測套件
安裝對應平台的 PyTorch / torchvision / torchaudio

x86_64（Windows/Linux）：可用官方 pip 或 CUDA 對應的輪檔

Jetson Orin Nano：請使用與 JetPack / CUDA 相容的 wheel（例如 Jetson AI Lab 的索引）

安裝 Ultralytics（YOLO）

bash
複製
編輯
pip install ultralytics
將你的模型/設定接到偵測流程（若有 yolo_inference.py 或類似模組，依內部說明整合）

專案結構
以目前 repo 主要檔案為準（simulation/、physical/、launcher_app.py、requirements.txt）

bash
複製
編輯
simulation-physical/
├── launcher_app.py          # 啟動器（可切換模擬/實體或進入主 UI）
├── requirements.txt         # 相依套件（最小可運行 + 選配 AI / 硬體）
├── simulation/              # 模擬模式邏輯（無硬體）
│   └── ...                  # 影像來源、節拍模擬、假資料輸出
├── physical/                # 實體模式邏輯（相機 / PCA9685 / I2C）
│   └── ...                  # 硬體抽象層、控制器、狀態檢查
└── README.md
原始 README 曾提到 scripts/, core/, ui/ 等資料夾；若後續加入，請同步更新本節結構表。
（來源：當前 repo 首頁列出之檔案清單） 
GitHub

運行模式
模擬模式

不需任何硬體；相機輸入可用測試影像或虛擬來源

可用來調整 GUI、節拍邏輯與 CSV 輸出格式

實體模式

需求：USB 相機、PCA9685 + 伺服（如 MG996R）、（選配）感測器

Jetson：請先確認 I2C 匯流排可見（i2cdetect -y 1），相機在 /dev/video*

若你的 UI 有「模式選擇」頁面，確保在無硬體檢測到時自動 fallback 到 模擬模式。

常見問題與排除
1) 啟動時找不到 Qt 平台外掛（xcb）
現象：qt.qpa.plugin: Could not load the Qt platform plugin "xcb"...

作法：

在 無桌面 或 遠端 環境改裝 opencv-python-headless

確認系統已安裝 libxcb 相關元件（Linux）

以 QT_DEBUG_PLUGINS=1 觀察缺件

2) 相機開不起來
檢查是否被其他程式佔用

Linux/Jetson：確認 /dev/video0 存在，並安裝 v4l2-utils 以測試（v4l2-ctl --all）

3) I2C / PCA9685 無回應
Jetson：先安裝 python3-smbus i2c-tools，並檢查 i2cdetect -y 1 是否能看到 0x40

伺服電源請獨立供電（如 6V/15A 桌上型直流電源），與 Jetson 共地（GND 相連）

4) PyTorch / Ultralytics 安裝困難
Windows / x86：使用官方 pip + CUDA 對應版本

Jetson：請安裝 對應 JetPack 的 wheel；不同版本混用會出現導入失敗或 CUDA 錯誤

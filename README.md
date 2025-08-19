# PCBA檢測系統 v2.0

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

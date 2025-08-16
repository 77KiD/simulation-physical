import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

class ModeLauncher:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("系統啟動器")
        self.root.geometry("380x260")
        self.root.minsize(380, 260)  # 保障最小高度
        self.root.resizable(False, False)

        self.center_window()

        title_label = tk.Label(self.root, text="系統模式選擇", font=("Arial", 18, "bold"), fg="navy")
        title_label.pack(pady=20)

        self.desc_label = tk.Label(self.root, text="請選擇要啟動的模式：", font=("Arial", 12))
        self.desc_label.pack(pady=6)

        # 取得檔案存在狀態，決定是否啟用按鈕
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.simulation_script = os.path.join(base_dir, "simulation", "run_script.py")
        self.physical_script   = os.path.join(base_dir, "physical",   "physical_mode.py")

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=16)

        # 左右並排的兩顆按鈕
        simulation_btn = tk.Button(
        button_frame, text="模擬模式", command=self.launch_simulation_mode,
        font=("Arial", 14), bg="#4CAF50", fg="white", width=12, height=2, cursor="hand2",
        state=tk.NORMAL if os.path.exists(self.simulation_script) else tk.DISABLED
        )
        simulation_btn.grid(row=0, column=0, padx=10)

        physical_btn = tk.Button(
        button_frame, text="實體模式", command=self.launch_physical_mode,
        font=("Arial", 14), bg="#2196F3", fg="white", width=12, height=2, cursor="hand2",
        state=tk.NORMAL if os.path.exists(self.physical_script) else tk.DISABLED
        )
        physical_btn.grid(row=0, column=1, padx=10)

        self.status_label = tk.Label(self.root, text="就緒", font=("Arial", 10), fg="gray")
        self.status_label.pack(side=tk.BOTTOM, pady=8)


        
    def center_window(self):
        """將視窗置中顯示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def launch_simulation_mode(self):
        """啟動模擬模式"""
        # 取得目前 launcher_app.py 所在資料夾
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # 用相對路徑定位 simulation 資料夾底下的 run_script.py
        simulation_script = os.path.join(base_dir, "simulation", "run_script.py")
        self.launch_program(simulation_script, "模擬模式")

        
    def launch_physical_mode(self):
        """啟動實體模式"""
        # 取得目前 launcher_app.py 所在資料夾
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # 用相對路徑定位 simulation 資料夾底下的 run_script.py
        physical_script = os.path.join(base_dir, "physical", "run_script.py")
        self.launch_program(physical_script, "實體模式")
        
    def launch_program(self, script_name, mode_name):
        """啟動指定的程式"""
        self.status_label.config(text=f"正在啟動{mode_name}...", fg="blue")
        self.root.update()
        
        try:
            if os.path.exists(script_name):
                # 啟動程式
                subprocess.Popen([sys.executable, script_name])
                messagebox.showinfo("啟動成功", f"{mode_name}已啟動")
                self.status_label.config(text=f"{mode_name}已啟動", fg="green")
                # 啟動成功後關閉啟動器
                self.root.quit()
            else:
                messagebox.showerror("檔案不存在", 
                                   f"找不到 {script_name}\n請確認檔案是否存在於同一目錄下")
                self.status_label.config(text="啟動失敗", fg="red")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"啟動{mode_name}失敗：\n{str(e)}")
            self.status_label.config(text="啟動失敗", fg="red")

def main():
    root = tk.Tk()
    app = ModeLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()

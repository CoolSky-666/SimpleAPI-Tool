# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk, ImageGrab
import io
import json
import os
import requests
import threading
import webbrowser
from latex2mathml.converter import convert
import sys

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
API_URL_TURBO = "https://server.simpletex.cn/api/latex_ocr_turbo"
API_URL_STANDARD = "https://server.simpletex.cn/api/latex_ocr"

# --- 现代设计师配色 ---
CLR_PRIMARY = "#2563EB"      # 核心蓝
CLR_HOVER = "#1D4ED8"        # 悬浮蓝
CLR_BG = "#F8FAFC"           # 纯净背景
CLR_CARD = "#FFFFFF"         # 卡片白
CLR_BORDER = "#E2E8F0"       # 边框线
CLR_TEXT_MAIN = "#1E293B"    # 主文字（深蓝黑）
CLR_TEXT_SEC = "#64748B"     # 辅助文字（灰蓝）
CLR_SUCCESS = "#10B981"      # 成功绿
CLR_WARNING = "#F59E0B"      # 警告橙
CLR_DANGER = "#EF4444"       # 错误红

class SimpleTexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SimpleTex API Tool")
        self.root.geometry("800x750")
        self.root.resizable(True, True)
        self.root.configure(bg=CLR_BG)
        
        self.api_key = ""
        self.current_image = None
        self.current_photo = None
        self.latex_result = ""
        
        self.setup_styles()
        self.load_config()
        self.setup_ui()
        self.bind_events()
        if getattr(sys, 'frozen', False):
            # 如果是打包后的环境
            bundle_dir = sys._MEIPASS
        else:
            # 如果是开发环境
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(bundle_dir, "logo.ico")
        
        try:
            # 设置窗口图标
            self.root.iconbitmap(icon_path)
        except:
            pass # 如果文件找不着，就忽略，防止程序崩溃
        if not self.api_key:
            self.root.after(500, self.show_api_key_dialog)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # 1. 容器样式
        style.configure('TFrame', background=CLR_BG)
        style.configure('Card.TFrame', background=CLR_CARD, relief="flat")
        
        # 2. 扁平单选框样式优化
        style.configure('TRadiobutton', 
                        background=CLR_BG, 
                        foreground=CLR_TEXT_MAIN, 
                        font=('Microsoft YaHei UI', 9))
        style.map('TRadiobutton', 
                  indicatorcolor=[('selected', CLR_PRIMARY), ('active',CLR_BG)],
                  background=[('active', CLR_BG)],
                  foreground=[('selected', CLR_PRIMARY)])
        
        # 3. 按钮扁平圆角样式
        style.configure('Primary.TButton', 
                        font=('Microsoft YaHei UI', 9, 'bold'),
                        background=CLR_PRIMARY, foreground='white', 
                        borderwidth=0, focuscolor='none', padding=(15, 8))
        style.map('Primary.TButton', background=[('active', CLR_HOVER)])
        
        style.configure('Action.TButton', 
                        font=('Microsoft YaHei UI', 9),
                        background=CLR_CARD, foreground=CLR_TEXT_MAIN,
                        borderwidth=1, bordercolor=CLR_BORDER, focuscolor='none', padding=(10, 5))
        style.map('Action.TButton', background=[('active', CLR_BG)])

    def setup_ui(self):
        # 主边距容器
        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- 顶部：精简配置栏 ---
        top_bar = ttk.Frame(main_container)
        top_bar.pack(fill=tk.X, pady=(0, 20))
        
        # API Token
        api_frame = ttk.Frame(top_bar)
        api_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # 使用 tk.Label 彻底解决灰色背景块
        tk.Label(api_frame, text="ACCESS TOKEN", font=('Consolas', 8, 'bold'), 
                 fg=CLR_TEXT_SEC, bg=CLR_BG).pack(anchor=tk.W)
        
        api_input_inner = ttk.Frame(api_frame)
        api_input_inner.pack(fill=tk.X, pady=(4, 0))
        self.api_entry = tk.Entry(api_input_inner, show="*", font=('Consolas', 10), 
                                 bg=CLR_CARD, fg=CLR_TEXT_MAIN, relief="flat", highlightthickness=1, 
                                 highlightbackground=CLR_BORDER, highlightcolor=CLR_PRIMARY)
        self.api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 8))
        self.api_entry.insert(0, self.api_key)
        
        ttk.Button(api_input_inner, text="保存配置", style="Action.TButton", command=self.save_api_key).pack(side=tk.LEFT, padx=2)
        ttk.Button(api_input_inner, text="用量查询", style="Action.TButton", command=self.open_usage_page).pack(side=tk.LEFT, padx=2)

        # 模型选择
        model_frame = ttk.Frame(top_bar, padding=(25, 0, 0, 0))
        model_frame.pack(side=tk.RIGHT)
        tk.Label(model_frame, text="识别模式", font=('Microsoft YaHei UI', 8, 'bold'), 
                 fg=CLR_TEXT_SEC, bg=CLR_BG).pack(anchor=tk.W)
        
        self.model_var = tk.StringVar(value="turbo")
        radio_box = ttk.Frame(model_frame)
        radio_box.pack(pady=(4, 0))
        ttk.Radiobutton(radio_box, text="极速", variable=self.model_var, value="turbo").pack(side=tk.LEFT)
        ttk.Radiobutton(radio_box, text="标准", variable=self.model_var, value="standard").pack(side=tk.LEFT, padx=(10, 0))

        # --- 中间：预览卡片 ---
        preview_header = ttk.Frame(main_container)
        preview_header.pack(fill=tk.X, pady=(0, 8))
        tk.Label(preview_header, text="图片预览", font=('Microsoft YaHei UI', 10, 'bold'), 
                 fg=CLR_TEXT_MAIN, bg=CLR_BG).pack(side=tk.LEFT)
        tk.Label(preview_header, text="Ctrl+V 粘贴截图", font=('Microsoft YaHei UI', 9), 
                 fg=CLR_TEXT_SEC, bg=CLR_BG).pack(side=tk.RIGHT)

        preview_card = ttk.Frame(main_container, style='Card.TFrame')
        preview_card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.image_canvas = tk.Canvas(preview_card, bg=CLR_CARD, 
                                      highlightthickness=1, highlightbackground=CLR_BORDER, bd=0)
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        self.image_canvas.bind("<Configure>", lambda e: self.display_image())
        
        self.hint_label = tk.Label(self.image_canvas, text="请粘贴截图...", font=('Microsoft YaHei UI', 11), 
                                  fg=CLR_TEXT_SEC, bg=CLR_CARD)
        self.hint_label.place(relx=0.5, rely=0.5, anchor="center")

        # --- 状态与操作栏 ---
        action_bar = ttk.Frame(main_container)
        action_bar.pack(fill=tk.X, pady=(0, 20))
        
        self.recognize_btn = ttk.Button(action_bar, text="识别公式", style="Primary.TButton", command=self.recognize_formula)
        self.recognize_btn.pack(side=tk.LEFT)
        
        ttk.Button(action_bar, text="清空预览", style="Action.TButton", command=self.clear_all).pack(side=tk.LEFT, padx=10)
        
        # 状态展示区
        status_info = ttk.Frame(action_bar)
        status_info.pack(side=tk.RIGHT)
        
        self.status_label = tk.Label(status_info, text="等待输入", font=('Microsoft YaHei UI', 9), 
                                    fg=CLR_TEXT_SEC, bg=CLR_BG)
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # 置信度可视化（彻底移除灰色块）
        tk.Label(status_info, text="置信度:", font=('Microsoft YaHei UI', 9), 
                 fg=CLR_TEXT_MAIN, bg=CLR_BG).pack(side=tk.LEFT, padx=(10, 5))
        
        self.conf_canvas = tk.Canvas(status_info, width=120, height=10, bg=CLR_BORDER, highlightthickness=0)
        self.conf_canvas.pack(side=tk.LEFT, padx=5)
        
        self.conf_label = tk.Label(status_info, text="--", width=5, font=('Consolas', 10, 'bold'), 
                                  fg=CLR_TEXT_MAIN, bg=CLR_BG)
        self.conf_label.pack(side=tk.LEFT)

        # --- 底部：结果区 ---
        result_title_frame = ttk.Frame(main_container)
        result_title_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(result_title_frame, text="识别结果 (LaTeX)", font=('Microsoft YaHei UI', 10, 'bold'), 
                 fg=CLR_TEXT_MAIN, bg=CLR_BG).pack(anchor=tk.W)
        
        self.result_text = scrolledtext.ScrolledText(main_container, height=5, font=('Consolas', 11),
                                                    bd=0, bg=CLR_CARD, highlightthickness=1,
                                                    highlightbackground=CLR_BORDER, padx=12, pady=12)
        self.result_text.pack(fill=tk.X, pady=(0, 15))
        
        # 复制按钮组
        copy_group = ttk.Frame(main_container)
        copy_group.pack(fill=tk.X)
        copy_btns = [("$LaTeX$", self.copy_latex_inline), ("$$LaTeX$$", self.copy_latex_display), 
                    ("纯文本", self.copy_latex), ("MathML (Word)", self.copy_mathml)]
        
        for text, cmd in copy_btns:
            ttk.Button(copy_group, text=text, style="Action.TButton", command=cmd).pack(side=tk.LEFT, padx=(0, 5))

        self.draw_confidence_bar(0)

    def draw_confidence_bar(self, conf):
        """修复坐标并美化进度条"""
        self.conf_canvas.delete("all")
        w, h = 120, 10
        # 背景（浅灰色底）
        self.conf_canvas.create_rectangle(0, 0, w, h, fill="#E2E8F0", outline="")
        if conf > 0:
            bar_w = int(w * conf)
            color = CLR_SUCCESS if conf >= 0.9 else (CLR_WARNING if conf >= 0.7 else CLR_DANGER)
            # 填充进度
            self.conf_canvas.create_rectangle(0, 0, bar_w, h, fill=color, outline="")
        self.conf_label.config(text=f"{conf*100:.0f}%" if conf > 0 else "--")

    # --- 以下逻辑保持与原版功能一致 ---
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.api_key = json.load(f).get('api_key', '')
            except: pass

    def save_api_key(self):
        self.api_key = self.api_entry.get().strip()
        if self.api_key:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({'api_key': self.api_key}, f)
            messagebox.showinfo("成功", "设置已保存")
        else:
            messagebox.showwarning("提示", "请输入 Token")

    def bind_events(self):
        self.root.bind('<Control-v>', self.paste_image)
        self.root.bind('<Control-V>', self.paste_image)
        self.root.bind('<Return>', lambda e: self.recognize_formula())

    def open_usage_page(self):
        webbrowser.open("https://simpletex.cn/user/center")

    def paste_image(self, event=None):
        try:
            image = ImageGrab.grabclipboard()
            if image is not None:
                self.current_image = image
                self.display_image()
                self.hint_label.place_forget()
                self.status_label.config(text="图片就绪", fg=CLR_PRIMARY)
            else:
                messagebox.showinfo("提示", "剪贴板中没有图片")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def display_image(self):
        if self.current_image is None: return
        self.root.update_idletasks()
        cw, ch = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()
        if cw < 50: return
        iw, ih = self.current_image.size
        ratio = min((cw-10)/iw, (ch-10)/ih, 1.0)
        disp = self.current_image.copy()
        if ratio < 1.0: disp.thumbnail((int(iw*ratio), int(ih*ratio)), Image.Resampling.LANCZOS)
        self.current_photo = ImageTk.PhotoImage(disp)
        self.image_canvas.delete("all")
        self.image_canvas.create_image(cw//2, ch//2, image=self.current_photo, anchor=tk.CENTER)

    def recognize_formula(self):
        if self.current_image is None: return
        token = self.api_entry.get().strip()
        if not token: 
            self.show_api_key_dialog()
            return
        self.recognize_btn.config(state=tk.DISABLED)
        self.status_label.config(text="识别中...", fg=CLR_WARNING)
        threading.Thread(target=self._do_recognize, args=(token,), daemon=True).start()

    def _do_recognize(self, token):
        try:
            buf = io.BytesIO()
            self.current_image.save(buf, format='PNG')
            buf.seek(0)
            url = API_URL_TURBO if self.model_var.get() == "turbo" else API_URL_STANDARD
            resp = requests.post(url, files={'file': ('img.png', buf, 'image/png')}, headers={'token': token}, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status'):
                    res = data['res']
                    latex = res.get('latex') or res.get('success_res', {}).get(next(iter(res.get('success_res', {}) or []), ''), {}).get('latex', '')
                    conf = res.get('conf') or res.get('success_res', {}).get(next(iter(res.get('success_res', {}) or []), ''), {}).get('conf', 0)
                    self.root.after(0, lambda: self._on_success(latex, conf))
                else: self.root.after(0, lambda: self._on_error(data.get('msg', '解析失败')))
            else: self.root.after(0, lambda: self._on_error(f"HTTP {resp.status_code}"))
        except Exception as e: self.root.after(0, lambda: self._on_error(str(e)))

    def _on_success(self, latex, conf):
        self.latex_result = latex
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, latex)
        self.recognize_btn.config(state=tk.NORMAL)
        self.status_label.config(text="识别完成", fg=CLR_SUCCESS)
        self.draw_confidence_bar(conf)

    def _on_error(self, msg):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"错误: {msg}")
        self.recognize_btn.config(state=tk.NORMAL)
        self.status_label.config(text="识别失败", fg=CLR_DANGER)

    def _copy(self, text):
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_label.config(text="已复制", fg=CLR_SUCCESS)

    def copy_latex(self): self._copy(self.latex_result)
    def copy_latex_inline(self): self._copy(f"${self.latex_result}$")
    def copy_latex_display(self): self._copy(f"$${self.latex_result}$$")
    # def copy_mathml(self):
    #     if self.latex_result:
    #         try:
    #             self._copy(convert(self.latex_result))
    #         except: messagebox.showerror("错误", "转换失败")
    def copy_mathml(self):
        if self.latex_result:
            try:
                # 尝试转换
                mathml_code = convert(self.latex_result)
                self._copy(mathml_code)
            except Exception as e:
                # 打印出真实的报错原因
                import traceback
                error_details = traceback.format_exc()
                print(error_details)  # 在控制台查看
                messagebox.showerror("转换失败", f"错误详情:\n{str(e)}")

    def clear_all(self):
        self.current_image = self.current_photo = None
        self.latex_result = ""
        self.image_canvas.delete("all")
        self.hint_label.place(relx=0.5, rely=0.5, anchor="center")
        self.result_text.delete(1.0, tk.END)
        self.status_label.config(text="就绪", fg=CLR_TEXT_SEC)
        self.draw_confidence_bar(0)

    def show_api_key_dialog(self):
        d = tk.Toplevel(self.root)
        d.title("设置 Token")
        d.geometry("350x160")
        d.configure(bg=CLR_CARD)
        d.transient(self.root)
        d.grab_set()
        tk.Label(d, text="请设置 SimpleTex Token", bg=CLR_CARD, font=('Microsoft YaHei UI', 10, 'bold')).pack(pady=15)
        e = tk.Entry(d, width=30, relief="flat", highlightthickness=1, highlightbackground=CLR_BORDER)
        e.pack(pady=5, ipady=4)
        ttk.Button(d, text="保存配置", style="Primary.TButton", command=lambda: [self.api_entry.delete(0, tk.END), self.api_entry.insert(0, e.get()), self.save_api_key(), d.destroy()]).pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleTexApp(root)
    root.mainloop()

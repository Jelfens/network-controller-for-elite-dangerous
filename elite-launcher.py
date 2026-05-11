import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading
import subprocess
import os
import sys
import math

class EliteLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Elite Control")
        
        # Sabit boyutu büyüttük (600x650)
        self.ww, self.wh = 600, 650
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - self.ww) // 2
        y = (sh - self.wh) // 2
        self.root.geometry(f"{self.ww}x{self.wh}+{x}+{y}")
        self.root.resizable(False, False)
        
        # Performans / Animasyon
        self.pulse_val = 0
        self.fade_alpha = 0.0
        
        # Elite Dangerous Renk Paleti
        self.orange = "#FF7100"
        self.dark_orange = "#8c3e00"
        self.bg_color = "#0B0C10" 
        self.panel_bg = "#1F2833" 
        self.text_color = "#C5C6C7"
        self.log_fg = "#45A29E" 
        
        self.root.configure(bg=self.bg_color)
        self.root.attributes('-alpha', 0.0)
        
        self.setup_styles()
        self.create_widgets()
        
        self.process = None
        self.is_running = False
        
        self.fade_in()
        self.pulse_animation()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("TFrame", background=self.bg_color)
        style.configure("Panel.TFrame", background=self.panel_bg)
        
        # Font boyutlarını sistem ölçeklendirmesine (DPI) karşı biraz küçülttük
        style.configure("Header.TLabel", background=self.bg_color, foreground=self.orange, font=("Orbitron", 16, "bold"))
        style.configure("Sub.TLabel", background=self.bg_color, foreground=self.text_color, font=("Sans", 9))
        style.configure("IP.TLabel", background=self.bg_color, foreground=self.orange, font=("Monospace", 12, "bold"))
        
        style.configure("Elite.TButton", 
                        background=self.panel_bg, 
                        foreground=self.orange, 
                        borderwidth=1, 
                        focusthickness=0, 
                        padding=12,
                        font=("Sans", 10, "bold"))
        
        style.map("Elite.TButton",
                  background=[('active', self.orange), ('pressed', self.dark_orange)],
                  foreground=[('active', self.bg_color), ('pressed', self.text_color)])

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def create_widgets(self):
        # Ana Canvas
        self.canvas = tk.Canvas(self.root, width=self.ww, height=self.wh, bg=self.bg_color, highlightthickness=0)
        self.canvas.place(x=0, y=0)
        
        # Sci-Fi Köşeleri (Çerçeve)
        c = self.orange
        w, h = self.ww, self.wh
        l = 40 
        self.canvas.create_line(15, 15+l, 15, 15, 15+l, 15, fill=c, width=2)
        self.canvas.create_line(w-15-l, 15, w-15, 15, w-15, 15+l, fill=c, width=2)
        self.canvas.create_line(15, h-15-l, 15, h-15, 15+l, h-15, fill=c, width=2)
        self.canvas.create_line(w-15-l, h-15, w-15, h-15, w-15, h-15-l, fill=c, width=2)
        
        # İçerik Çerçevesi (Boyutu büyüdü)
        content = ttk.Frame(self.root)
        content.place(x=35, y=35, width=self.ww-70, height=self.wh-70)
        
        # 1. Başlık
        ttk.Label(content, text="ELITE CONTROL", style="Header.TLabel").pack(pady=(20, 5))
        ttk.Label(content, text="NETWORK TELEMETRY LINK", style="Sub.TLabel").pack()
        
        ttk.Frame(content, height=1, style="Panel.TFrame").pack(fill="x", pady=20, padx=40)
        
        # 2. IP Alanı
        ttk.Label(content, text="SCAN THIS IP ON YOUR DEVICE:", style="Sub.TLabel").pack()
        self.ip_label = ttk.Label(content, text=f"http://{self.get_ip()}:5000", style="IP.TLabel")
        self.ip_label.pack(pady=(10, 20))
        
        # 4. Butonlar (Log alanından önce alta sabitliyoruz)
        btn_frame = ttk.Frame(content)
        btn_frame.pack(side="bottom", fill="x", pady=(10, 15), padx=20)
        
        self.start_btn = ttk.Button(btn_frame, text="ENGAGE SERVER", style="Elite.TButton", command=self.toggle_server)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        ttk.Button(btn_frame, text="OFFLINE", style="Elite.TButton", command=self.quit_app).pack(side="right", expand=True, fill="x")

        # 3. Log Alanı (Geri kalan boşluğu doldurması için en son packliyoruz)
        log_container = tk.Frame(content, bg=self.orange, bd=1) 
        log_container.pack(side="top", fill="both", expand=True, padx=20, pady=10)
        
        self.log_area = scrolledtext.ScrolledText(
            log_container, bg=self.bg_color, fg=self.log_fg, 
            font=("Monospace", 9), borderwidth=0, highlightthickness=0
        )
        self.log_area.pack(fill="both", expand=True, padx=2, pady=2)
        self.log_area.insert(tk.END, "> SYSTEM BOOT SEQUENCE INITIATED...\n")
        self.log_area.configure(state='disabled')

    def fade_in(self):
        if self.fade_alpha < 1.0:
            self.fade_alpha += 0.04
            self.root.attributes('-alpha', self.fade_alpha)
            self.root.after(16, self.fade_in)

    def pulse_animation(self):
        self.pulse_val += 0.1
        intensity = int(180 + 75 * math.sin(self.pulse_val))
        color = f'#{intensity:02x}{int(intensity*0.44):02x}00'
        
        try:
            self.ip_label.configure(foreground=color)
            if self.is_running:
                g_intensity = int(150 + 105 * math.sin(self.pulse_val))
                ttk.Style().configure("Running.TButton", foreground=f'#00{g_intensity:02x}00', background=self.panel_bg)
                self.start_btn.configure(style="Running.TButton")
        except:
            pass
        self.root.after(40, self.pulse_animation)

    def log(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, f"[{threading.get_ident()%1000:03d}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def toggle_server(self):
        if not self.is_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        script_path = os.path.join(os.path.dirname(__file__), "elite-control.py")
        self.log("ENGAGING FSD... (STARTING SERVER)")
        
        self.process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )
        
        self.is_running = True
        self.start_btn.configure(text="DISENGAGE")
        threading.Thread(target=self.read_output, daemon=True).start()

    def read_output(self):
        for line in iter(self.process.stdout.readline, ''):
            clean_line = line.strip()
            if clean_line:
                self.root.after(0, self.log, clean_line)
        self.process.stdout.close()

    def stop_server(self):
        if self.process:
            self.process.terminate()
            self.process = None
        self.is_running = False
        self.start_btn.configure(text="ENGAGE SERVER")
        self.start_btn.configure(style="Elite.TButton")
        self.log("SYSTEMS OFFLINE.")

    def quit_app(self):
        self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EliteLauncher(root)
    root.mainloop()

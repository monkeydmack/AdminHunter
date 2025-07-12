#!/usr/bin/env python3
"""
Admin Hunter GUI (Tkinter) - Dark Mode with Animated GIFs & Webhook Alerts

Features:
  - Auto-elevate on Windows (UAC prompt)
  - Dark-themed UI with animated side sprites
  - Minimize-to-tray support via pystray
  - Discord webhook alerts (URL persisted in config file)
  - Dynamic polling interval (1–30s) with synced progress bar
  - Startup and start-hunting notifications
  - Hunting status indicator (inactive/active)
  - Log rotation (last 7 days) and GUI log window
"""
import os
import sys
import time
import threading
import subprocess
import requests
import ctypes
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, font

# Optional tray & notifications support
try:
    import pystray
    from PIL import Image
except ImportError:
    pystray = None

# Desktop notifications & sound alerts
try:
    from plyer import notification
except ImportError:
    notification = None
import winsound

# ----- Configuration -----
SPRITE_LEFT_FILE = 'nqtKzsh.gif'
SPRITE_RIGHT_FILE = 'mGzCi6Z.gif'
FONT_NAME = 'InvisibleKiller'
URL = 'https://realmstock.network/Notifier/EventHistory'
ADMIN_IDS = ['0', '1']
DEFAULT_INTERVAL = 5
ROTMG_EXE = 'RotMG Exalt.exe'
LOG_RETENTION_DAYS = 7
SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'AdminHunterConfig.json')

# ----- Config persistence -----
def load_webhook():
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
            return config.get('webhook_url', '')
    except:
        return ''

def save_webhook(url):
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump({'webhook_url': url}, f)
    except:
        pass

target_webhook = load_webhook()

# ----- Enhanced Admin Data Parsing -----
def parse_admin_data(lines):
    """Parse admin data from API response lines"""
    for line in lines:
        parts = line.split('|')
        if len(parts) >= 9 and parts[0] in ADMIN_IDS:
            return {
                'player_id': parts[0],
                'server': parts[1], 
                'region': parts[2],
                'time': parts[6],
                'uuid': parts[7],
                'value': parts[9] if len(parts) > 9 else 'N/A'
            }
    return None

def create_admin_alert_message(admin_data):
    """Create detailed admin alert message with Discord embed"""
    from datetime import datetime
    
    embed = {
        "title": "🚨 ADMIN DETECTED! 🚨",
        "color": 16711680,  # Red color
        "fields": [
            {
                "name": "👤 Player Info",
                "value": f"**ID:** {admin_data['player_id']}",
                "inline": True
            },
            {
                "name": "🌍 Location",
                "value": f"**Region:** {admin_data['server']}\n**Server:** {admin_data['region']}",
                "inline": True
            },
            {
                "name": "📊 Details",
                "value": f"**Time:** {admin_data['time']}",
                "inline": True
            },
            {
                "name": "⚡ Action Taken",
                "value": "🎮 **RotMG closed automatically!**\n🔄 **Continuing hunt...**",
                "inline": False
            }
        ],
        "thumbnail": {
            "url": "https://i.imgur.com/nqtKzsh.gif"  # RotMG icon (optional)
        },
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {
            "text": "Admin Hunter Alert System",
            "icon_url": "https://i.imgur.com/nqtKzsh.gif"  # Your sprite (optional)
        }
    }
    
    return {
        "content": "@everyone",  
        "embeds": [embed]
    }

# ----- Animated GIF widget -----
class AnimatedGIF(tk.Label):
    def __init__(self, master, path, delay=100, **kw):
        super().__init__(master, **kw)
        self.frames = []
        idx = 0
        while True:
            try:
                frame = tk.PhotoImage(file=path, format=f'gif -index {idx}')
            except tk.TclError:
                break
            self.frames.append(frame)
            idx += 1
        self.delay = delay
        self.idx = 0
        if self.frames:
            w, h = self.frames[0].width(), self.frames[0].height()
            self.config(width=w, height=h, image=self.frames[0])
            self.after(self.delay, self._animate)

    def _animate(self):
        self.idx = (self.idx + 1) % len(self.frames)
        self.config(image=self.frames[self.idx])
        self.after(self.delay, self._animate)

# ----- Helpers -----
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if sys.platform.startswith('win') and not is_admin():
    # Relaunch with admin rights
    script = os.path.abspath(sys.argv[0])
    args = ' '.join(f'"{a}"' for a in sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, f'"{script}" {args}', None, 1)
    sys.exit(0)


def is_rotmg_running():
    try:
        out = subprocess.check_output(
            ['tasklist', '/FI', f'IMAGENAME eq {ROTMG_EXE}'], stderr=subprocess.DEVNULL, text=True)
        return ROTMG_EXE in out
    except:
        return False

# ----- Logging -----
def rotate_logs(dirpath):
    now = time.time()
    for fname in os.listdir(dirpath):
        p = os.path.join(dirpath, fname)
        if os.stat(p).st_mtime < now - LOG_RETENTION_DAYS * 86400:
            try:
                os.remove(p)
            except:
                pass

def setup_logging():
    logs_dir = os.path.join(os.path.expanduser('~'), 'Desktop', 'AdminHunterLogs')
    os.makedirs(logs_dir, exist_ok=True)
    rotate_logs(logs_dir)
    log_path = os.path.join(logs_dir, f"adminhunter_{time.strftime('%Y%m%d_%H%M%S')}.log")
    return open(log_path, 'a', encoding='utf-8', buffering=1)

# ----- Webhook -----
def send_webhook(msg):
    global target_webhook
    if target_webhook:
        try:
            # Handle both simple strings and embed objects
            if isinstance(msg, dict):
                requests.post(target_webhook, json=msg, timeout=5)
            else:
                requests.post(target_webhook, json={'content': msg}, timeout=5)
        except:
            pass

# ----- Main GUI -----
def main():
    global target_webhook
    log_fh = setup_logging()
    root = tk.Tk()
    root.title('Admin Hunter')
    root.config(bg='black')
    root.protocol('WM_DELETE_WINDOW', lambda: root.withdraw() if pystray else root.destroy())

    # Banner
    banner = tk.Frame(root, bg='black')
    AnimatedGIF(banner, SPRITE_LEFT_FILE, bg='black').pack(side=tk.LEFT, padx=(30,10))
    tf = (FONT_NAME, 28, 'bold') if FONT_NAME in font.families() else ('Helvetica', 28, 'bold')
    tk.Label(banner, text='ADMIN HUNTER', font=tf, fg='#FF0000', bg='black').pack(side=tk.LEFT, expand=True)
    AnimatedGIF(banner, SPRITE_RIGHT_FILE, bg='black').pack(side=tk.LEFT, padx=(10,30))
    banner.pack(fill=tk.X, pady=5)

    # Hunting status (hidden)
    hunting_status = tk.Label(root, text='Hunting: Active', font=('Consolas',12,'bold'), fg='#AA0000', bg='black')

    # Controls
    ctrl = tk.Frame(root, bg='black')
    lbl_rotmg = tk.Label(ctrl, text='RotMG: Unknown', font=('Consolas',12), fg='#00FF00', bg='black')
    lbl_next = tk.Label(ctrl, text='Next hunt in: N/A', font=('Consolas',12), fg='#BBBBBB', bg='black')
    lbl_rotmg.pack(side=tk.LEFT, padx=5)
    lbl_next.pack(side=tk.LEFT, padx=5)
    tk.Label(ctrl, text='Interval (s):', fg='#BBBBBB', bg='black').pack(side=tk.LEFT)
    iv = tk.IntVar(value=DEFAULT_INTERVAL)
    sb = tk.Spinbox(ctrl, from_=1, to=30, width=4, textvariable=iv)
    sb.pack(side=tk.LEFT, padx=5)

    # Webhook input
    tk.Label(ctrl, text='Webhook URL:', fg='#BBBBBB', bg='black').pack(side=tk.LEFT)
    wh_var = tk.StringVar(value='')
    ent_wh = tk.Entry(ctrl, textvariable=wh_var, width=30)
    ent_wh.pack(side=tk.LEFT, padx=5)
    cfg_btn = dict(bg='#222222', fg='#AA0000', activebackground='#550000', activeforeground='#FFFFFF', width=12, bd=1, relief='raised')
    btn_apply = tk.Button(ctrl, text='APPLY', **cfg_btn)
    btn_apply.pack(side=tk.LEFT, padx=5)
    def apply_wh():
        nonlocal ent_wh, wh_var
        target_webhook = wh_var.get().strip()
        save_webhook(target_webhook)
        send_webhook('🎯 **Webhook setup correctly!** Ready to start hunting.')
        wh_label.config(text='Webhook: Active', fg='#00FF00')
        log_fh.write(f"[{time.strftime('%H:%M:%S')}] Webhook configured: {target_webhook}\n")
        ent_wh.delete(0, tk.END)
    btn_apply.config(command=apply_wh)
    ctrl.pack(pady=10)

    # Progress bar
    style = ttk.Style(); style.theme_use('default')
    style.configure('DH.Horizontal.TProgressbar', troughcolor='black', background='#880000', thickness=12)
    prog = ttk.Progressbar(root, style='DH.Horizontal.TProgressbar', mode='determinate', length=400, maximum=iv.get())
    prog.pack(pady=(0,10))
    iv.trace_add('write', lambda *_: prog.config(maximum=iv.get()))

    # Webhook status label
    wh_label = tk.Label(root, text=f"Webhook: {'Active' if target_webhook else 'Inactive'}",
                        fg='#00FF00' if target_webhook else '#FF4444', bg='black', font=('Consolas',10))
    wh_label.pack(fill=tk.X, padx=10)

    # Log window
    txt = scrolledtext.ScrolledText(root, state='disabled', bg='black', fg='#BBBBBB', insertbackground='#FF8888', font=('Consolas',10), height=12)
    txt.tag_config('INFO', foreground='#BBBBBB'); txt.tag_config('WARN', foreground='#FF4444'); txt.tag_config('SUCCESS', foreground='#00FF00')
    txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
    def log(msg, level='INFO'):
        ts = time.strftime('%H:%M:%S'); entry = f'[{ts}] {msg}\n'
        txt.config(state='normal'); txt.insert(tk.END, entry, level); txt.see(tk.END); txt.config(state='disabled')
        try: log_fh.write(entry)
        except: pass

    # Pulse setup
    pulse_flag = False
    def pulse():
        nonlocal pulse_flag
        # Alternate fg for pulsing
        if hunting_status.winfo_ismapped():
            hunting_status.config(fg='#880000' if pulse_flag else '#440000')
            pulse_flag = not pulse_flag
            root.after(500, pulse)

    # Monitoring logic
    stop_evt = threading.Event()
    detection_count = 0
    
    def start_hunt():
        nonlocal detection_count
        detection_count = 0
        if not hunting_status.winfo_ismapped(): hunting_status.pack(pady=(0,5))
        send_webhook(f'🏹 **Admin hunting started!** ⏱️ Interval: {iv.get()}s')
        log(f'Start hunting with interval {iv.get()}s', 'SUCCESS')
        hunting_status.config(text='Hunting: Active', fg='#AA0000')
        btn_start.config(state='disabled'); btn_stop.config(state='normal')
        threading.Thread(target=hunt_loop, daemon=True).start()
        
    def handle_detect(admin_data):
        nonlocal detection_count
        detection_count += 1
        
        # Keep hunting status visible and active
        hunting_status.config(text=f'Hunting: Active (Detections: {detection_count})', fg='#FF0000')
        
        log(f'🚨 Admin spotted #{detection_count}! Terminating RotMG and continuing hunt...', 'WARN')
        lbl_rotmg.config(text='ADMIN SPOTTED', fg='#FF0000')
        subprocess.run(['taskkill','/F','/IM',ROTMG_EXE], check=False)
        
        # Send detailed webhook alert
        alert_msg = create_admin_alert_message(admin_data)
        send_webhook(alert_msg)
        
        # Enhanced logging
        log(f'Admin ID {admin_data["player_id"]} on {admin_data["server"]} ({admin_data["region"]}) at {admin_data["time"]}', 'WARN')
        log(f'🔄 Continuing hunt in {iv.get()} seconds... (Total detections: {detection_count})', 'INFO')
        
        # Brief pause before continuing (uses same interval)
        for i in range(iv.get(), 0, -1):
            if stop_evt.is_set(): return
            lbl_next.config(text=f'Resuming hunt in: {i}s')
            time.sleep(1)
        
        log('🔄 Resuming hunt...', 'SUCCESS')
        
    def hunt_loop():
        while not stop_evt.is_set():
            log('🕵️ Hunting for admins...', 'INFO')
            try:
                r = requests.get(URL, timeout=5)
                lines = r.json().get('value','').splitlines() if r.ok else []
                admin_data = parse_admin_data(lines)
                if admin_data: 
                    handle_detect(admin_data)  # Continue hunting after detection
                else: 
                    log('No admins found.','INFO')
            except Exception as e: 
                log(f'Error: {e}','WARN')
            
            # Normal interval countdown
            for i in range(iv.get(), 0, -1):
                if stop_evt.is_set(): return
                lbl_next.config(text=f'Next hunt in: {i}s'); prog['value'] = iv.get() - i; time.sleep(1)
            prog['value'] = iv.get()

    # Control buttons
    btn_frame = tk.Frame(root, bg='black')
    btn_start = tk.Button(btn_frame, text='START', command=start_hunt, **cfg_btn)
    def stop_hunt():
        stop_evt.set()
        hunting_status.pack_forget()
        btn_stop.config(state='disabled')
        btn_start.config(state='normal')
        send_webhook(f'🛑 **Admin hunting stopped!** Total detections: {detection_count}')
        log('🛑 Hunting stopped by user', 'WARN')
        lbl_next.config(text='Hunt stopped')
        
    btn_stop = tk.Button(btn_frame, text='STOP', state='disabled', command=stop_hunt, **cfg_btn)
    btn_exit = tk.Button(btn_frame, text='EXIT', command=lambda: sys.exit(0), **cfg_btn)
    btn_start.pack(side=tk.LEFT, padx=5); btn_stop.pack(side=tk.LEFT, padx=5); btn_exit.pack(side=tk.LEFT, padx=5)
    btn_frame.pack(pady=10)

    # RotMG status update
    def update_status():
        running = is_rotmg_running()
        # Only update if not currently showing "ADMIN SPOTTED"
        if lbl_rotmg.cget('text') != 'ADMIN SPOTTED':
            lbl_rotmg.config(text='RotMG: RUNNING' if running else 'RotMG: NOT RUNNING', fg='#00FF00' if running else '#FF0000')
        root.after(2000, update_status)
    root.after(1000, update_status)

    # Auto-size window
    root.update_idletasks(); root.minsize(root.winfo_width(), root.winfo_height())
    log_fh.write(f"[{time.strftime('%H:%M:%S')}] Launched. Logs: {log_fh.name}\n")
    root.mainloop()

if __name__=='__main__':
    main()

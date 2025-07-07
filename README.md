
# Admin Hunter by Macky

**Admin Hunter** is a Windows GUI application that monitors *Realm of the Mad God* (RotMG) for administrative presence, immediately terminates the game if an admin appears, and sends alerts via Discord webhooks.

---

## 💡 Features

- **Auto-Elevation**: Prompts for UAC if not running as administrator.
- **Dark-Themed UI**: Custom InvisibleKiller font (falls back to Helvetica), blood-red accents, animated GIF side sprites.
- **Adjustable Polling**: Set check interval from 1 to 30 seconds with a determinate progress bar.
- **Discord Webhook Alerts**: Send notifications to a Discord channel on hunt start and admin detection.
- **Desktop & Sound Alerts**: Uses `plyer` for toast notifications and `winsound` for an audible beep on detection.
- **System Tray Integration**: Minimize to tray with `pystray`; right-click tray icon to restore or exit.
- **Hunting Status Indicator**: Hidden until active, then shows a pulsing “Hunting: Active” label.
- **Log Management**: Retains 7 days of logs in `Desktop/AdminHunterLogs` and streams INFO/WARN entries in-app.

---

## 🔧 Prerequisites

- **OS:** Windows 10 or 11
- **Python:** 3.8 or newer (only for development—end users can use the standalone EXE)
- **Python Packages:**
  ```bash
  pip install requests pystray pillow plyer
  ```
- **Assets:** Place `nqtKzsh.gif` and `mGzCi6Z.gif` next to `admin_hunter.py`.
- **Font:** InvisibleKiller.ttf
---

## ▶️ Running Locally

1. Open a **standard** (non-admin) Command Prompt in the project directory.
2. Run:
   ```bash
   python admin_hunter.py
   ```
3. Approve the UAC prompt to elevate.
4. Enter your **Discord Webhook URL** in the text box and click **APPLY**.
5. Adjust the **Interval (s)** spinner to your desired polling frequency.
6. Click **START** to begin hunting; a pulsing status label appears.
7. Click **STOP** to pause hunting; close the window to minimize to tray.

---

## 📦 Building a Standalone EXE

From the same directory as `admin_hunter.py` and the GIFs, run:

```bat
pyinstaller --onefile --windowed   --add-data "nqtKzsh.gif;."   --add-data "mGzCi6Z.gif;."   admin_hunter.py
```

- The compiled executable will appear in `dist/admin_hunter.exe`.
- Ship the single EXE—no Python install required.

---
## EXE Included but not Recommended

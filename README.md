# 🌱 RootBox Project

RootBox is a Raspberry Pi–based automated root observation system designed to scan and monitor plant root growth over time. It supports multiple USB flatbed scanners, provides a local web interface for configuration, and logs all activity for future analysis.

## 📦 Features

- Supports **1–6 USB scanners**, each with independent settings
- Automatically scans at user-defined **intervals** and **resolutions**
- Stores images in timestamped files inside per-scanner folders
- Built-in **web GUI** to:
  - Enable/disable scanners
  - Assign scanner labels
  - Set scan frequency and DPI resolution
  - Choose which USB scanner is assigned
  - View the last 50 lines of system logs (collapsible panel)
  - Trigger **manual scans** per scanner
  - Start and stop the scanning controller
- **Desktop shortcut** created on the Pi desktop to launch the web GUI
- Auto-detects connected scanner devices via background service
- Logs system activity in a rotating log file (`logs/control_log.txt`)
- Uses simple **JSON** config files — no database or internet required
- Future expansion: automatic image upload, root tracking via AI


## 🖥️ Accessing the Web GUI

Once installed either:

- Open a browser and navigate to:
  ```
  http://<raspberry pi ip address>:5000
  ```
OR

- Use Real VNC viewer and log into <Raspberry Pi IP> Port 5900				

OR

- Open any browser on the Raspberry Pi
- Navigate to:  
  ```
  http://localhost:5000
  ```

OR use the desktop shortcut:

### 📁 Desktop Shortcut

The installer automatically creates a shortcut on the Raspberry Pi desktop:

- 📌 **RootBox GUI** → double-click to open the web interface in your browser
- It runs:  
  ```
  xdg-open http://localhost:5000
  ```

This makes it easy to access the GUI without typing anything.



## ⚙️ How to Install

1. Install **Raspberry Pi OS with Desktop**  
   (Make sure it's connected to the internet, SSH enabled and its in the right timezone)
2. SSH into the Pi or open a terminal
3. Run this command:
   ```bash
   bash <(curl -s https://raw.githubusercontent.com/Mr-Vale/RootBox-Software/main/install.sh)
   ```
4. Wait for installation to complete
5. Reboot the Pi before first use



## 🔄 Service Management Commands

Check all running services:
```bash
sudo systemctl status
```

Check RootBox web GUI service:
```bash
sudo systemctl status rootbox-gunicorn.service
```

Restart RootBox web GUI:
```bash
sudo systemctl restart rootbox-gunicorn.service
```

Check Scanner Auto-Detect service:
```bash
sudo systemctl status rootbox-scanner-autodetect.service
```

Restart Scanner Auto-Detect service:
```bash
sudo systemctl restart rootbox-scanner-autodetect.service
```



## 🧰 Project Structure

```
~/RootBox/
├── 00_scan_control.py          # Main controller (scheduled scanning)
├── 01_scan_image.py            # Triggers single scanner image capture
├── 02_image_manager.py         # Deletes old scans, manages disk space
├── 03_Scanner_Autodetect.py    # Auto-detects USB scanner connections
├── venv/                       # Python virtual environment
├── web/
│   ├── app.py                  # Flask web server
│   ├── templates/
│   │   └── index.html          # HTML interface
│   ├── settings.json           # Scanner settings and state
│   └── scanner_devices.json    # Auto-generated scanner device list
├── logs/
│   └── control_log.txt         # Controller log output
├── scan_images/
│   └── scanner01/..scanner06/  # Output image folders
└── controller.pid              # Tracks control script PID
```

---

## 💬 Questions?

- Need help ? - sorry I am not avaiable
---

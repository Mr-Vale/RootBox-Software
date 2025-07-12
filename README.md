# 🌱 RootBox Project

RootBox is a Raspberry Pi–based automated root observation system designed to scan and monitor plant root growth over time. It supports multiple USB flatbed scanners, provides a Flask-based web interface for control, and logs all activity for later analysis.

---
How to Install:

1. Install full Desktop Raspberry PI OS (ensure SSH is enabled and connected to the internet)
2. Login to PI with SSH
3. Copy the complete next line and run it

bash <(curl -s https://raw.githubusercontent.com/Mr-Vale/RootBox-Software/main/install.sh)

4. Should perform a reboot before using

---
Service Management Commands:

Check all running services:
  sudo systemctl status

Check custom web hosting service:
  sudo systemctl status rootbox-gunicorn.service

Restart custom web hosting service:
  sudo systemctl restart rootbox-gunicorn.service

Check custom scanner detect service:
  sudo systemctl status rootbox-scanner-autodetect.service

Restart custom scanner detect service:
  sudo systemctl restart rootbox-scanner-autodetect.service

---

## 📦 Features

- Supports **1–6 scanners**, each with independent settings
- Scans roots on a schedule with user-defined **intervals and resolutions**
- Stores images with timestamped filenames in per-scanner folders
- Web GUI to:
  - Enable/disable scanners
  - Assign labels
  - Set scan frequency and resolution
  - Choose connected scanner devices
  - Start/stop the control service
- Automatically rotates log files and manages local disk space
- JSON-based configuration — no database required
- Future expansion: image upload, AI root tracking

---

## 🧰 Project Structure

~/RootBox/
├── 00_scan_control.py # Main control loop
├── 01_scan_image.py # Scans an image from a specific scanner
├── 02_image_manager.py # Cleans up old images and manages disk space
├── 03_Scanner_Autodetect.py # Monitors connected USB scanner devices
├── web/
│ ├── app.py # Flask web interface
│ ├── templates/
│ │ └── index.html # HTML interface
│ ├── settings.json # Stores scanner configurations
│ └── scanner_devices.json # Auto-updated list of attached scanner devices
├── logs/
│ └── control_log.txt # Rolling log of system actions
├── scan_images/ # Stores scan output
│ └── scanner01/... # Images organized by scanner
└── controller.pid # PID tracking for the control loop

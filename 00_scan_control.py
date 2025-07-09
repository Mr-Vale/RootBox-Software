import subprocess
import time
import json
import os
from datetime import datetime, timedelta

# Define dynamic paths
HOME_DIR = os.path.expanduser("~")
ROOTBOX_DIR = os.path.join(HOME_DIR, "RootBox")

SETTINGS_PATH = os.path.join(ROOTBOX_DIR, 'web', 'settings.json')
LOG_DIR = os.path.join(ROOTBOX_DIR, 'logs')
LOG_PATH = os.path.join(LOG_DIR, 'control_log.txt')
PID_FILE = os.path.join(ROOTBOX_DIR, 'controller.pid')

SCAN_IMAGE_SCRIPT = os.path.join(ROOTBOX_DIR, '01_scan_image.py')
IMAGE_MANAGER_SCRIPT = os.path.join(ROOTBOX_DIR, '02_image_manager.py')

def rotate_log():
    os.makedirs(LOG_DIR, exist_ok=True)

    if os.path.exists(LOG_PATH):
        timestamp = datetime.now().strftime('%d-%m-%Y-%H-%M')
        archived_log = os.path.join(LOG_DIR, f"control_log_{timestamp}.txt")
        os.rename(LOG_PATH, archived_log)

    log_files = sorted(
        [f for f in os.listdir(LOG_DIR) if f.startswith("control_log") and f.endswith(".txt")],
        key=lambda f: os.path.getmtime(os.path.join(LOG_DIR, f))
    )

    while len(log_files) > 5:
        oldest = log_files.pop(0)
        try:
            os.remove(os.path.join(LOG_DIR, oldest))
        except Exception as e:
            print(f"⚠️ Failed to delete old log {oldest}: {e}")

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_PATH, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def load_settings():
    try:
        with open(SETTINGS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        log(f"⚠️ Failed to load settings: {e}")
        return {}

# Rotate log at startup
rotate_log()

# Write PID
with open(PID_FILE, 'w') as f:
    f.write(str(os.getpid()))

log("🟢 Controller started.")

last_run_times = {}

try:
    while True:
        settings = load_settings()
        scanners = settings.get("scanners", {})

        for scanner_id, config in scanners.items():
            label = config.get("label", scanner_id)
            enabled = config.get("enabled", False)
            interval = config.get("interval_minutes", 60)
            resolution = config.get("resolution", 150)

            if not enabled:
                continue

            now = datetime.now()
            last_run = last_run_times.get(scanner_id, now - timedelta(minutes=interval + 1))
            elapsed = (now - last_run).total_seconds() / 60

            if elapsed >= interval:
                log(f"▶ Running scan for {scanner_id} ({label}) at {resolution}dpi")

                try:
                    subprocess.run(["python3", SCAN_IMAGE_SCRIPT, scanner_id], check=True)
                    last_run_times[scanner_id] = datetime.now()
                    log(f"✅ Scan complete for {scanner_id}")
                except subprocess.CalledProcessError as e:
                    log(f"❌ Scan failed for {scanner_id}: {e}")
            else:
                log(f"⏳ Skipping {scanner_id} — next scan in {interval - int(elapsed)} min")

        try:
            subprocess.run(["python3", IMAGE_MANAGER_SCRIPT], check=True)
            log("🧹 Image manager complete.")
        except subprocess.CalledProcessError as e:
            log(f"❌ Image manager failed: {e}")

        time.sleep(30)

except KeyboardInterrupt:
    log("🛑 Controller stopped by keyboard.")
except Exception as e:
    log(f"❗ Unexpected error: {e}")
finally:
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

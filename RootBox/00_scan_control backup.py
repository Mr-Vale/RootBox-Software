import subprocess
import time
import json
import os
from datetime import datetime, timedelta

#Find user home path and create folder directory
HOME_DIR = os.path.expanduser("~")
ROOTBOX_DIR = os.path.join(HOME_DIR, "RootBox")


SETTINGS_PATH = os.path.join(ROOTBOX_DIR, 'web', 'settings.json')
LOG_PATH = os.path.join(ROOTBOX_DIR, 'logs', 'control_log.txt')
PID_FILE = os.path.join(ROOTBOX_DIR, 'controller.pid')


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
                    subprocess.run(
                        ["python3", "/home/Admin/RootBox/01_scan_image.py", scanner_id],
                        check=True
                    )
                    last_run_times[scanner_id] = datetime.now()
                    log(f"✅ Scan complete for {scanner_id}")
                except subprocess.CalledProcessError as e:
                    log(f"❌ Scan failed for {scanner_id}: {e}")
            else:
                log(f"⏳ Skipping {scanner_id} — next scan in {interval - int(elapsed)} min")

        # Run image manager every loop
        try:
            subprocess.run(
                ["python3", "/home/Admin/RootBox/02_image_manager.py"],
                check=True
            )
            log("🧹 Image manager complete.")
        except subprocess.CalledProcessError as e:
            log(f"❌ Image manager failed: {e}")

        time.sleep(30)  # check again every 30 seconds

except KeyboardInterrupt:
    log("🛑 Controller stopped by keyboard.")
except Exception as e:
    log(f"❗ Unexpected error: {e}")
finally:
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

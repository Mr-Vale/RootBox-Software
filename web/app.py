from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
import subprocess
import signal
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'rootbox-secret'  # Replace with secure key in production

#Find user home path and create folder directory
HOME_DIR = os.path.expanduser("~")
ROOTBOX_DIR = os.path.join(HOME_DIR, "RootBox")

# File paths
SETTINGS_PATH = os.path.join(ROOTBOX_DIR, 'web', 'settings.json')
DEVICES_PATH = os.path.join(ROOTBOX_DIR,'web','scanner_devices.json')
PID_FILE = os.path.join(ROOTBOX_DIR, 'controller.pid')
CONTROL_SCRIPT = os.path.join(ROOTBOX_DIR,'00_scan_control.py')

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def is_controller_running():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return True
        except Exception:
            return False
    return False

def start_controller():
    if not is_controller_running():
        subprocess.Popen(['python3', CONTROL_SCRIPT])
        return True
    return False

def stop_controller():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            os.remove(PID_FILE)
            return True
        except Exception:
            return False
    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    settings = load_json(SETTINGS_PATH)
    devices_json = load_json(DEVICES_PATH)
    available_devices = devices_json.get('devices', [])
    scanners = settings.get('scanners', {})

    if request.method == 'POST':
        for scanner_id in scanners.keys():
            label = request.form.get(f'label_{scanner_id}', '').strip()
            enabled = request.form.get(f'enabled_{scanner_id}') == 'on'
            interval = int(request.form.get(f'interval_{scanner_id}', '60'))
            resolution = int(request.form.get(f'res_{scanner_id}', '150'))
            device = request.form.get(f'device_{scanner_id}', '')

            scanners[scanner_id].update({
                'label': label,
                'enabled': enabled,
                'interval_minutes': interval,
                'resolution': resolution,
                'device': device
            })

        settings['scanners'] = scanners
        save_json(SETTINGS_PATH, settings)
        flash("Settings saved successfully.", "success")
        return redirect(url_for('index'))

    # 🔽 Calculate estimated time remaining per scanner
    countdowns = {}
    now = datetime.now()
    for scanner_id, config in scanners.items():
        if config.get("enabled") and "last_scan" in config:
            try:
                last_scan = datetime.fromisoformat(config["last_scan"])
                interval = config.get("interval_minutes", 60)
                next_scan = last_scan + timedelta(minutes=interval)
                remaining_td = next_scan - now
                if remaining_td.total_seconds() > 0:
                    total_minutes = int(remaining_td.total_seconds() // 60)
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    countdowns[scanner_id] = f"{hours:02}:{minutes:02}"
                else:
                    countdowns[scanner_id] = "00:00"

            except Exception:
                countdowns[scanner_id] = None
        else:
            countdowns[scanner_id] = None

    # 🔽 Detect duplicates
    device_count = {}
    for config in scanners.values():
        device = config.get('device')
        if device:
            device_count[device] = device_count.get(device, 0) + 1
    duplicate_devices = {dev for dev, count in device_count.items() if count > 1}

    running = is_controller_running()
    return render_template(
        'index.html',
        scanners=scanners,
        available_devices=available_devices,
        running=running,
        duplicate_devices=duplicate_devices,
        countdowns=countdowns
    )

@app.route('/start', methods=['POST'])
def start():
    start_controller()
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    stopped = stop_controller()

    if stopped:
        settings = load_json(SETTINGS_PATH)
        for config in settings.get('scanners', {}).values():
            config.pop("last_scan", None)  # remove the timer
        save_json(SETTINGS_PATH, settings)

    return redirect(url_for('index'))
    
@app.route('/manual_scan/<scanner_id>', methods=['POST'])
def manual_scan(scanner_id):
    try:
        result = subprocess.run(
            ['python3', os.path.join(ROOTBOX_DIR, '01_scan_image.py'), scanner_id],
            check=True
        )
        flash(f"✅ Manual scan for {scanner_id} completed successfully.", "success")
    except subprocess.CalledProcessError as e:
        flash(f"❌ Manual scan for {scanner_id} failed: {e}", "danger")
    return redirect(url_for('index'))

@app.route('/log')
def view_log():
    log_path = os.path.join(ROOTBOX_DIR, 'logs', 'control_log.txt')
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
        last_lines = lines[-50:]
        return ''.join(last_lines)
    except Exception as e:
        return f"⚠️ Error reading log file: {e}"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

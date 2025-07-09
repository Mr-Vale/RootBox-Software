import sys
import os
import json
import datetime
import subprocess

# Find user home and RootBox directory
HOME_DIR = os.path.expanduser("~")
ROOTBOX_DIR = os.path.join(HOME_DIR, "RootBox")

SETTINGS_PATH = os.path.join(ROOTBOX_DIR, 'web', 'settings.json')
SCAN_IMAGES_DIR = os.path.join(ROOTBOX_DIR, 'scan_images')

def load_settings():
    try:
        with open(SETTINGS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load settings: {e}")
        return {}

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 01_scan_image.py scanner_id")
        sys.exit(1)

    scanner_id = sys.argv[1]

    settings = load_settings()
    scanners = settings.get("scanners", {})

    if scanner_id not in scanners:
        print(f"Scanner ID '{scanner_id}' not found in settings.")
        sys.exit(1)

    config = scanners[scanner_id]
    label = config.get("label", scanner_id).replace(" ", "_")
    device = config.get("device", "")
    resolution = config.get("resolution", 150)

    # Prepare folder for this scanner
    scanner_folder = os.path.join(SCAN_IMAGES_DIR, scanner_id)
    os.makedirs(scanner_folder, exist_ok=True)

    # Timestamp for filename
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y-%H%M")

    filename = f"{scanner_id}-{label}-{timestamp}.png"
    filepath = os.path.join(scanner_folder, filename)

    # Build scan command
    # Example using scanimage (must be installed, supports device selection)
    # You may need to adjust options depending on your scanner and drivers.
    scan_cmd = [
        "scanimage",
        "-d", device,
        "--format=png",
        f"--resolution={resolution}",
        "--mode", "Color",
       # "--depth", "8",
        "--batch={}".format(filepath),
        "--batch-start=1",
        "--batch-count=1"
    ]

    try:
        print(f"Starting scan for {scanner_id} ({label}) at {resolution} dpi...")
        subprocess.run(scan_cmd, check=True)
        print(f"Scan saved to {filepath}")
    except subprocess.CalledProcessError as e:
        print(f"Scan failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

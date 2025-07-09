import time
import subprocess
import json
import re
import os

#Find user home path and create folder directory
HOME_DIR = os.path.expanduser("~")
ROOTBOX_DIR = os.path.join(HOME_DIR, "RootBox")

OUTPUT_PATH = os.path.join(ROOTBOX_DIR,'web','scanner_devices.json')

def detect_scanners():
    try:
        result = subprocess.run(['scanimage', '-L'], capture_output=True, text=True, check=True)
        devices = []
        for line in result.stdout.strip().splitlines():
            match = re.match(r"device `(.*?)'", line)
            if match:
                devices.append(match.group(1))
        if devices:
           # return [devices[0]]  # Return only the first device as a single-item list
           return devices         # Return all detected devices
        else:
            return []
    except Exception as e:
        print(f"Error detecting scanners: {e}")
        return []

def save_devices(devices):
    try:
        with open(OUTPUT_PATH, 'w') as f:
            json.dump({"devices": devices}, f, indent=2)
    except Exception as e:
        print(f"Error saving devices: {e}")

def main():
    while True:
        devices = detect_scanners()
        save_devices(devices)
        time.sleep(10)  # wait 10 seconds before next scan

if __name__ == "__main__":
    main()

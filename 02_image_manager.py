import os
import shutil
from datetime import datetime

#Find user home path and create folder directory
HOME_DIR = os.path.expanduser("~")
ROOTBOX_DIR = os.path.join(HOME_DIR, "RootBox")

# Configuration
#SCRIPT_DIR = "/home/Admin/RootBox"
SCAN_DIR = os.path.join(ROOTBOX_DIR, "scan_images")
OLD_DIR = os.path.join(ROOTBOX_DIR, "old")
LOG_FILE = os.path.join(ROOTBOX_DIR, "logs", "control_log.txt")
MAX_IMAGES = 10
OLD_SIZE_LIMIT_BYTES = int(3 * 1024**3)  # 3 GB

def log(scanner, message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    entry = f"{timestamp} [{scanner}] [Image Manager] {message}"
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")
    print(entry)

def get_scanner_folders():
    return [d for d in os.listdir(SCAN_DIR)
            if os.path.isdir(os.path.join(SCAN_DIR, d)) and d.startswith("scanner")]

def get_folder_size(path):
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except FileNotFoundError:
                pass
    return total

def manage_old_folder():
    if not os.path.exists(OLD_DIR):
        return

    folder_size = get_folder_size(OLD_DIR)
    if folder_size >= OLD_SIZE_LIMIT_BYTES:
        for f in os.listdir(OLD_DIR):
            file_path = os.path.join(OLD_DIR, f)
            try:
                os.remove(file_path)
            except Exception as ex:
                log("System", f"Error deleting old file {f}: {ex}")
        log("System", f"Deleted all files in 'old/' folder (used {folder_size / 1024**3:.2f} GB)")

def manage_images(scanner):
    folder = os.path.join(SCAN_DIR, scanner)
    os.makedirs(OLD_DIR, exist_ok=True)

    try:
        images = [f for f in os.listdir(folder) if f.endswith(".png")]
        images.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)))

        while len(images) > MAX_IMAGES:
            oldest = images.pop(0)
            src = os.path.join(folder, oldest)
            dst = os.path.join(OLD_DIR, oldest)
            shutil.move(src, dst)
            log(scanner, f"Moved image to old/: {oldest}")

    except Exception as ex:
        log(scanner, f"ERROR managing images: {ex}")

def main():
    scanners = get_scanner_folders()
    if not scanners:
        log("System", "No scanner folders found.")
    for scanner in scanners:
        manage_images(scanner)

        # ------------------------------
        # 📤 REMOTE UPLOAD PLACEHOLDER
        # TODO: Add remote server upload logic here.
        # Example:
        # upload_latest_image(scanner, "/remote/path", "user", "host")
        # Optional: repeat upload for redundancy
        # ------------------------------

    manage_old_folder()

if __name__ == "__main__":
    main()

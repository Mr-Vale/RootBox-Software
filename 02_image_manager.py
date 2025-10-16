import os
import shutil
import json
import pickle
import time
from datetime import datetime
import getpass

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# -----------------------------
# CONFIG
# -----------------------------
HOME_DIR = os.path.expanduser("~")
ROOTBOX_DIR = os.path.join(HOME_DIR, "RootBox")

SCAN_DIR = os.path.join(ROOTBOX_DIR, "scan_images")
OLD_DIR = os.path.join(ROOTBOX_DIR, "old")
LOG_FILE = os.path.join(ROOTBOX_DIR, "logs", "control_log.txt")

LAST_UPLOAD_FILE = os.path.join(ROOTBOX_DIR, "last_upload.json")

MAX_IMAGES = 10
OLD_SIZE_LIMIT_BYTES = int(20 * 1024**3)  # 20 GB

# Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_PATH = os.path.join(ROOTBOX_DIR, "creds", "token.pickle")
CREDENTIALS_PATH = os.path.join(ROOTBOX_DIR, "creds", "credentials.json")

# Root folder in Google Drive where "scanner01", "scanner02" etc. exist
DRIVE_ROOT_FOLDER_ID = "1my_IEvjcIxUgUBlKN-GCfrOMm3_0Cpu9"  # your upload-folder ID

# USB copy configuration
# Set USB_IMAGE_COPY_PATH environment variable to override a single default path.
USB_IMAGE_COPY_PATH = os.environ.get("USB_IMAGE_COPY_PATH", "/media/usb/RootBox")
# Set USB_SEARCH_PATHS to a comma-separated list of base paths to search for mounts.
# Use {USER} placeholder to inject the current user (e.g. "/media/{USER}").
# Default tries /media/<user>, /run/media/<user>, /media and /mnt
USB_SEARCH_PATHS = os.environ.get("USB_SEARCH_PATHS", "")

# -----------------------------
# UTILS
# -----------------------------
def log(scanner, message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    entry = f"{timestamp} [{scanner}] [Image Manager] {message}"
    # Ensure log directory exists
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(entry + "\n")
    except Exception:
        # If log file can't be written, still print so debugging is possible
        pass
    print(entry)

def load_last_uploads():
    if os.path.exists(LAST_UPLOAD_FILE):
        with open(LAST_UPLOAD_FILE, "r") as f:
            return json.load(f)
    return {}

def save_last_uploads(data):
    os.makedirs(os.path.dirname(LAST_UPLOAD_FILE), exist_ok=True)
    with open(LAST_UPLOAD_FILE, "w") as f:
        json.dump(data, f)

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

# -----------------------------
# USB detection helper
# -----------------------------
def get_usb_mounts():
    """
    Return a list of detected USB mount roots to copy images to.
    Strategy:
      - Use USB_SEARCH_PATHS env if provided (comma-separated).
      - Otherwise search defaults: /media/<user>, /run/media/<user>, /media, /mnt
    Only include candidates that are actual mountpoints and writable.
    """
    mounts = []
    user = getpass.getuser()

    if USB_SEARCH_PATHS:
        bases = [p.replace("{USER}", user) for p in USB_SEARCH_PATHS.split(",")]
    else:
        bases = [f"/media/{user}", f"/run/media/{user}", "/media", "/mnt"]

    def is_writable_dir(p):
        try:
            return os.path.isdir(p) and os.access(p, os.W_OK | os.X_OK)
        except Exception:
            return False

    for base in bases:
        try:
            if not os.path.isdir(base):
                continue
            # Include immediate children that are mountpoints AND writable
            for name in os.listdir(base):
                candidate = os.path.join(base, name)
                if os.path.ismount(candidate) and is_writable_dir(candidate):
                    mounts.append(candidate)
            # Include the base itself only if it is a mountpoint and writable (rare)
            if os.path.ismount(base) and is_writable_dir(base):
                mounts.append(base)
        except Exception:
            continue

    # Deduplicate while preserving order
    seen = set()
    result = []
    for m in mounts:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result

# -----------------------------
# USB helper (copy)
# -----------------------------
def copy_to_usb(src_path, scanner, usb_root=USB_IMAGE_COPY_PATH):
    """
    Copy the image to a mounted USB drive. This attempts to create a structured
    destination: <usb_root>/scan_images/<scanner>/
    Returns True on success, False on failure.
    Behavior: If the configured usb_root does not exist, this logs and returns False.
    """
    try:
        # Basic existence check for the USB root. If the mount isn't present, bail out.
        if not os.path.exists(usb_root):
            raise FileNotFoundError(f"USB root not found at {usb_root}")

        dest_dir = os.path.join(usb_root, "scan_images", scanner)
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, os.path.basename(src_path))
        shutil.copy2(src_path, dest_path)
        log(scanner, f"Copied {os.path.basename(src_path)} to USB at {dest_path}")
        return True
    except Exception as ex:
        log(scanner, f"Failed copying to USB ({usb_root}): {ex}")
        return False

# -----------------------------
# GOOGLE DRIVE HELPERS
# -----------------------------
def get_creds():
    """
    Policy:
    - Only token.pickle exists -> use it (and refresh if possible).
    - Only credentials.json exists -> skip (headless, no OAuth flow).
    - Both missing -> skip.
    - Token exists but invalid and cannot refresh, and credentials.json is missing -> skip.
    Note: Even if credentials.json exists alongside token, we DO NOT run an OAuth flow in headless mode.
    """
    try:
        token_exists = os.path.exists(TOKEN_PATH)
        creds_json_exists = os.path.exists(CREDENTIALS_PATH)

        if token_exists:
            try:
                with open(TOKEN_PATH, 'rb') as f:
                    creds = pickle.load(f)
            except Exception as ex:
                log("System", f"Failed to load token from {TOKEN_PATH}: {ex}. Skipping cloud upload.")
                return None

            if creds and getattr(creds, "valid", False):
                return creds

            if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
                try:
                    creds.refresh(Request())
                    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
                    with open(TOKEN_PATH, 'wb') as tf:
                        pickle.dump(creds, tf)
                    return creds
                except Exception as ex:
                    log("System", f"Token refresh failed: {ex}. Skipping cloud upload.")
                    return None

            # Token exists but not valid and cannot refresh
            log("System", "Token present but invalid and cannot refresh. Skipping cloud upload.")
            return None

        # No token file
        if not token_exists and creds_json_exists:
            log("System", "Only credentials.json present; headless mode skips OAuth flow. Skipping cloud upload.")
            return None

        log("System", "No token.pickle and no credentials.json found. Skipping cloud upload.")
        return None
    except Exception as ex:
        log("System", f"Error resolving Google Drive credentials: {ex}. Skipping cloud upload.")
        return None

def get_or_create_drive_folder(service, parent_id, folder_name):
    query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    resp = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = resp.get('files', [])
    if files:
        return files[0]['id']
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']

def upload_latest_image(scanner, latest_file, latest_timestamp, last_uploads):
    # First: detect USB mounts and attempt to copy to every detected USB
    try:
        usb_mounts = get_usb_mounts()
        if not usb_mounts:
            log(scanner, "No USB mounts detected; skipping local USB backup")
        else:
            log(scanner, f"Detected USB mounts: {usb_mounts}")
            for mount in usb_mounts:
                try:
                    ok = copy_to_usb(latest_file, scanner, usb_root=mount)
                    if not ok:
                        log(scanner, f"Copy to USB {mount} failed; continuing")
                except Exception as ex:
                    log(scanner, f"Error copying to USB {mount}: {ex}")

    except Exception as ex:
        # best-effort: do not block upload
        log(scanner, f"Unexpected error detecting/copying USB mounts: {ex}")

    # Then: upload to Google Drive as before (best-effort)
    try:
        creds = get_creds()
        if not creds:
            raise RuntimeError("No valid Google Drive credentials available.")
        service = build('drive', 'v3', credentials=creds)
        folder_id = get_or_create_drive_folder(service, DRIVE_ROOT_FOLDER_ID, scanner)
        file_metadata = {'name': os.path.basename(latest_file), 'parents': [folder_id]}
        media = MediaFileUpload(latest_file, resumable=True)
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        log(scanner, f"Uploaded {os.path.basename(latest_file)} to Google Drive")
        # Only mark as uploaded on success
        last_uploads[scanner] = latest_timestamp
        save_last_uploads(last_uploads)
    except Exception as ex:
        log(scanner, f"Cloud upload failed: {ex}. Will retry next cycle.")

# -----------------------------
# MAIN
# -----------------------------
def main():
    last_uploads = load_last_uploads()

    scanners = get_scanner_folders()
    if not scanners:
        log("System", "No scanner folders found.")
    for scanner in scanners:
        try:
            manage_images(scanner)

            folder = os.path.join(SCAN_DIR, scanner)
            images = [f for f in os.listdir(folder) if f.endswith(".png")]

            if not images:
                continue

            # Find newest by unix timestamp in filename
            try:
                images.sort(key=lambda f: int(f.split("-")[-1].replace(".png", "")))
            except ValueError:
                log(scanner, "Skipping image with bad timestamp in filename")
                continue

            latest_file = os.path.join(folder, images[-1])
            latest_timestamp = int(images[-1].split("-")[-1].replace(".png", ""))

            last_uploaded = last_uploads.get(scanner, 0)

            if latest_timestamp > last_uploaded:
                try:
                    upload_latest_image(scanner, latest_file, latest_timestamp, last_uploads)
                except Exception as ex:
                    # Hard guard: never let an unexpected error stop the loop
                    log(scanner, f"Unexpected error during upload handling: {ex}")
            else:
                log(scanner, "No new images to upload")
        except Exception as ex:
            log(scanner, f"Unhandled error in scanner loop: {ex}")

    manage_old_folder()

if __name__ == "__main__":
    main()
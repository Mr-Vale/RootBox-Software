import os
import shutil
import json
import pickle
import time
from datetime import datetime

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

# -----------------------------
# UTILS
# -----------------------------
def log(scanner, message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    entry = f"{timestamp} [{scanner}] [Image Manager] {message}"
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")
    print(entry)

def load_last_uploads():
    if os.path.exists(LAST_UPLOAD_FILE):
        with open(LAST_UPLOAD_FILE, "r") as f:
            return json.load(f)
    return {}

def save_last_uploads(data):
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
# GOOGLE DRIVE HELPERS
# -----------------------------
def get_creds():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)
    return creds

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
    creds = get_creds()
    service = build('drive', 'v3', credentials=creds)

    # Ensure scanner folder exists in Drive
    folder_id = get_or_create_drive_folder(service, DRIVE_ROOT_FOLDER_ID, scanner)

    # Upload
    file_metadata = {'name': os.path.basename(latest_file), 'parents': [folder_id]}
    media = MediaFileUpload(latest_file, resumable=True)

    service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    log(scanner, f"Uploaded {os.path.basename(latest_file)} to Google Drive")

    # Save last uploaded timestamp
    last_uploads[scanner] = latest_timestamp
    save_last_uploads(last_uploads)

# -----------------------------
# MAIN
# -----------------------------
def main():
    last_uploads = load_last_uploads()

    scanners = get_scanner_folders()
    if not scanners:
        log("System", "No scanner folders found.")
    for scanner in scanners:
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
            upload_latest_image(scanner, latest_file, latest_timestamp, last_uploads)
        else:
            log(scanner, "No new images to upload")

    manage_old_folder()

if __name__ == "__main__":
    main()

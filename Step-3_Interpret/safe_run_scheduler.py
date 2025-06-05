import requests
import os
import sys
import datetime
from dotenv import load_dotenv
import subprocess

# === LOAD ENVIRONMENT ===
load_dotenv()

SCRIPT_DIR = os.getenv("SCRIPT_DIR")
PYTHON_VENV_PATH = os.getenv("PYTHON_VENV_PATH")
MAIN_SCRIPT = os.getenv("MAIN_SCRIPT")
MAIL_SCRIPT = os.getenv("MAIL_SCRIPT")

# Allowed IPs - comma separated in .env
ALLOWED_IPS = set([ip.strip() for ip in os.getenv("ALLOWED_IPS", "").split(",") if ip.strip()])
USE_WIFI_SSID_CHECK = os.getenv("USE_WIFI_SSID_CHECK", "false").lower() == "true"
ALLOWED_SSIDS = set([s.strip() for s in os.getenv("ALLOWED_SSIDS", "").split(",") if s.strip()])

def get_public_ip():
    try:
        return requests.get('https://api.ipify.org').text.strip()
    except Exception as e:
        print(f"{datetime.datetime.now().isoformat()}: IP check failed: {e}")
        return None

def on_trusted_ssid():
    # Only works on Mac for WiFi interface
    try:
        output = subprocess.check_output([
            "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"
        ], universal_newlines=True)
        for line in output.split('\n'):
            if " SSID:" in line:
                return line.split(":")[1].strip() in ALLOWED_SSIDS
    except Exception:
        pass
    return False

def main():
    now = datetime.datetime.now().isoformat()
    my_ip = get_public_ip()
    if my_ip is None:
        print(f"{now}: Could not retrieve public IP; aborting job.")
        sys.exit(88)

    # Optionally use SSID check for home WiFi (Mac only)
    if USE_WIFI_SSID_CHECK:
        if on_trusted_ssid():
            print(f"{now}: On allowed WiFi SSID; running batch job.")
        elif my_ip in ALLOWED_IPS:
            print(f"{now}: On allowed public IP ({my_ip}); running batch job.")
        else:
            print(f"{now}: Not on allowed WiFi or IP ({my_ip}); aborting job.")
            sys.exit(91)
    else:
        if my_ip in ALLOWED_IPS:
            print(f"{now}: On allowed public IP ({my_ip}); running batch job.")
        else:
            print(f"{now}: Not on allowed IP ({my_ip}); aborting job.")
            sys.exit(91)

    # === Run the main script ===
    try:
        result = subprocess.run([PYTHON_VENV_PATH, MAIN_SCRIPT], cwd=SCRIPT_DIR)
        if result.returncode != 0:
            print(f"{now}: Main script exited with error code {result.returncode}")
        else:
            print(f"{now}: Main script completed successfully.")
    except Exception as e:
        print(f"{now}: Failed to run main script: {e}")

    # === Call mail_send.py (email log) after batch job ===
    try:
        ret_mail = subprocess.run([PYTHON_VENV_PATH, MAIL_SCRIPT], cwd=SCRIPT_DIR)
        if ret_mail.returncode != 0:
            print(f"{now}: mail_send.py failed with code {ret_mail.returncode}")
        else:
            print(f"{now}: Log notification email sent successfully.")
    except Exception as e:
        print(f"{now}: Failed to run mail_send.py: {e}")

if __name__ == "__main__":
    main()
import json
from pathlib import Path
from datetime import datetime
import zoneinfo
import os
from sort_os_files import sort_os_file
from sort_device_files import sort_device_file

while True:
    app_name = input("App Name: ")
    if not app_name:
        break
    app_key = app_name.replace(":", "").replace(".", "").replace("⁺", "+")
    build = input("Build: ")
    version = input("Version: ")
    beta = "beta" in version
    internal = bool(input("Is App Internal? [y/n]: ").strip().lower() == "y")
    use_today = bool(input("Use today's date (today in Cupertino time)? [y/n]: ").strip().lower() == "y")
    if use_today:
        release_date = datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
    else:
        release_date = input("Enter release date (YYYY-MM-DD): ").strip()

    if not Path(f"osFiles/Software/{app_key}").exists():
        device_file = Path(f"deviceFiles/Software/{app_key}.json")
        device_details = {
            'name': app_name,
            'type': 'Software'
        }
        if app_key != app_name:
            device_details['key'] = app_key
        if internal:
            device_details['internal'] = True
        if release_date:
            device_details['released'] = release_date
        json.dump(
            sort_device_file(None, device_details),
            device_file.open("w", encoding="utf-8", newline="\n"),
            indent=4,
            ensure_ascii=False,
        )
        os.makedirs(f'osFiles/Software/{app_key}', exist_ok=True)
    app_file = Path(f"osFiles/Software/{app_key}/{version}.json")
    os_str = app_name.split(" (", 1)[0]
    if os_str in ['Apple TV', 'Apple Music Classical', 'iCloud Bookmarks', 'iCloud Passwords', 'Photomator', 'Connect SSO', 'Sneaky Sasquatch']:
        os_str = app_name
    app_details = {
        'osStr': os_str,
        'version': version,
        'deviceMap': [app_key]
    }
    if internal:
        app_details['internal'] = True
    if release_date:
        app_details['released'] = release_date
    if build:
        app_details['build'] = build
    if beta:
        app_details['beta'] = True
    json.dump(
        sort_os_file(None, app_details),
        app_file.open("w", encoding="utf-8", newline="\n"),
        indent=4,
        ensure_ascii=False,
    )
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
    build = input("Build: ")
    version = input("Version: ")
    internal = bool(input("Is App Internal? [y/n]: ").strip().lower() == "y")
    if internal:
        release_date = None
    else:
        use_today = bool(input("Use today's date (today in Cupertino time)? [y/n]: ").strip().lower() == "y")
        if use_today:
            release_date = datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
        else:
            release_date = input("Enter release date (YYYY-MM-DD): ").strip()

    if not Path(f"osFiles/Software/{app_name}").exists():
        device_file = Path(f"deviceFiles/Software/{app_name}.json")
        device_details = {
            'name': app_name,
            'type': 'Software'
        }
        if internal:
            device_details['internal'] = True
        elif release_date:
            device_details['released'] = release_date
        json.dump(
            sort_device_file(None, device_details),
            device_file.open("w", encoding="utf-8", newline="\n"),
            indent=4,
            ensure_ascii=False,
        )
        os.makedirs(f'osFiles/Software/{app_name}', exist_ok=True)
    app_file = Path(f"osFiles/Software/{app_name}/{version}.json")
    app_details = {
        'osStr': app_name,
        'version': version,
        'deviceMap': [app_name]
    }
    if internal:
        app_details['internal'] = True
    elif release_date:
        app_details['released'] = release_date
    if build:
        app_details['build'] = build
    json.dump(
        sort_os_file(None, app_details),
        app_file.open("w", encoding="utf-8", newline="\n"),
        indent=4,
        ensure_ascii=False,
    )
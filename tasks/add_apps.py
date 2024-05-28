import json
from pathlib import Path
from datetime import datetime
import zoneinfo
from sort_os_files import sort_os_file

while True:
    app_name = input("App Name: ")
    if not app_name:
        break
    build = input("Build: ")
    version = input("Version: ")
    use_today = bool(input("Use today's date (today in Cupertino time)? [y/n]: ").strip().lower() == "y")
    if use_today:
        release_date = datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
    else:
        release_date = input("Enter release date (YYYY-MM-DD): ").strip()

    if not Path(f"osFiles/Software/{app_name}").exists():
        print("Invalid app name, ensure app exists in AppleDB before adding new version")
        break
    app_file = Path(f"osFiles/Software/{app_name}/{version}.json")
    app_details = {
        'osStr': app_name,
        'version': version,
        'released': release_date,
        'deviceMap': [app_name]
    }
    if build:
        app_details['build'] = build
    json.dump(
        sort_os_file(None, app_details),
        app_file.open("w", encoding="utf-8", newline="\n"),
        indent=4,
        ensure_ascii=False,
    )
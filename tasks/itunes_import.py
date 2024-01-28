#!/usr/bin/env python3

import json
import plistlib
import random
from pathlib import Path
from zoneinfo import ZoneInfo
import re

import requests

from sort_os_files import sort_os_file
from update_links import update_links

result = requests.get(f"https://swcatalog.apple.com/content/catalogs/others/index-windows-1.sucatalog?cachebust{random.randint(100, 1000)}")

plist = list(plistlib.loads(result.content)['Products'].values())
plist.sort(key=lambda x: x['PostDate'], reverse=True)
target_date = None
version_details = {}
for product in plist:
    if 'iTunes' not in product.get('ServerMetadataURL', ''): continue
    release_date = product['PostDate'].replace(tzinfo=ZoneInfo('UTC')).astimezone(ZoneInfo('America/Los_Angeles')).strftime("%Y-%m-%d")
    if not target_date:
        target_date = release_date
    elif target_date != release_date:
        break
    dist_response = requests.get(product['Distributions']['English']).text

    itunes_version = [x for x in re.findall(r"(<pkg-ref.*<\/pkg-ref>)", dist_response) if 'id="iTunes' in x][0].split('version="')[1].split('"')[0]
    if "WINDOWS64" in product['ServerMetadataURL']:
        device_name = "iTunes (Windows, x64)"
        source_link = requests.head('https://www.apple.com/itunes/download/win64').headers['Location']
    else:
        device_name = "iTunes (Windows, x86)"
        source_link = requests.head('https://www.apple.com/itunes/download/win32').headers['Location']

    if not version_details:
        version_details = {
            "osStr": "iTunes",
            "version": itunes_version,
            "released": release_date,
            "deviceMap": [],
            "osMap": [
                "Windows 10",
                "Windows 11"
            ],
            "sources": []
        }
    version_details["deviceMap"].append(device_name)
    version_details["sources"].append({
        "type": "exe",
        "deviceMap": [
            device_name
        ],
        "osMap": version_details["osMap"],
        "links": [
            {
                "url": source_link
            }
        ]
    })

file_path = Path(f"osFiles/Software/iTunes/{itunes_version.split(".")[0]}.x/{itunes_version}.json")
# osFiles/Software/iTunes/12.x/12.10.11.2.json
json.dump(sort_os_file(None, version_details), file_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
update_links([file_path])

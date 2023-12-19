#!/usr/bin/env python3

from datetime import timezone
import re
import json
import plistlib
import random
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from sort_os_files import sort_os_file
from update_links import update_links

result = requests.get(f"https://swscan.apple.com/content/catalogs/others/index-rosettaupdateauto-1.sucatalog?cachebust{random.randint(100, 1000)}")
result.raise_for_status()

plist = plistlib.loads(result.content)['Products']

for product in plist.values():
    # print(re.match())
    build = product['ExtendedMetaInfo']['BuildVersion']
    kernel_version = re.match(r"(\d+)([A-Z])(\d+)([A-Z])?", build)[1]
    current_path = Path(f'osFiles/Software/Rosetta/{kernel_version}x - {int(kernel_version) - 9}.x/{build}.json')
    if not current_path.exists():
        print(current_path)
        if not current_path.parent.exists():
            Path.mkdir(current_path.parent, parents=True)
        os_path = Path(str(current_path).replace("Software/Rosetta", "macOS"))
        if os_path.exists():
            os_details = json.load(os_path.open())
            desired_version = os_details['version']
            beta = os_details.get('beta')
            rc = os_details.get('rc')
        else:
            distribution_result = requests.get(product['ServerMetadataURL'])

            distribution_plist = plistlib.loads(distribution_result.content)
            distribution_version = distribution_plist["CFBundleShortVersionString"]

            print(f"\tCurrent version is: {distribution_version}")
            desired_version = input("\tEnter version (include beta/RC), or press Enter to keep current: ").strip()
            beta = None
            rc = None
            if desired_version:
                beta = "beta" in desired_version.lower()
                rc = "rc" in desired_version.lower()

        output = {
            "osStr": "Rosetta",
            "version": desired_version or distribution_version,
            "build": build,
            "released": product['PostDate'].replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d"),
            "deviceMap": [
                "Rosetta"
            ],
            "sources": [
                {
                    "type": "pkg",
                    "deviceMap": [
                        "Rosetta"
                    ],
                    "links": [
                        {
                            "url": product["Packages"][0]["URL"],
                            "active": True
                        }
                    ],
                    "size": product["Packages"][0]["Size"]
                }
            ]
        }
        if beta:
            output["beta"] = True
        if rc:
            output["rc"] = True
        json.dump(sort_os_file(None, output), current_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
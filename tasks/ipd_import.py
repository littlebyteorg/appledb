#!/usr/bin/env python3

import re
import sys
import json
import plistlib
from pathlib import Path
import random

import requests

from sort_os_files import sort_os_file

docs = {}
for target_build in sys.argv[1:]:
    docs[target_build] = {}

response = requests.get(f"https://itunes.apple.com/WebObjects/MZStore.woa/wa/com.apple.jingle.appserver.client.MZITunesClientCheck/version?cachebust{random.randint(100, 1000)}", timeout=30)
response.raise_for_status()

plist = plistlib.loads(response.content)

for version_group in plist["MobileDeviceSoftwareVersionsByVersion"].values():
    for device, device_info in version_group["MobileDeviceSoftwareVersions"].items():
        if device in ["iPod1,1", "iPhone1,1", "iPhone1,2", "iPod2,1", "AppleTV2,1", "AppleTV3,1", "AppleTV3,2"]:
            # Special cases not worth dealing with
            continue
        for build, build_info in device_info.items():
            if build == "Unknown":
                if "Universal" in build_info:
                    build_info = build_info["Universal"]
            if build_info.keys() == {"SameAs"}:
                continue
            for variant in [i for i in build_info.values() if isinstance(i, dict)]:
                if not variant.get("DocumentationURL"):
                    continue
                if variant.get('BuildVersion') not in (docs.keys()):
                    continue

                doc_filename = variant['DocumentationURL'].split('/')[-1]

                if doc_filename.startswith('iPad'):
                    docs[variant['BuildVersion']]['iPad'] = variant['DocumentationURL']
                elif doc_filename.startswith('iPod'):
                    docs[variant['BuildVersion']]['iPod'] = variant['DocumentationURL']
                elif doc_filename.startswith('iPhone') or doc_filename.startswith('iOS'):
                    docs[variant['BuildVersion']]['iPhone'] = variant['DocumentationURL']
                elif doc_filename.startswith('AppleTV'):
                    docs[variant['BuildVersion']]['AppleTV'] = variant['DocumentationURL']
                elif doc_filename.startswith('HomePod'):
                    docs[variant['BuildVersion']]['AudioAccessory'] = variant['DocumentationURL']
                else:
                    continue

for build, doc_links in docs.items():
    build_subsets = re.match(r"(\d+)([A-Z])(\d+)([A-Z])?", build)
    include_ipad = int(build_subsets[1]) < 17 and 'iPad' in doc_links.keys()

    for title, link in doc_links.items():
        if title == 'AudioAccessory':
            subfolder = 'audioOS'
        elif title == 'AppleTV':
            subfolder = 'tvOS'
        elif title == 'iPad' and not include_ipad:
            subfolder = 'iPadOS'
        else:
            subfolder = 'iOS'

        file_path = list(Path(f"osFiles/{subfolder}").rglob(f"{build}.json"))[0]
        
        file_contents = json.load(file_path.open())
        file_contents.setdefault('ipd', {})
        if file_contents['ipd'].get(title):
            continue
        file_contents['ipd'][title] = link
        json.dump(sort_os_file(None, file_contents), file_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)

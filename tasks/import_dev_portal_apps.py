#!/usr/bin/env python3

import json
import os
import re
import sys
from pathlib import Path

import dateutil.parser
import lxml.etree
import lxml.html
import requests
import lxml.etree
from lxml.etree import _Element as Element

from sort_os_files import sort_os_file  # pylint: disable=no-name-in-module

LINK_PREFIX = 'https://developer.apple.com/services-account/download?path='

HEADERS = {}

macos_codenames = json.load(Path("tasks/macos_codenames.json").open(encoding="utf-8"))

# If you have a proxy to access the dev portal, pass it on the command line, set the DEV_DATA_PROXY environment variable, or set it here
# Otherwise, leave it blank and save the JSON to import_raw.json
if sys.argv[1:]:
    DEV_DATA_PROXY = sys.argv[1]
elif os.environ.get('DEV_DATA_PROXY'):
    DEV_DATA_PROXY = os.environ['DEV_DATA_PROXY'].strip()
else:
    DEV_DATA_PROXY = ""  # Set your proxy here

if sys.argv[2:]:
    DEV_AUTH_VALUE = sys.argv[2]
elif os.environ.get('DEV_AUTH_VALUE'):
    DEV_AUTH_VALUE = os.environ['DEV_AUTH_VALUE'].strip()
else:
    DEV_AUTH_VALUE = "" # Set your value here for an authorization header

if DEV_AUTH_VALUE:
    HEADERS = {'Authorization': DEV_AUTH_VALUE}

if DEV_DATA_PROXY:
    response = requests.get(DEV_DATA_PROXY, headers=HEADERS).json()

    if response.get('token', {}).get('ADCDownloadAuth'):
            with Path('apple_token.txt').open('w') as token_file:
                token_file.write(response['token']['ADCDownloadAuth'])

    json.dump(response, Path("import_raw.json").open("w", encoding="utf-8", newline="\n"))

json_data = json.load(Path("import_raw.json").open(encoding="utf-8"))

downloads = sorted(json_data['downloads'], key=lambda x: dateutil.parser.parse(x['dateCreated']), reverse=True)

process_downloads = {
    "Safari": True,
    "Command Line Tools": True,
    "Kernel Debug Kit": True,
}

for download in downloads:
    download_name = download.get('displayName', download['name'])

    filtered_download_prefixes = [k for k,v in process_downloads.items() if v]
    if not filtered_download_prefixes: break

    if download_name.startswith("Safari") and process_downloads['Safari']:
        download_name_split = download_name.split(" ")
        safari_subfolder = f"{download_name_split[1].split('.')[0]}.x"
        safari_version = f"{download_name_split[1]} {download_name_split[-2]} {download_name_split[-1]}"

        release_notes_link = LINK_PREFIX + [x for x in download['files'] if x['fileFormat']['extension'] == '.pdf'][0]['remotePath']

        for candidate_file in Path(f"osFiles/Software/Safari/{safari_subfolder}").glob("*.json"):
            candidate_data = json.load(candidate_file.open(encoding="utf-8"))
            if candidate_data["version"] == safari_version:
                candidate_data["releaseNotes"] = release_notes_link
                for os_item in candidate_data["osMap"]:
                    os_version = os_item.split(" ")[-1]
                    download_details = [item for item in download['files'] if macos_codenames[str(os_version)] in item['filename']][0]
                    existing_source = [source for source in candidate_data.get('sources', []) if source['type'] == 'dmg' and source['osMap'] == [os_item]]
                    if existing_source:
                        continue
                    candidate_data['sources'].append({
                        "type": "dmg",
                        "deviceMap": [
                            "Safari (macOS)"
                        ],
                        "osMap": [
                            os_item
                        ],
                        "links": [
                            {
                                "url": LINK_PREFIX + download_details['remotePath'],
                                "active": True
                            }
                        ],
                        "size": download_details['fileSize']
                    })
                    json.dump(sort_os_file(None, candidate_data), candidate_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    elif download_name.startswith("Command Line Tools") and process_downloads["Command Line Tools"]:
        clt_version = download_name.split("Xcode ")[1]
        clt_subfolder = f"{clt_version.split(' ')[0].split('.')[0]}.x"
        target_file = Path(f"osFiles/Software/Xcode Command Line Tools/{clt_subfolder}/{clt_version}.json")
        if target_file.exists():
            process_downloads["Command Line Tools"] = False
            continue
        
        release_date = dateutil.parser.parse(download['dateCreated'])
        json_data = {
            "osStr": "Xcode Command Line Tools",
            "version": clt_version,
            "released": release_date.strftime("%Y-%m-%d"),
            "deviceMap": [
                "Xcode Command Line Tools"
            ],
            "osMap": [
                "macOS 14"
            ],
            "sources": [
                {
                    "type": "dmg",
                    "deviceMap": [
                        "Xcode Command Line Tools"
                    ],
                    "osMap": [
                        "macOS 14"
                    ],
                    "links": [
                        {
                            "url": "https://developer.apple.com/services-account/download?path=/Developer_Tools/Command_Line_Tools_for_Xcode_15.3_beta/Command_Line_Tools_for_Xcode_15.3_beta.dmg",
                            "active": True
                        }
                    ],
                    "size": 724806633
                }
            ]
        }
        if "beta" in clt_version:
            json_data["beta"] = True
        if "RC" in clt_version:
            json_data["rc"] = True

        json.dump(sort_os_file(None, json_data), target_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    elif download_name.startswith("Kernel Debug Kit") and process_downloads["Kernel Debug Kit"]:
        kdk_build = download_name.replace(" 89541", "").split(" ")[-1].split(".")[0]
        target_file = list(Path("osFiles/macOS").rglob(f"{kdk_build}.json"))
        if not target_file:
            print(f"Missing build for KDK build {kdk_build}")
            continue
        kdk_build_data = json.load(target_file[0].open(encoding="utf-8"))
        kdk_file = download['files'][0]
        if bool([source for source in kdk_build_data.get('sources', []) if source['type'] == 'kdk']):
            process_downloads["Kernel Debug Kit"] = False
            continue
        kdk_build_data.setdefault('sources', []).append({
            "type": "kdk",
            "deviceMap": kdk_build_data['deviceMap'],
            "links": [
                {
                    "url": LINK_PREFIX + kdk_file['remotePath'],
                    "active": True
                }
            ],
            "size": kdk_file['fileSize']
        })

        json.dump(sort_os_file(None, kdk_build_data), target_file[0].open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
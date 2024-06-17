#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

import dateutil.parser
import lxml.html
import requests
import lxml.etree

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
# deliberately imported here to grab fresh token
from update_links import update_links

downloads = sorted(json_data['downloads'], key=lambda x: dateutil.parser.parse(x['dateCreated']), reverse=True)

process_downloads = {
    "Safari": True,
    "Command Line Tools": True,
    "Kernel Debug Kit": True,
    "Simulator": True,
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
                    alternate_source = [source for source in candidate_data.get('sources', []) if source['type'] == 'pkg' and source['osMap'] == [os_item]][0]
                    if existing_source:
                        continue
                    candidate_data['sources'].append({
                        "type": "dmg",
                        "deviceMap": alternate_source['deviceMap'],
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
                    update_links([candidate_file])
    elif download_name.startswith("Command Line Tools") and process_downloads["Command Line Tools"]:
        if download_name.split(" ")[-1].startswith("201"):
            clt_version = download_name.split(" - ")[-1]
            clt_subfolder = clt_version.split(" ")[-1]
        elif " - Xcode " in download_name:
            clt_version = download_name.split(" - Xcode ")[-1]
            clt_subfolder = f"{clt_version.split(' ')[0].split('.')[0]}.x"
        else:
            clt_version = download_name.split("Xcode ")[1].replace('Release Candidate', 'RC').replace(' Seed', '').replace(' seed', '').removeprefix('- ')
            clt_subfolder = f"{clt_version.split(' ')[0].split('.')[0]}.x"
        target_file = Path(f"osFiles/Software/Xcode Command Line Tools/{clt_subfolder}/{clt_version}.json")
        if target_file.exists():
            process_downloads["Command Line Tools"] = False
            continue
        download_details = download['files'][0]
        
        release_date = dateutil.parser.parse(download['dateCreated'])
        json_data = {
            "osStr": "Xcode Command Line Tools",
            "version": clt_version,
            "released": release_date.strftime("%Y-%m-%d"),
            "deviceMap": [
                "Xcode Command Line Tools"
            ],
            "osMap": [
                "macOS 14",
                "macOS 15"
            ],
            "sources": [
                {
                    "type": "dmg",
                    "deviceMap": [
                        "Xcode Command Line Tools"
                    ],
                    "osMap": [
                        "macOS 14",
                        "macOS 15"
                    ],
                    "links": [
                        {
                            "url": LINK_PREFIX + download_details['remotePath'],
                            "active": True
                        }
                    ],
                    "size": download_details['fileSize']
                }
            ]
        }
        if "beta" in clt_version:
            json_data["beta"] = True
        if "RC" in clt_version:
            json_data["rc"] = True

        json.dump(sort_os_file(None, json_data), target_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
        update_links([target_file])
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
        update_links([target_file[0]])
    elif download_name.endswith('Simulator Runtime') and process_downloads['Simulator']:
        download_name_split = download_name.split(" ")
        subfolder_pattern = f"*x - {download_name_split[1].split('.')[0]}.x"
        relative_path = f"osFiles/Simulators/{download_name_split[0]}"
        for candidate_file in list(Path(relative_path).glob(subfolder_pattern))[0].glob("*.json"):
            if int(str(candidate_file).split("/")[3].split("x")[0]) < 22: continue
            candidate_data = json.load(candidate_file.open(encoding="utf-8"))
            if candidate_data.get('sources'): continue
            if candidate_data["version"].replace(".0", "").replace("Simulator", "Simulator Runtime") == download_name.replace(f"{candidate_data['osStr']} ", ""):
                candidate_data['sources'] = [
                    {
                        'type': 'dmg',
                        'deviceMap': [f"{download_name_split[0]} Simulator"],
                        'links': [
                            {
                                'url': LINK_PREFIX + download['files'][0]['remotePath'],
                                'active': True
                            }
                        ],
                        'size': download['files'][0]['fileSize']
                    }
                ]
                json.dump(sort_os_file(None, candidate_data), candidate_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
                update_links([candidate_file])
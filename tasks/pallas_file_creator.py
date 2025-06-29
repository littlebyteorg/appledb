import base64
import json
from pathlib import Path
import argparse
import re

import requests
import urllib3

from sort_os_files import sort_os_file
from image_info import get_image

# Disable SSL warnings, because Apple's SSL is broken
urllib3.disable_warnings()

session = requests.Session()

processed_devices = set()
processed_builds = {}
device_map = {}

raw_audiences = json.load(Path("tasks/audiences.json").open(encoding="utf-8"))

latest_builds = json.load(Path("tasks/latest_builds.json").open(encoding="utf-8"))

choice_list = list(latest_builds.keys())

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--os', action='append', choices=choice_list)
parser.add_argument('-u', '--update-type', default='release')
args = parser.parse_args()

choices = args.os or choice_list

def get_build_type(build_number):
    build_type_map = {
        '2': 'Forked',
        '5': 'Beta',
        '6': 'Inflated',
        '8': 'Forked'
    }
    if not (len(build_number) >= 7 and build_number[6].isdigit()):
        return 'Release'
    
    return build_type_map.get(build_number[3], 'Release')

def clear_inflated_build(build_number):
    if get_build_type(build_number) != 'Inflated':
        return build_number
    if build_number.startswith('22A63'):
        return build_number.replace('22A63', '22A33')
    return f"{build_number[:3]}{re.sub(r'^0{1,}', '', build_number[4:])}"

def call_pallas(request, os_str, target_device):
    response = session.post("https://gdmf.apple.com/v2/assets", json=request, headers={"Content-Type": "application/json"}, verify=False)
    parsed_response = json.loads(base64.b64decode(response.text.split('.')[1] + '==', validate=False))
    discovered_builds = set()
    for asset in parsed_response['Assets']:
        cleaned_build = clear_inflated_build(asset['Build'])
        if cleaned_build in discovered_builds: continue
        if len(list(Path(f"osFiles/{os_str}").rglob(f"{cleaned_build}.json"))) > 0:
            print(f"{os_str}-{cleaned_build}")
            continue
        discovered_builds.add(cleaned_build)
        if not processed_builds.get(f"{os_str}-{cleaned_build}"):
            default_version = asset['OSVersion'].removeprefix('9.9.')
            entered_version = input(f"Enter version (include beta/RC), or press Enter to keep {default_version} for {os_str} ({cleaned_build}): ").strip() or default_version
            processed_build = {
                "osStr": os_str,
                "version": entered_version,
                "build": cleaned_build,
                "released": parsed_response['PostingDate'],
                "beta": "beta" in entered_version,
                "rc": "RC" in entered_version,
                "appledbWebImage": get_image(os_str, entered_version),
                "deviceMap": set()
            }
            if not processed_build['beta']:
                del processed_build['beta']
            if not processed_build['rc']:
                del processed_build['rc']
            processed_builds[f"{os_str}-{cleaned_build}"] = processed_build
        processed_builds[f"{os_str}-{cleaned_build}"]['deviceMap'].add(target_device)

def flatten_audiences(audience_dict):
    audience_list = []
    for label, audience_item in audience_dict.items():
        if isinstance(audience_item, dict):
            audience_list.extend(flatten_audiences(audience_item))
        else:
            if (label == 'release') != (args.update_type == 'release'): continue
            if (label == '26') != (args.update_type == 'next'): continue
            audience_list.append(audience_item)
    return audience_list

for os in choices:
    build_map = latest_builds[os]
    audience_key = os
    if audience_key == 'iPadOS':
        audience_key = 'iOS'
    audiences = flatten_audiences(raw_audiences[audience_key])
    pallas_request = {
        "ClientVersion": 2,
        "CertIssuanceDay": "2024-12-05",
        "BuildVersion": "0"
    }
    if os == 'macOS':
        pallas_request["AssetType"] = "com.apple.MobileAsset.MacSoftwareUpdate"
    else:
        pallas_request["AssetType"] = "com.apple.MobileAsset.SoftwareUpdate"

    for build in build_map[args.update_type]:
        file_path = list(Path(f"osFiles/{os}").rglob(f"{build}.json"))[0]
        file_contents = json.load(file_path.open())
        # device = file_contents['deviceMap'][0]
        for device in file_contents['deviceMap']:
            processed_devices.add(device.split("-")[0])
            if os != 'tvOS':
                device_file = json.load(list(Path("deviceFiles").rglob(f"{device}.json"))[0].open(encoding="utf-8"))
                if isinstance(device_file['board'], list):
                    device_map[device] = device_file['board'][0]
                else:
                    device_map[device] = device_file['board']
                pallas_request["HWModelStr"] = device_map[device]
            if os != 'macOS':
                pallas_request["ProductType"] = device
            for audience in audiences:
                pallas_request['AssetAudience'] = audience
                call_pallas(pallas_request, os, device)
            # break

for build_details in processed_builds.values():
    build_details['deviceMap'] = list(build_details['deviceMap'])
    file_path = f"osFiles/{build_details['osStr']}/{build_details['build'][0:2]}x - {build_details['version'].split(".", 1)[0]}.x/{build_details['build']}.json"
    json.dump(sort_os_file(None, build_details), Path(file_path).open("w", encoding="utf-8"), indent=4)

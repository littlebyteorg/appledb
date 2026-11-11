#!/usr/bin/env python3

import base64
import json
import plistlib
import re
from pathlib import Path
from datetime import datetime

import remotezip
import requests

from sort_os_files import sort_os_file, build_number_sort
from update_links import update_links

SESSION = requests.session()

print(datetime.now())

asset_types = {
    'AirPods': {
        'A2618': ['com.apple.MobileAsset.UARP.A2618'],
        'A2968': ['com.apple.MobileAsset.UARP.A2968'],
        'A3048': ['com.apple.MobileAsset.UARP.A3048'],
        'A3053': ['com.apple.MobileAsset.UARP.A3053'],
        'A3056': ['com.apple.MobileAsset.UARP.A3056'],
        'A3064': ['com.apple.MobileAsset.UARP.A3064'],
        'A3122': ['com.apple.MobileAsset.UARP.A3122'],
        'A3454': ['com.apple.MobileAsset.UARP.A3454'],
        'A3440': ['com.apple.MobileAsset.UARP.A3440'],
        'A3532': ['com.apple.MobileAsset.UARP.A3532'],
    },
    'AirTags': {
        'A2937': ['com.apple.MobileAsset.UARP.A2937'],
    },
    'Studio Display': {
        'A2525': ['com.apple.MobileAsset.DarwinAccessoryUpdate.A2525'],
        'A3348': ['com.apple.MobileAsset.DarwinAccessoryUpdate.A3348'],
        'A3350': ['com.apple.MobileAsset.DarwinAccessoryUpdate.A3350'],
    }
}

os_str_map = {
    'AirPods': 'Bluetooth Headset Firmware',
    'AirTags': '<Model> Firmware',
    'Studio Display': 'Studio Display Firmware',
}

os_subfolder_map = {
    'A2937 Firmware': 'Durian Firmware'
}

release_notes_map = {
    # 'AirPods': 'https://support.apple.com/106340',
    'AirTags': 'https://support.apple.com/102183'
}

device_map = {
    'A2525': [
        'AppleDisplay2,1'
    ],
    'A2618': [
        "AirPodsPro1,2-left",
        "AirPodsPro1,2-right"
    ],
    'A2968': [
        "AirPodsPro1,2-usbc-case"
    ],
    'A2937': [
        'afw2,4'
    ],

    'A3048': [
        "AirPodsPro1,2-usbc-left",
        "AirPodsPro1,2-usbc-right"
    ],
    'A3053': [
        'AirPods1,4-left',
        'AirPods1,4-right'
    ],
    'A3056': [
        'AirPods1,5-left',
        'AirPods1,5-right'
    ],
    'A3064': [
        'AirPodsPro1,3-left',
        'AirPodsPro1,3-right'
    ],
    'A3122': [
        'AirPodsPro1,3-case'
    ],
    'A3348': [
        'AppleDisplay18,1'
    ],
    'A3350': [
        'AppleDisplay18,2'
    ],
    'A3454': [
        "AirPodsMax1,2"
    ],
    'A3440': [
        'AirPods3,8-left',
        'AirPods3,8-right'
    ],
    'A3532': [
        'AirPods3,7-left',
        'AirPods3,7-right'
    ]
}

os_audience_map = {
    'AirPods': ['0c88076f-c292-4dad-95e7-304db9d29d34', '02d8e57e-dd1c-4090-aa50-b4ed2aef0062'],
    'AirPods beta': ['174c5baa-4dbf-4bae-9b71-55637b17dad2', '8d1900d3-8b34-4707-893e-a6151c04ee05'],
    'AirTags': ['0c88076f-c292-4dad-95e7-304db9d29d34'],
    'Studio Display': ['02d8e57e-dd1c-4090-aa50-b4ed2aef0062']
}

found_builds = {
    'AirPods': set(),
    'AirTags': set(),
    'Studio Display': set(),
}

def call_pallas(audience, asset_name, model, is_beta):
    files = set()
    request = {
        "ClientVersion": 2,
        "CertIssuanceDay": "2025-12-08",
        "AssetType": asset_name,
        "AssetAudience": audience
    }
    response = SESSION.post("https://gdmf.apple.com/v2/assets", json=request, headers={"Content-Type": "application/json"}, verify=False)
    asset_plist = json.loads(base64.b64decode(response.text.split('.')[1] + '==', validate=False))
    release_date = asset_plist['PostingDate']
    os_str = os_str_map[asset_type].replace("<Model>", model)
    for asset in asset_plist['Assets']:
        version = None
        if os_str == 'A2937 Firmware':
            version = f"{asset['FirmwareVersionMajor']}.{asset['FirmwareVersionMinor']}.{asset['FirmwareVersionBuild']}"
            file_path = f"osFiles/{os_subfolder_map.get(os_str, os_str)}/{asset['FirmwareVersionMajor']}x/{version}.json"
        else:
            kern_version = re.search(r"\d+(?=[a-zA-Z])", asset['Build']).group()
            if os_str == 'Studio Display Firmware':
                file_path = f"osFiles/{os_subfolder_map.get(os_str, os_str)}/{kern_version}x - {asset['OSVersion'].split('.', 1)[0]}.x/{asset['Build']}.json"
            else:
                file_path = f"osFiles/{os_subfolder_map.get(os_str, os_str)}/{kern_version}x/{asset['Build']}.json"

        if not Path(file_path).exists():
            if not Path(file_path).parent.exists():
                Path(file_path).parent.mkdir()
            with remotezip.RemoteZip(f"{asset['__BaseURL']}{asset['__RelativePath']}") as file:
                manifest_paths = [f for f in file.namelist() if f.endswith("BuildManifest.plist")]
                buildtrain = asset.get('TrainName')
                if manifest_paths and os_str != 'A2937 Firmware':
                    build_manifest = plistlib.loads(file.read(manifest_paths[0]))
                    version = build_manifest['ProductVersion']
                base_contents = {
                    "osStr": os_str,
                    "version": version,
                    "build": asset['Build'],
                    "released": release_date,
                    "deviceMap": []
                }
                if os_str == 'A2937 Firmware':
                    del base_contents['build']
                elif buildtrain:
                    base_contents['buildTrain'] = buildtrain

                if is_beta:
                    base_contents['beta'] = True
                    print(f"\tCurrent version is: {version}")
                    version = input("\tEnter version (include beta/RC), or press Enter to keep current: ").strip() or version
                    base_contents['version'] = version
                else:
                    if release_notes_map.get(asset_type):
                        base_contents["releaseNotes"] = release_notes_map[asset_type]
                json.dump(base_contents, Path(file_path).open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)

        file_data = json.load(Path(file_path).open(encoding="utf-8"))
        found_builds[asset_type].add(Path(file_path).stem)
        if device_map[model][0] in file_data['deviceMap']:
            continue
        print(f"New build {asset['Build']} for {model}")
        source = {"deviceMap": device_map[model], "type": "ota", "links": [{"url": f"{asset['__BaseURL']}{asset['__RelativePath']}", "active": True}]}
        if release_date != file_data['released']:
            extended_items = []
            extended_item_processed = False
            extended_item_changed = False
            for item in file_data.get('createDuplicateEntries', []):
                if item.get('released', file_data['released']) == release_date:
                    extended_item_processed = True
                    if device_map[model][0] not in item['deviceMap']:
                        item['deviceMap'].extend(device_map[model])
                        item.setdefault('sources', []).append(source)
                        extended_item_changed = True
                extended_items.append(item)
            
            if not extended_item_processed:
                extended_items.append({
                    'uniqueBuild': f"{file_data['build']}-{model}",
                    'released': release_date,
                    'deviceMap': device_map[model],
                    'sources': [source]
                })
                extended_item_changed = True
            if not extended_item_changed:
                continue
            file_data['createDuplicateEntries'] = extended_items
        else:
            file_data['deviceMap'].extend(device_map[model])
            file_data.setdefault('sources', []).append(source)

        json.dump(sort_os_file(None, file_data), Path(file_path).open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)

        files.add(Path(file_path))
    return files

processed_files = set()
for asset_type, assets in asset_types.items():
    for asset_model, asset_names in assets.items():
        for audience_uuid in os_audience_map[asset_type]:
            for model_asset_name in asset_names:
                processed_files.update(call_pallas(audience_uuid, model_asset_name, asset_model, False))
        for audience_uuid in os_audience_map.get(f"{asset_type} beta", []):
            for model_asset_name in asset_names:
                processed_files.update(call_pallas(audience_uuid, model_asset_name, asset_model, True))

if processed_files:
    update_links(list(processed_files))
print(found_builds)

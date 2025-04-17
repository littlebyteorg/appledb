#!/usr/bin/env python3

import json
import plistlib
import random
import re
from pathlib import Path
from datetime import datetime, timezone
import zoneinfo

import remotezip
import requests

from sort_os_files import sort_os_file
from update_links import update_links

SESSION = requests.session()

print(datetime.now())

beta_asset_subfolders = {
    'AirPods': 'AirPods2022Seed'
}

asset_types = {
    'AirPods': {
        'A2032': 'com_apple_MobileAsset_MobileAccessoryUpdate_A2032_EA',
        'A2084': 'com_apple_MobileAsset_MobileAccessoryUpdate_A2084_EA',
        'A2096': 'com_apple_MobileAsset_MobileAccessoryUpdate_A2096_EA',
        'A2564': 'com_apple_MobileAsset_MobileAccessoryUpdate_A2564_EA',
        'A2618': 'com_apple_MobileAsset_UARP_A2618',
        'A2968': 'com_apple_MobileAsset_UARP_A2968',
        'A3048': 'com_apple_MobileAsset_UARP_A3048',
        'A3053': 'com_apple_MobileAsset_UARP_A3053',
        'A3056': 'com_apple_MobileAsset_UARP_A3056',
        'A3184': [
            'com_apple_MobileAsset_MobileAccessoryUpdate_A3184_EA',
            'com_apple_MobileAsset_MobileAccessoryUpdate_A3184-24E_EA'
        ]
    },
    'AirTags': {
        'A2187': 'com_apple_MobileAsset_MobileAccessoryUpdate_DurianFirmware'
    },
    'Beats': {
        'A2048': 'com_apple_MobileAsset_MobileAccessoryUpdate_A2048_EA',
        'A2577': 'com_apple_MobileAsset_MobileAccessoryUpdate_A2577_EA',
        'A3157': 'com_apple_MobileAsset_UARP_A3157'
    },
    'Keyboards': {
        'A2520': 'com_apple_MobileAsset_MobileAccessoryUpdate_KeyboardFirmware_10',
        'A2450': 'com_apple_MobileAsset_MobileAccessoryUpdate_KeyboardFirmware_8',
        'A2449': 'com_apple_MobileAsset_MobileAccessoryUpdate_KeyboardFirmware_6',
        'A1644': 'com_apple_MobileAsset_MobileAccessoryUpdate_KeyboardFirmware_5',
        'A1843': 'com_apple_MobileAsset_MobileAccessoryUpdate_ExternalKeyboardFirmware'
    }
}

os_str_map = {
    'AirPods': 'Bluetooth Headset Firmware',
    'AirTags': 'Durian Firmware',
    'Beats': 'Bluetooth Headset Firmware',
    'Keyboards': 'Keyboard Firmware'
}

release_notes_map = {
    'AirPods': 'https://support.apple.com/106340',
    'AirTags': 'https://support.apple.com/102183'
}

device_map = {
    'A1644': [
        'Magic Keyboard (1st generation)'
    ],
    'A1843': [
        'Magic Keyboard with Numeric Keypad'
    ],
    'A2032': [
        "AirPods2,1-left",
        "AirPods2,1-right"
    ],
    'A2048': [
        "PowerbeatsPro1,1-left",
        "PowerbeatsPro1,1-right",
        "PowerbeatsPro2,1-left",
        "PowerbeatsPro2,1-right",
        "PowerbeatsPro2,1-left",
        "PowerbeatsPro2,1-right",
        "PowerbeatsPro2,1-faze-left",
        "PowerbeatsPro2,1-faze-right",
        "PowerbeatsPro2,1-fragment-left",
        "PowerbeatsPro2,1-fragment-right",
        "PowerbeatsPro2,1-melody-left",
        "PowerbeatsPro2,1-melody-right",
        "PowerbeatsPro2,1-nba-left",
        "PowerbeatsPro2,1-nba-right",
        "PowerbeatsPro2,1-paria-left",
        "PowerbeatsPro2,1-paria-right",
        "PowerbeatsPro2,1-samuel-left",
        "PowerbeatsPro2,1-samuel-right"
    ],
    'A2084': [
        "AirPods2,2-left",
        "AirPods2,2-right"
    ],
    'A2096': [
        "iProd8,6"
    ],
    'A2187': [
        "AirTag1,1"
    ],
    'A2449': [
        'Magic Keyboard with Touch ID'
    ],
    'A2450': [
        'Magic Keyboard (2nd generation)'
    ],
    'A2520': [
        'Magic Keyboard with Touch ID and Numeric Keypad'
    ],
    'A2564': [
        "Audio2,1-left",
        "Audio2,1-right"
    ],
    'A2577': [
        "BeatsFitPro1,1-left",
        "BeatsFitPro1,1-right",
        "BeatsFitPro1,1-alo-left",
        "BeatsFitPro1,1-alo-right",
        "BeatsFitPro1,1-fragment-left",
        "BeatsFitPro1,1-fragment-right",
        "BeatsFitPro1,1-kim-left"
        "BeatsFitPro1,1-kim-right"
    ],
    'A2618': [
        "AirPods3,1-left",
        "AirPods3,1-right"
    ],
    'A2968': [
        "Device1,8228-case"
    ],
    'A3048': [
        "Device1,8228-left",
        "Device1,8228-right"
    ],
    'A3053': [
        'AirPods3,2-left',
        'AirPods3,2-right'
    ],
    'A3056': [
        'AirPods3,3-left',
        'AirPods3,3-right'
    ],
    'A3157': [
        'Powerb3,1-left',
        'Powerb3,1-right'
    ],
    'A3184': [
        "AirPodsMax1,2"
    ]
}

def call_mesu(asset_url):
    files = set()
    asset_response = SESSION.get(f"{asset_url}?cachebust{random.randint(100, 1000)}")
    try:
        asset_response.raise_for_status()
    except:
        print(f"Skipping {asset_url.removeprefix("https://mesu.apple.com/assets/").removesuffix(".xml")}")
        return files
    asset_plist = plistlib.loads(asset_response.content)
    release_date = datetime.strptime(asset_response.headers.get("Last-Modified").replace(" GMT", ""), '%a, %d %b %Y %H:%M:%S').replace(tzinfo=timezone.utc).astimezone(zoneinfo.ZoneInfo('America/Los_Angeles')).strftime("%Y-%m-%d")
    for asset in asset_plist['Assets']:
        kern_version = re.search(r"\d+(?=[a-zA-Z])", asset['Build']).group()
        file_path = f"osFiles/{os_str_map[asset_type]}/{kern_version}x/{asset['Build']}.json"

        if not Path(file_path).exists():
            if not Path(file_path).parent.exists():
                Path(file_path).parent.mkdir()
            with remotezip.RemoteZip(f"{asset['__BaseURL']}{asset['__RelativePath']}") as file:
                manifest_paths = [f for f in file.namelist() if f.endswith("BuildManifest.plist")]
                buildtrain = None
                version = None
                if manifest_paths:
                    build_manifest = plistlib.loads(file.read(manifest_paths[0]))
                    buildtrain = build_manifest['BuildIdentities'][0]['Info']['BuildTrain']
                    version = build_manifest['ProductVersion']
                if os_str_map[asset_type] == 'Bluetooth Headset Firmware' and not version:
                    if asset['FirmwareVersionMinor'] > 1000:
                        version = '.'.join(str(asset['FirmwareVersionMajor']))
                    else:
                        version = f"{asset['FirmwareVersionMajor']}.{asset['FirmwareVersionMinor']}"
                elif os_str_map[asset_type] == 'Durian Firmware':
                    version = f"{asset['FirmwareVersionMajor']}.{asset['FirmwareVersionMinor']}.{asset['FirmwareVersionRelease']}"
                base_contents = {
                    "osStr": os_str_map[asset_type],
                    "version": version,
                    "build": asset['Build'],
                    "released": release_date,
                    "deviceMap": []
                }
                if buildtrain:
                    base_contents['buildTrain'] = buildtrain

                if beta:
                    base_contents["beta"] = True
                elif release_notes_map.get(asset_type):
                    base_contents["releaseNotes"] = release_notes_map[asset_type]
                json.dump(base_contents, Path(file_path).open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)

        file_data = json.load(Path(file_path).open(encoding="utf-8"))
        if device_map[model][0] in file_data['deviceMap']:
            continue
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
for beta in [True, False]:
    for asset_type, assets in asset_types.items():
        for model, asset_link in assets.items():
            if isinstance(asset_link, list):
                for asset_sublink in asset_link:
                    if beta:
                        if not beta_asset_subfolders.get(asset_type):
                            break
                        asset_url = f'https://mesu.apple.com/assets/{beta_asset_subfolders[asset_type]}/{asset_sublink}/{asset_sublink}.xml'
                    else:
                        asset_url = f'https://mesu.apple.com/assets/{asset_sublink}/{asset_sublink}.xml'
                    processed_files.update(call_mesu(asset_url))
            else:
                if beta:
                    if not beta_asset_subfolders.get(asset_type):
                        break
                    asset_url = f'https://mesu.apple.com/assets/{beta_asset_subfolders[asset_type]}/{asset_link}/{asset_link}.xml'
                else:
                    asset_url = f'https://mesu.apple.com/assets/{asset_link}/{asset_link}.xml'
                processed_files.update(call_mesu(asset_url))
            
update_links(list(processed_files))

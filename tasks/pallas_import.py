#!/usr/bin/env python3

import base64
import json
import plistlib
import re
from pathlib import Path
from datetime import datetime

import remotezip
import requests

from sort_os_files import sort_os_file
from update_links import update_links

SESSION = requests.session()

print(datetime.now())

asset_types = {
    'AirTags': {
        'A2937': ['com.apple.MobileAsset.UARP.A2937']
    }
}

os_str_map = {
    'AirTags': '<Model> Firmware'
}

os_subfolder_map = {
    'A2937 Firmware': 'Durian Firmware'
}

release_notes_map = {
    'AirTags': 'https://support.apple.com/102183'
}

device_map = {
    'A2937': [
        'afw2,4'
    ]
}

os_audience_map = {
    'AirTags': ['0c88076f-c292-4dad-95e7-304db9d29d34'],
    'Studio Display': ['02d8e57e-dd1c-4090-aa50-b4ed2aef0062']
}

def call_pallas(audience, asset_name, model):
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

                if release_notes_map.get(asset_type):
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
for asset_type, assets in asset_types.items():
    for model, asset_names in assets.items():
        for audience in os_audience_map[asset_type]:
            for asset_name in asset_names:
                processed_files.update(call_pallas(audience, asset_name, model))

if processed_files:
    update_links(list(processed_files))

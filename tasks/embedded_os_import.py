#!/usr/bin/env python3
import json
from pathlib import Path

import remotezip
import requests

from file_downloader import handle_pkg_file
from sort_os_files import sort_os_file

SESSION = requests.session()

output_pkg_path = 'out/EmbeddedOSFirmware'
manifest_path = 'usr/standalone/firmware/iBridge1_1Customer.bundle/Contents/Resources/BuildManifest.plist'

for source in list(Path('osFiles/macOS/22x - 13.x').rglob('22H*.json')):
    source_json = json.load(source.open())

    if source_json.get('embeddedOSBuild') or source_json.get('preinstalled') or 'MacBookPro14,1' not in source_json.get('deviceMap', []):
        continue

    relevant_otas = [x for x in source_json.get("sources", []) if x['type'] == 'ota' and not x.get('prerequisiteBuild') and 'MacBookPro14,1' in x.get('deviceMap', [])]

    if not relevant_otas:
        continue

    relevant_ota = relevant_otas[0]

    counter = 0
    while not Path('out/package.pkg').exists():
        try:
            with remotezip.RemoteZip(relevant_ota['links'][0]['url'], initial_buffer_size=256*1024, session=SESSION, timeout=120) as ota:
                with open(f'out/package.pkg', 'wb') as eos_file:
                    eos_file.write(ota.read('AssetData/boot/EmbeddedOSFirmware.pkg'))
        except:
            if counter >= 10:
                raise
            counter += 1

    (_, manifest) = handle_pkg_file(hashes=[], extracted_manifest_file_path=manifest_path)

    source_json['embeddedOSBuild'] = manifest['ProductBuildVersion']

    build_path = Path(f"osFiles/embeddedOS/{manifest['ProductBuildVersion']}.json")
    if not build_path.exists():
        new_file_contents = {
            "osStr": "embeddedOS",
            "version": manifest["ProductVersion"],
            "build": manifest['ProductBuildVersion'],
            "buildTrain": manifest['BuildIdentities'][0]['Info']['BuildTrain'],
            "deviceMap": [
                "iBridge1,1"
            ]
        }
        json.dump(sort_os_file(None, new_file_contents), build_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    json.dump(sort_os_file(None, source_json), source.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
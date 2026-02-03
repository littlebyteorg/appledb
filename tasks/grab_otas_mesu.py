#!/usr/bin/env python3

import argparse
import json
import plistlib
from pathlib import Path
import random
import re

import requests
from sort_os_files import build_number_sort, device_sort

class SetEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, set):
            return list(o)
        return json.JSONEncoder.default(self, o)

urls = {
    'audioOS': 'https://mesu.apple.com/assets/audio/com_apple_MobileAsset_SoftwareUpdate/com_apple_MobileAsset_SoftwareUpdate.xml',
    'iOS': 'https://mesu.apple.com/assets/com_apple_MobileAsset_SoftwareUpdate/com_apple_MobileAsset_SoftwareUpdate.xml',
    'tvOS': 'https://mesu.apple.com/assets/tv/com_apple_MobileAsset_SoftwareUpdate/com_apple_MobileAsset_SoftwareUpdate.xml',
    'watchOS': 'https://mesu.apple.com/assets/watch/com_apple_MobileAsset_SoftwareUpdate/com_apple_MobileAsset_SoftwareUpdate.xml',
}
# urls = [
#     "https://mesu.apple.com/assets/com_apple_MobileAsset_SoftwareUpdate/com_apple_MobileAsset_SoftwareUpdate.xml",
#     "https://mesu.apple.com/assets/watch/com_apple_MobileAsset_SoftwareUpdate/com_apple_MobileAsset_SoftwareUpdate.xml"
# ]

skip_builds = [
    "9B206",
    "10A444",
    "10B329",
    "10B500",
    "11D257",
    "11D258",
    "12H321",
    "12H1006",
    "13G36",
    "13G37",
    "14G60",
    "14G61",
    "15U70",
    "16H88",
    "16U693",
    "17M61",
    "17U224",
    "19H402",
    "20H370",
    "21H450",
    "22H218",
    "23C71",
    "99Z999"
]

ota_links=set()
ota_list = {}

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--suffix', default="")
args = parser.parse_args()

file_name_base = f"import-ota-{args.suffix}" if args.suffix else "import-ota"

for (os_str, url) in urls.items():
    response = requests.get(url + f"?cachebust{random.randint(100, 1000)}", timeout=30)
    response.raise_for_status()

    assets = plistlib.loads(response.content)['Assets']

    for asset in assets:
        cleaned_os_version = asset['OSVersion'].removeprefix('9.9.')
        if os_str == 'iOS' and 'iPad' in asset['SupportedDevices'][0] and int(cleaned_os_version.split('.')[0]) >= 13:
            os_str_name = 'iPadOS'
        else:
            os_str_name = os_str
        updated_build = asset['Build']
        # ensure deltas from beta builds to release builds are properly filtered out as noise as well if the target build is known
        delta_from_beta = re.search(r"(6\d{3})", updated_build)
        if delta_from_beta:
            updated_build = updated_build.replace(delta_from_beta.group(), str(int(delta_from_beta.group()) - 6000))
        if updated_build in skip_builds: continue
        restore_version = asset.get('RestoreVersion')
        if restore_version:
            restore_version = restore_version.replace('.6.0,0', '.0.0,0')
        if not ota_list.get(f"{os_str_name}-{updated_build}"):
            base_details = {
                'osStr': os_str_name,
                'version': cleaned_os_version,
                'build': updated_build,
                'buildTrain': asset.get('TrainName'),
                'restoreVersion': restore_version,
                'sources': {}
            }
            ota_list[f"{os_str_name}-{updated_build}"] = base_details
        link = f"{asset['__BaseURL']}{asset['__RelativePath']}"
        if 'OTARescueAsset' in link: continue
        if not ota_list[f"{os_str_name}-{updated_build}"]['sources'].get(link):
            ota_list[f"{os_str_name}-{updated_build}"]['sources'][link] = {
                "prerequisites": set(),
                "deviceMap": set(),
                "boardMap": set(),
                "links": [{
                    "url": link,
                    "key": asset.get('ArchiveDecryptionKey')
                }]
            }
        ota_list[f"{os_str_name}-{updated_build}"]['sources'][link]["deviceMap"].update(asset['SupportedDevices'])
        # iPhone11,4 is weird; nothing comes back from Pallas, but it's in the BuildManifest for the actual zip in this scenario
        if ota_list[f"{os_str_name}-{updated_build}"]['sources'][link]["deviceMap"].intersection({"iPhone11,2", "iPhone11,6"}) == {"iPhone11,2", "iPhone11,6"}:
            ota_list[f"{os_str_name}-{updated_build}"]['sources'][link]["deviceMap"].add("iPhone11,4")
        ota_list[f"{os_str_name}-{updated_build}"]['sources'][link]["boardMap"].update(asset.get('SupportedDeviceModels', []))
        if asset.get('PrerequisiteBuild') and asset.get('AllowableOTA', True):
            ota_list[f"{os_str_name}-{updated_build}"]['sources'][link]['prerequisites'].add(asset['PrerequisiteBuild'])

        if asset.get('TrainName') and not ota_list[f"{os_str_name}-{updated_build}"].get('buildTrain'):
            ota_list[f"{os_str_name}-{updated_build}"]['buildTrain'] = asset['TrainName']
        if asset.get('ArchiveDecryptionKey'):
            link = f"{link};{asset['ArchiveDecryptionKey']}"
        ota_links.add(link)

builds = set()
for key in ota_list.keys():
    sources = []
    builds.add(ota_list[key]['build'])
    for source in ota_list[key]['sources'].values():
        source['deviceMap'] = sorted(list(source['deviceMap']), key=device_sort)
        source['prerequisites'] = sorted(list(source['prerequisites']), key=build_number_sort)
        if len(source['prerequisites']):
            if source['prerequisites'][0][:3] != source['prerequisites'][-1][:3]:
                source['prerequisites'] = []
        source['boardMap'] = sorted(list(source['boardMap']))
        sources.append(source)
    ota_list[key]['sources'] = sources

print(sorted(builds, key=build_number_sort))
if bool(ota_list.keys()):
    print(f"{len([x for x in ota_list.values() for y in x['sources'] for z in y['links']])} links added")
    _ = [i.unlink() for i in Path.cwd().glob(f"{file_name_base}.*") if i.is_file()]
    json.dump(list(ota_list.values()), Path(f"{file_name_base}.json").open("w", encoding="utf-8"), indent=4, cls=SetEncoder)
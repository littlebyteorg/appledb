import argparse
import json
from pathlib import Path
from sort_files_common import build_number_sort, device_sort

subfolders = [
    'audioOS',
    'bridgeOS',
    'iOS',
    'iPadOS',
    'macOS',
    'tvOS',
    'Studio Display Firmware',
    'visionOS',
    'watchOS',
]

blocked_prefixes = {
    'macOS': [
        'iMac14',
        'iMac15',
        'iMac16',
        'iMac17',
        'iMac18',
        'iMac19',
        'iMac20',
        'iMacPro1',
        'MacBook8',
        'MacBook9',
        'MacBook10',
        'MacBookAir6',
        'MacBookAir7',
        'MacBookAir8',
        'MacBookAir9',
        'MacBookPro11',
        'MacBookPro12',
        'MacBookPro13',
        'MacBookPro14',
        'MacBookPro15',
        'MacBookPro16',
        'Macmini7',
        'Macmini8',
        'MacPro6',
        'MacPro7',
    ]
}

parser = argparse.ArgumentParser()
parser.add_argument('-b', '--betas', action='store_true')
parser.add_argument('-d', '--devices', action='store_true')
parser.add_argument('-o', '--os', action='append', choices=subfolders)
args = parser.parse_args()

signed_builds = {}

for subfolder in args.os or subfolders:
    working_dict = {}
    for file_path in Path(f"osFiles/{subfolder}").rglob("*.json"):
        file_contents = json.load(file_path.open(encoding='utf-8'))
        if not file_contents.get('signed'): continue
        if not args.betas and (file_contents.get('beta') or file_contents.get('rc') or file_contents.get('internal')): continue
        if isinstance(file_contents['signed'], list):
            working_dict[file_contents['build']] = file_contents['signed']
        else:
            working_dict[file_contents['build']] = [x for x in file_contents['deviceMap'] if x.split(",")[0] not in blocked_prefixes.get(subfolder, [])]
    if args.devices:
        signed_builds[subfolder] = {k: sorted(working_dict[k], key=device_sort) for k in sorted(working_dict.keys(), key=build_number_sort)}
    else:
        signed_builds[subfolder] = sorted(working_dict.keys(), key=build_number_sort)
    
print(json.dumps(signed_builds, indent=4))
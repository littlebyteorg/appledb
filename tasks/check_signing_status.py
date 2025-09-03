import argparse
import json
from pathlib import Path
import shutil
import string
import subprocess
import requests
import remotezip

from file_downloader import handle_ota_file, handle_pkg_file
from sort_os_files import sort_os_file

session = requests.Session()

parser = argparse.ArgumentParser()
parser.add_argument('-b', '--build', action='append', nargs='+')
parser.add_argument('-o', '--os', action='append')
args = parser.parse_args()

parsed_args = dict(zip(args.os, args.build))

baseband_value = {
    "iPad2,2": "112312323123123123121212",
    "iPad2,3": "11231232",
    "iPad2,6": "11231232",
    "iPad2,7": "11231232",
    "iPad3,2": "11231232",
    "iPad3,3": "11231232",
    "iPad3,5": "11231232",
    "iPad3,6": "11231232",
    "iPad4,2": "11231232",
    "iPad4,3": "11231232",
    "iPad4,5": "11231232",
    "iPad4,6": "11231232",
    "iPad4,8": "11231232",
    "iPad4,9": "11231232",
    "iPad5,2": "11231232",
    "iPad5,4": "11231232",
    "iPad6,4": "11231232",
    "iPad6,8": "11231232",
    "iPad6,12": "11231232",
    "iPad7,2": "11231232",
    "iPad7,4": "11231232",
    "iPad7,6": "11231232",
    "iPad7,12": "112312323123123123121212",
    "iPad8,3": "112312323123123123121212",
    "iPad8,4": "112312323123123123121212",
    "iPad8,7": "112312323123123123121212",
    "iPad8,8": "112312323123123123121212",
    "iPad8,10": "112312323123123123121212",
    "iPad8,12": "112312323123123123121212",
    "iPad11,2": "112312323123123123121212",
    "iPad11,4": "112312323123123123121212",
    "iPad11,7": "112312323123123123121212",
    "iPad12,2": "112312323123123123121212",
    "iPad13,2": "112312323123123123121212",
    "iPad13,6": "11231232",
    "iPad13,7": "11231232",
    "iPad13,10": "11231232",
    "iPad13,11": "11231232",
    "iPad13,17": "11231232",
    "iPad13,19": "11231232",
    "iPad14,2": "11231232",
    "iPad14,4": "11231232",
    "iPad14,6": "11231232",
    "iPad14,9": "11231232",
    "iPad14,11": "11231232",
    "iPad15,4": "11231232",
    "iPad15,6": "11231232",
    "iPad15,8": "11231232",
    "iPad16,2": "11231232",
    "iPad16,4": "11231232",
    "iPad16,6": "11231232",
    "iPhone2,1": "112312323123123123121212",
    "iPhone3,1": "112312323123123123121212",
    "iPhone3,2": "112312323123123123121212",
    "iPhone3,3": "11231232",
    "iPhone4,1": "11231232",
    "iPhone5,1": "11231232",
    "iPhone5,2": "11231232",
    "iPhone5,3": "11231232",
    "iPhone5,4": "11231232",
    "iPhone6,1": "11231232",
    "iPhone6,2": "11231232",
    "iPhone7,1": "11231232",
    "iPhone7,2": "11231232",
    "iPhone8,1": "11231232",
    "iPhone8,2": "11231232",
    "iPhone8,4": "11231232",
    "iPhone9,1": "11231232",
    "iPhone9,2": "11231232",
    "iPhone9,3": "112312323123123123121212",
    "iPhone9,4": "112312323123123123121212",
    "iPhone10,1": "11231232",
    "iPhone10,2": "11231232",
    "iPhone10,3": "11231232",
    "iPhone10,4": "112312323123123123121212",
    "iPhone10,5": "112312323123123123121212",
    "iPhone10,6": "112312323123123123121212",
    "iPhone11,2": "112312323123123123121212",
    "iPhone11,4": "112312323123123123121212",
    "iPhone11,6": "112312323123123123121212",
    "iPhone11,8": "112312323123123123121212",
    "iPhone12,1": "112312323123123123121212",
    "iPhone12,3": "112312323123123123121212",
    "iPhone12,5": "112312323123123123121212",
    "iPhone12,8": "112312323123123123121212",
    "iPhone13,1": "11231232",
    "iPhone13,2": "11231232",
    "iPhone13,3": "11231232",
    "iPhone13,4": "11231232",
    "iPhone14,2": "11231232",
    "iPhone14,3": "11231232",
    "iPhone14,4": "11231232",
    "iPhone14,5": "11231232",
    "iPhone14,6": "11231232",
    "iPhone14,7": "11231232",
    "iPhone14,8": "11231232",
    "iPhone15,2": "11231232",
    "iPhone15,3": "11231232",
    "iPhone15,4": "11231232",
    "iPhone15,5": "11231232",
    "iPhone16,1": "11231232",
    "iPhone16,2": "11231232",
    "iPhone17,1": "11231232",
    "iPhone17,2": "11231232",
    "iPhone17,3": "11231232",
    "iPhone17,4": "11231232",
    "Watch3,1": "11231232",
    "Watch3,2": "11231232",
    "Watch4,3": "112312323123123123121212",
    "Watch4,4": "112312323123123123121212",
    "Watch5,3": "112312323123123123121212",
    "Watch5,4": "112312323123123123121212",
    "Watch5,11": "112312323123123123121212",
    "Watch5,12": "112312323123123123121212",
    "Watch6,3": "112312323123123123121212",
    "Watch6,4": "112312323123123123121212",
    "Watch6,8": "112312323123123123121212",
    "Watch6,9": "112312323123123123121212",
    "Watch6,12": "112312323123123123121212",
    "Watch6,13": "112312323123123123121212",
    "Watch6,16": "112312323123123123121212",
    "Watch6,17": "112312323123123123121212",
    "Watch6,18": "112312323123123123121212",
    "Watch7,3": "112312323123123123121212",
    "Watch7,4": "112312323123123123121212",
    "Watch7,5": "112312323123123123121212",
    "Watch7,10": "112312323123123123121212",
    "Watch7,11": "112312323123123123121212",
}

board_ids = {
    'iPad6,11': ["J71sAP", "J71tAP"],
    'iPad6,12': ["J72sAP", "J72tAP"],
    'iPhone8,1': ["N71AP", "N71mAP"],
    'iPhone8,2': ["N66AP", "N66mAP"],
    'iPhone8,4': ["N69uAP", "N69AP"],
}

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

def handle_signing(json_contents):
    checked_build_device_list = set()
    checked_board_device_list = set()
    for source in json_contents['sources']:
        if not set([x for x in source['deviceMap'] if "-" not in x and x.split(",")[0] not in blocked_prefixes.get(os, [])]).difference(checked_build_device_list): continue
        if not ((source['type'] == 'pkg' and os == 'bridgeOS') or source['type'] in ['ipsw', 'ota']): continue
        previously_checked = []
        for device in source['deviceMap']:
            if json_contents.get('signingStatus', {}).get(device) is not None:
                if isinstance(board_ids.get(device), list):
                    if not isinstance(json_contents['signingStatus'][device], dict):
                        continue
                    if len(board_ids[device]) != len(json_contents['signingStatus'][device].keys()):
                        continue
                previously_checked.append(device)
        if len(previously_checked) == len(source['deviceMap']):
            continue
        # if source['type'] == 'ipsw': continue
        link = [x for x in source['links'] if x['active'] and 'apple.com' in x['url'] and 'developer' not in x['url']]
        if not link: continue
        link = link[0]
        url_prefix = link['url'].rsplit('/', 1)[1].split('_', 1)[0]
        if url_prefix in ['iPhone1,1', 'iPod1,1']: continue
        parent_path = None
        if source['type'] == 'pkg':
            parent_path = 'out/package-bridge'
            handle_pkg_file(link['url'], file_suffix='-bridge', remove_file=False)
            subprocess.run(['pkgutil', '--expand-full', f'{parent_path}.pkg', parent_path], check=True)
            Path(f'{parent_path}.pkg').unlink()
            file_path = f'{parent_path}/Payload/usr/standalone/firmware/bridgeOSCustomer.bundle/Contents/Resources/BuildManifest.plist'
        else:
            manifest_response = session.get(link['url'].rsplit("/", 1)[0] + "/BuildManifest.plist")
            file_path = "out/BuildManifest.plist"
            if manifest_response.status_code == 200:
                Path(file_path).write_bytes(manifest_response.content)
            else:
                if link.get('decryptionKey'):
                    handle_ota_file(link['url'], link['decryptionKey'], 'aastuff_standalone', True)
                    parent_path = f"otas/{link['url'].rsplit('/', 1)[1].split('.', 1)[0]}"
                    file_path = f"{parent_path}/AssetData/boot/BuildManifest.plist"
                else:
                    path_prefix = 'AssetData/boot/' if link['url'].endswith('.zip') else ''
                    file = remotezip.RemoteZip(link['url'].replace("https://secure-appldnld", "http://appldnld"), session=session)
                    if url_prefix in ['iPhone1,2', 'iPod2,1'] and int(build[0]) == 7:
                        source_file_name = 'BuildManifesto.plist'
                    else:
                        source_file_name = 'BuildManifest.plist'
                    Path(file_path).write_bytes(file.read(f"{path_prefix}{source_file_name}"))
        for model in source['deviceMap']:
            model = model.split("-", 1)[0]
            if model.split(",")[0] in blocked_prefixes.get(os, []): continue
            if model in checked_build_device_list:
                if isinstance(board_ids.get(model), list):
                    if set(board_ids[model]).issubset(checked_board_device_list):
                        continue
                else:
                    continue

            if json_contents.get('signingStatus', {}).get(model) and not model.startswith('iPhone8'): continue
            params = ["./tsschecker", "-m", file_path, "-d", model]
            if json_contents.get('basebandVersions', {}).get(model) and model not in ['iPhone1,1', 'iPhone1,2', 'iPhone2,1', 'iPad1,1', 'iPhone17,5']:
                params.append("-c")
                params.append(baseband_value[model])
            else:
                params.append("-b")
            if isinstance(board_ids.get(model), list):
                params.append("--boardconfig")
                if not isinstance(json_contents.get('signingStatus', {}).get(model, {}), dict):
                    del json_contents['signingStatus'][model]
                for board in source.get('boardMap', board_ids[model]):
                    if params[-1] != '--boardconfig':
                        params.pop()
                    params.append(board)
                    signing_check = subprocess.run(params, check=False, capture_output=True)
                    signed = signing_check.returncode == 0
                    print(f"{model}-{board} ({build}): {signed}")
                    if not json_contents.get('signingStatus', {}).get(model, {}).get(board):
                        json_contents.setdefault('signingStatus', {}).setdefault(model, {})[board] = signed
                    checked_board_device_list.add(board)
            else:
                if board_ids.get(model):
                    params.append("--boardconfig")
                    params.append(board_ids[model])
                signing_check = subprocess.run(params, check=False, capture_output=True)
                signed = signing_check.returncode == 0
                print(f"{model} ({build}): {signed}")
                if not json_contents.get('signingStatus', {}).get(model):
                    json_contents.setdefault('signingStatus', {})[model] = signed
            checked_build_device_list.add(model)
        Path(file_path).unlink()
        if parent_path:
            shutil.rmtree(parent_path)
    return json_contents

for os, builds in parsed_args.items():
    print(os)
    for build in builds:
        if int(build[0]) < 7 and build[1] in string.ascii_uppercase:
            continue
        print(build)
        for file_name in Path(f'osFiles/{os}').rglob(f"{build}.json"):
            json_contents = json.load(file_name.open(encoding="utf-8"))
            if not json_contents.get('sources'): continue
            json_contents = handle_signing(json_contents)
            for i, dup in enumerate(json_contents.get('createDuplicateEntries', [])):
                if not dup.get('sources') or not dup.get('deviceMap'): continue
                json_contents['createDuplicateEntries'][i] = handle_signing(dup)
            json.dump(sort_os_file(None, json_contents), file_name.open('w', encoding='utf-8'), indent=4)

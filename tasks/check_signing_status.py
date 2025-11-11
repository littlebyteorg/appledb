import argparse
import json
from pathlib import Path
import shutil
import string
import subprocess
import random
import requests
import remotezip
import packaging.version

from file_downloader import handle_ota_file, handle_pkg_file
from sort_os_files import sort_os_file
from sort_files_common import build_number_sort, device_sort

session = requests.Session()

supported_os_names = [
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

parser = argparse.ArgumentParser()
parser.add_argument('-a', '--all-signed', action='store_true')
parser.add_argument('-b', '--build', action='append', nargs='+')
parser.add_argument('-f', '--force-final-releases', action='store_true')
parser.add_argument('-l', '--list-signed', action='store_true')
parser.add_argument('-ld', '--list-devices', action='store_true')
parser.add_argument('-o', '--os', action='append', choices=supported_os_names)
parser.add_argument('-s', '--signed-only', action='store_true')
parser.add_argument('-u', '--unsigned', action='store_true')
args = parser.parse_args()

final_builds = {
    'audioOS': [
        '17M61',
    ],
    'iOS': [
        '8B117',
        '8C148',
        '9B206',
        '10B500',
        '11D257',
        '13G36',
        '13G37',
        '14G60',
        '14G61',
        '16H81',
        '19H394',
        '20H364',
    ],
    'iPadOS': [
        '19H394',
        '20H364',
    ],
    'macOS': [
        '20B28'
    ],
    'tvOS': [
        '10B809',
        '11D257',
        '11D258',
        '12H606',
        '12H1006',
        '14W756',
        '17M61',
    ],
    'Studio Display Firmware': [
        '19F80',
        '20E246',
        '21A329'
    ],
    'visionOS': [],
    'watchOS': [
        '14V753',
        '15U70',
        '16U693',
        '17U208',
        '17U216',
        '19U512',
        '20U502',
        '21U580',
        '22U84',
        '22U90',
    ],
}

current_builds = json.load(Path('tasks/latest_builds.json').open(encoding="utf-8"))
for final_build_os_name in final_builds.keys():
    final_builds[final_build_os_name] = list(set(final_builds[final_build_os_name]).union(current_builds.get(final_build_os_name, {}).get('release', [])))

baseband_value = {
    "iPad2,2": 12,
    "iPad2,3": 4,
    "iPad2,6": 4,
    "iPad2,7": 4,
    "iPad3,2": 4,
    "iPad3,3": 4,
    "iPad3,5": 4,
    "iPad3,6": 4,
    "iPad4,2": 4,
    "iPad4,3": 4,
    "iPad4,5": 4,
    "iPad4,6": 4,
    "iPad4,8": 4,
    "iPad4,9": 4,
    "iPad5,2": 4,
    "iPad5,4": 4,
    "iPad6,4": 4,
    "iPad6,8": 4,
    "iPad6,12": 4,
    "iPad7,2": 4,
    "iPad7,4": 4,
    "iPad7,6": 4,
    "iPad7,12": 12,
    "iPad8,3": 12,
    "iPad8,4": 12,
    "iPad8,7": 12,
    "iPad8,8": 12,
    "iPad8,10": 12,
    "iPad8,12": 12,
    "iPad11,2": 12,
    "iPad11,4": 12,
    "iPad11,7": 12,
    "iPad12,2": 12,
    "iPad13,2": 12,
    "iPad13,6": 4,
    "iPad13,7": 4,
    "iPad13,10": 4,
    "iPad13,11": 4,
    "iPad13,17": 4,
    "iPad13,19": 4,
    "iPad14,2": 4,
    "iPad14,4": 4,
    "iPad14,6": 4,
    "iPad14,9": 4,
    "iPad14,11": 4,
    "iPad15,4": 4,
    "iPad15,6": 4,
    "iPad15,8": 4,
    "iPad16,2": 4,
    "iPad16,4": 4,
    "iPad16,6": 4,
    "iPhone3,1": 12,
    "iPhone3,2": 12,
    "iPhone3,3": 4,
    "iPhone4,1": 4,
    "iPhone5,1": 4,
    "iPhone5,2": 4,
    "iPhone5,3": 4,
    "iPhone5,4": 4,
    "iPhone6,1": 4,
    "iPhone6,2": 4,
    "iPhone7,1": 4,
    "iPhone7,2": 4,
    "iPhone8,1": 4,
    "iPhone8,2": 4,
    "iPhone8,4": 4,
    "iPhone9,1": 4,
    "iPhone9,2": 4,
    "iPhone9,3": 12,
    "iPhone9,4": 12,
    "iPhone10,1": 4,
    "iPhone10,2": 4,
    "iPhone10,3": 4,
    "iPhone10,4": 12,
    "iPhone10,5": 12,
    "iPhone10,6": 12,
    "iPhone11,2": 12,
    "iPhone11,4": 12,
    "iPhone11,6": 12,
    "iPhone11,8": 12,
    "iPhone12,1": 12,
    "iPhone12,3": 12,
    "iPhone12,5": 12,
    "iPhone12,8": 12,
    "iPhone13,1": 4,
    "iPhone13,2": 4,
    "iPhone13,3": 4,
    "iPhone13,4": 4,
    "iPhone14,2": 4,
    "iPhone14,3": 4,
    "iPhone14,4": 4,
    "iPhone14,5": 4,
    "iPhone14,6": 4,
    "iPhone14,7": 4,
    "iPhone14,8": 4,
    "iPhone15,2": 4,
    "iPhone15,3": 4,
    "iPhone15,4": 4,
    "iPhone15,5": 4,
    "iPhone16,1": 4,
    "iPhone16,2": 4,
    "iPhone17,1": 4,
    "iPhone17,2": 4,
    "iPhone17,3": 4,
    "iPhone17,4": 4,
    "iPhone18,1": 8,
    "iPhone18,2": 8,
    "iPhone18,3": 8,
    "Watch3,1": 4,
    "Watch3,2": 4,
    "Watch4,3": 12,
    "Watch4,4": 12,
    "Watch5,3": 12,
    "Watch5,4": 12,
    "Watch5,11": 12,
    "Watch5,12": 12,
    "Watch6,3": 12,
    "Watch6,4": 12,
    "Watch6,8": 12,
    "Watch6,9": 12,
    "Watch6,12": 12,
    "Watch6,13": 12,
    "Watch6,16": 12,
    "Watch6,17": 12,
    "Watch6,18": 12,
    "Watch7,3": 12,
    "Watch7,4": 12,
    "Watch7,5": 12,
    "Watch7,10": 12,
    "Watch7,11": 12,
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

def get_builds(os_names, include_devices):
    signed_builds = {}
    for os_name in os_names:
        working_dict = {}
        for file_path in Path(f"osFiles/{os_name}").rglob("*.json"):
            file_contents = json.load(file_path.open(encoding='utf-8'))
            if os_name == 'audioOS' and file_contents['build'] == '15C25': continue
            if file_contents.get('osStr') and not file_contents.get('build'): continue
            if os_name == 'macOS' and packaging.version.parse(file_contents.get('version', '0').split(" ", 1)[0]) < packaging.version.parse("10.16"): continue
            if os_name == 'tvOS' and packaging.version.parse(file_contents.get('version', '0').split(" ", 1)[0]) < packaging.version.parse("4"): continue
            if not file_contents.get('deviceMap'): continue
            if not args.force_final_releases and not args.list_signed:
                if os_name == 'macOS' and not (file_contents.get('beta') or file_contents.get('rc')): continue
                if file_contents['build'] in final_builds.get(os_name, []): continue
            if not file_contents.get('signed', args.unsigned): continue
            if not args.unsigned and isinstance(file_contents['signed'], list):
                working_dict[file_contents['build']] = file_contents['signed']
            else:
                working_dict[file_contents['build']] = [x for x in file_contents['deviceMap'] if x.split(",")[0] not in blocked_prefixes.get(os_name, [])]
        if include_devices:
            signed_builds[os_name] = {k: sorted(working_dict[k], key=device_sort) for k in sorted(working_dict.keys(), key=build_number_sort)}
        else:
            signed_builds[os_name] = sorted(working_dict.keys(), key=build_number_sort)
    return signed_builds

def generate_random_serial(raw_length):
    altered_length = raw_length * 2
    # pad zeroes to the end in case getrandbits returns a bunch of leading 0s that get dropped
    random_serial = f"{str(random.getrandbits(4 * altered_length))}{''.join(['0' for _ in range(altered_length)])}"[:altered_length]
    return random_serial

def check_signing_status(fw, os_name):
    checked_build_device_list = set()
    checked_board_device_list = set()
    signed_devices = []
    existing_signed = fw.get('signed', False)
    if args.signed_only and not existing_signed: return (fw, False)
    if isinstance(existing_signed, list):
        existing_signed = fw['signed'].copy()
    fw_device_map = [x for x in fw['deviceMap'] if "-" not in x and x.split(",")[0] not in blocked_prefixes.get(os_name, [])]
    fw_preinstalled_devices = []
    if isinstance(fw.get('preinstalled'), list):
        fw_preinstalled_devices = [x for x in fw['preinstalled'] if "-" not in x and x.split(",")[0] not in blocked_prefixes.get(os_name, [])]
    elif fw.get('preinstalled'):
        fw_preinstalled_devices = fw_device_map.copy()
    for source in fw['sources']:
        device_map = [x for x in source['deviceMap'] if "-" not in x and x.split(",")[0] not in blocked_prefixes.get(os_name, [])]
        cached_device_map = device_map.copy()
        if args.signed_only:
            if isinstance(existing_signed, list):
                device_map = [x for x in device_map if x in fw['signed']]
            elif not existing_signed: continue
        if not set(device_map).difference(checked_build_device_list): continue
        if not ((source['type'] == 'pkg' and os_name == 'bridgeOS') or source['type'] in ['ipsw', 'ota'] or (source['type'] == 'installassistant' and fw['build'] in ['20B50', '20D75', '23D2057', '25A8353'])): continue
        if source['type'] == 'ipsw' and os_name in ['tvOS', 'audioOS', 'watchOS'] and 'AppleTV2,1' not in fw_device_map: continue
        if fw.get('build'):
            fw_build = fw['build']
        else:
            fw_build = fw['uniqueBuild'].split('-')[0]
        link = [x for x in source['links'] if 'apple.com' in x['url'] and ('developer' not in x['url'] or fw_build in ['20A5299w'])]
        if not link: continue
        link = link[0]
        url_prefix = link['url'].rsplit('/', 1)[1].split('_', 1)[0]
        if url_prefix in ['iPhone1,1', 'iPod1,1']: continue
        parent_path = None
        if os_name in ['macOS', 'bridgeOS'] and len(cached_device_map) > 3:
            device_map_name = 'Universal'
        else:
            device_map_name = ";".join(cached_device_map)
        cached_path = f"manifest_cache/{os_str}/{fw_build}/{device_map_name}/BuildManifest.plist"
        has_cached_manifest = Path(cached_path).exists()
        if not has_cached_manifest:
            link = [x for x in source['links'] if x['active'] and 'apple.com' in x['url'] and 'developer' not in x['url']]
            if not link: continue
            link = link[0]
            print(f'Cache miss for {cached_path}, grabbing from source')
            Path(cached_path).parent.mkdir(parents=True, exist_ok=True)
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
                        if os_name == 'Studio Display Firmware':
                            path_prefix = path_prefix.removesuffix("boot/")
                        file = remotezip.RemoteZip(link['url'].replace("https://secure-appldnld", "http://appldnld"), session=session)
                        if url_prefix in ['iPhone1,2', 'iPod2,1'] and int(build[0]) == 7:
                            source_file_name = 'BuildManifesto.plist'
                        else:
                            source_file_name = 'BuildManifest.plist'
                        Path(file_path).write_bytes(file.read(f"{path_prefix}{source_file_name}"))
            shutil.copyfile(file_path, cached_path)
            Path(file_path).unlink()
            if parent_path:
                shutil.rmtree(parent_path)
        for model in device_map:
            model = model.split("-", 1)[0]
            if model.split(",")[0] in blocked_prefixes.get(os_name, []): continue
            if model in checked_build_device_list:
                if isinstance(board_ids.get(model), list):
                    if set(board_ids[model]).issubset(checked_board_device_list):
                        continue
                else:
                    continue
            
            if model in fw_preinstalled_devices:
                fw_preinstalled_devices.remove(model)
            params = ["./tsschecker", "-m", cached_path, "-d", model]
            if fw.get('basebandVersions', {}).get(model) and baseband_value.get(model):
                params.append("-c")
                params.append(generate_random_serial(baseband_value[model]))
            else:
                params.append("-b")
            signed = False
            if isinstance(board_ids.get(model), list):
                params.append("--boardconfig")
                for board in source.get('boardMap', board_ids[model]):
                    if params[-1] != '--boardconfig':
                        params.pop()
                    params.append(board)
                    signing_check = subprocess.run(params, check=False, capture_output=True)
                    signed = signed or (signing_check.returncode == 0)
                    if (args.signed_only and not signed) or not args.signed_only:
                        print(f"    {model}-{board} ({build}): {signed}")
                    checked_board_device_list.add(board)
            else:
                if board_ids.get(model):
                    params.append("--boardconfig")
                    params.append(board_ids[model])
                signing_check = subprocess.run(params, check=False, capture_output=True)
                signed = signing_check.returncode == 0
                if (args.signed_only and not signed) or not args.signed_only:
                    print(f"    {model} ({build}): {signed}")
            checked_build_device_list.add(model)
            if signed:
                signed_devices.append(model)
    if len(signed_devices) > 0:
        if len(set(fw_device_map).symmetric_difference(set(signed_devices + fw_preinstalled_devices))) == 0:
            fw['signed'] = True
        else:
            fw['signed'] = signed_devices
    elif fw.get('signed'):
        del fw['signed']
    return fw, fw.get('signed', False) != existing_signed

if args.all_signed or args.list_signed or args.unsigned:
    os_build_map = get_builds(args.os or supported_os_names, args.list_signed and args.list_devices)
    if args.list_signed:
        print(json.dumps(os_build_map, indent=4))
        exit(0)
else:
    os_build_map = dict(zip(args.os, args.build))

for os_str, builds in os_build_map.items():
    print(os_str)
    for build in builds:
        if int(build[0]) < 7 and build[1] in string.ascii_uppercase:
            continue
        print(f"  {build}")
        for file_name in Path(f'osFiles/{os_str}').rglob(f"{build}.json"):
            json_contents = json.load(file_name.open(encoding="utf-8"))
            if not [x for x in json_contents.get('sources', []) if x['type'] != 'kdk']: continue
            (json_contents, save_file) = check_signing_status(json_contents, os_str)
            for i, dup in enumerate(json_contents.get('createDuplicateEntries', [])):
                if not dup.get('sources') or not dup.get('deviceMap'): continue
                (json_contents['createDuplicateEntries'][i], dup_save_file) = check_signing_status(dup, os_str)
                save_file = save_file or dup_save_file
            if save_file:
                json.dump(sort_os_file(None, json_contents), file_name.open('w', encoding='utf-8'), indent=4)

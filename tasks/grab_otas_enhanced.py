from pathlib import Path
import re
import argparse
import base64
import json
import uuid
import requests
import urllib3
from sort_os_files import build_number_sort, device_sort

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


# Disable SSL warnings, because Apple's SSL is broken
urllib3.disable_warnings()

session = requests.session()

added_builds = {
    '19A346': ['19A340', '19A345|19A344'],
    '19B75': ['19B74'],
    '19C57': ['19C56'],
    '19G71': ['19-19G69'],
    '20H19': ['20-20H18'],
    '21A329': ['21A326'],
    '21A327': ['21A329'],
    '21A350': ['21A340', '21A351'],
    '21B80': ['21B74'],
    '21F90': ['21F101'],
    '21G80': ['21G79'],
    '22A3354': ['22A3351'],
    '22C152': ['22C154'],
}

# Ensure known versions of watchOS don't get included in import-ota.txt.
# Update this dictionary in case Apple updates watchOS for iPhones that don't support latest iOS.
latest_watch_compatibility_versions = {
    12: '5.3.9',
    18: '8.8.1',
    20: '9.6.3'
}

asset_audiences_overrides = {
    'iPadOS': 'iOS'
}

kernel_marketing_version_offset_map = {
    'macOS': 9,
    'watchOS': 11,
    'visionOS': 20
}

default_kernel_marketing_version_offset = 4

asset_audiences = json.load(Path("tasks/audiences.json").open())

mac_device_map_checks = {
    '13': set([
        "iMac18,1",
        "iMac18,2",
        "iMac18,3",
        "MacBook10,1",
        "MacBookPro14,1",
        "MacBookPro14,2",
        "MacBookPro14,3"
    ]),
    '14': set([
        "MacBookAir8,1",
        "MacBookAir8,2"
    ])
}

mac_device_map_extensions = {
    '13': set([
        "iMac19,1",
        "iMac19,2",
        "iMac20,1",
        "iMac20,2",
        "iMacPro1,1",
        "MacBookAir8,1",
        "MacBookAir8,2",
        "MacBookAir9,1",
        "MacBookPro15,1-2018",
        "MacBookPro15,1-2019",
        "MacBookPro15,2-2018",
        "MacBookPro15,2-2019",
        "MacBookPro15,3-2018",
        "MacBookPro15,3-2019",
        "MacBookPro15,4",
        "MacBookPro16,1",
        "MacBookPro16,2",
        "MacBookPro16,3",
        "MacBookPro16,4",
        "Macmini8,1",
        "MacPro7,1",
        "MacPro7,1-Rack"
    ]),
    '14': set([
        "iMac19,1",
        "iMac19,2",
        "iMac20,1",
        "iMac20,2",
        "iMacPro1,1",
        "MacBookAir9,1",
        "MacBookPro15,1-2018",
        "MacBookPro15,1-2019",
        "MacBookPro15,2-2018",
        "MacBookPro15,2-2019",
        "MacBookPro15,3-2018",
        "MacBookPro15,3-2019",
        "MacBookPro15,4",
        "MacBookPro16,1",
        "MacBookPro16,2",
        "MacBookPro16,3",
        "MacBookPro16,4",
        "Macmini8,1",
        "MacPro7,1",
        "MacPro7,1-Rack"
    ])
}

mac_device_additions = {
    '21F2081': [
        "iMac21,1",
        "iMac21,2",
        "Mac13,1",
        "Mac13,2",
        "MacBookAir10,1",
        "MacBookPro17,1",
        "MacBookPro18,1",
        "MacBookPro18,2",
        "MacBookPro18,3",
        "MacBookPro18,4",
        "Macmini9,1",
        "VirtualMac2,1"
    ],
    '24A8332': [
        "VirtualMac2,1"
    ],
    '24B2082': [
        "VirtualMac2,1"
    ],
    '24B2083': [
        "VirtualMac2,1"
    ],
    '24B2091': [
        "VirtualMac2,1"
    ],
}

choice_list = list(asset_audiences.keys())
choice_list.extend(list(asset_audiences_overrides.keys()))

parser = argparse.ArgumentParser()
parser.add_argument('-a', '--audience', default=['release'], nargs="+")
parser.add_argument('-b', '--build', action='append', nargs='+')
parser.add_argument('-d', '--devices', nargs='+')
parser.add_argument('-n', '--no-prerequisites', action='store_true')
parser.add_argument('-o', '--os', action='append', choices=choice_list)
parser.add_argument('-r', '--rsr', action='store_true')
parser.add_argument('-s', '--suffix', default="")
parser.add_argument('-t', '--time-delay', type=int, default=0, choices=range(0,91))
parser.add_argument('-u', '--update-type')
args = parser.parse_args()

file_name_base = f"import-ota-{args.suffix}" if args.suffix else "import-ota"

if args.os and args.build:
    parsed_args = dict(zip(args.os, args.build))
else:
    latest_builds = json.load(Path('tasks/latest_builds.json').open())
    beta_builds = any((x for x in args.audience if x in ['beta', 'developer', 'appleseed', 'public'])) and args.update_type != 'rc'
    is_rc = args.update_type == 'rc'
    parsed_args = {}
    for os_str, types in latest_builds.items():
        if args.os and os_str not in args.os: continue
        parsed_args.setdefault(os_str, [])
        use_beta_builds = beta_builds and not (is_rc and os_str not in ('watchOS', 'macOS'))
        if use_beta_builds:
            parsed_args[os_str].extend(latest_builds[os_str]['beta'])
        else:
            parsed_args[os_str].extend(latest_builds[os_str]['release'])

board_ids = {}
build_versions = {}
restore_versions = {}

newly_discovered_versions = {}

ota_list = {}

def generate_restore_version(build_number):
    global restore_versions
    if not restore_versions.get(build_number):
        match = re.match(r"(\d+)([A-Z])(\d+)([A-z])?", build_number)
        match_groups = match.groups()
        kernel_version = int(match_groups[0])
        build_letter = match_groups[1]
        build_iteration = int(match_groups[2])
        build_suffix = match_groups[3]

        divisor = 1000
        if build_number.startswith('20G1'):
            divisor = 10000

        restore_pieces = []

        restore_pieces.append(kernel_version)
        restore_pieces.append(ord(build_letter) - 64)
        restore_pieces.append(build_iteration % divisor)
        restore_pieces.append(int(build_iteration / divisor))
        restore_pieces.append(ord(build_suffix) - 96 if build_suffix else '0')

        restore_versions[build_number] = f"{'.'.join([str(piece) for piece in restore_pieces])},0"

    return restore_versions[build_number]

def get_board_ids(identifier):
    global board_ids
    if not board_ids.get(identifier):
        device_path = list(Path('deviceFiles').rglob(f"{identifier}.json"))[0]
        device_data = json.load(device_path.open())
        
        if device_data.get('iBridge'):
            device_path = Path(f"deviceFiles/iBridge/{device_data['iBridge']}.json")
            device_data = json.load(device_path.open())
            # iBridge board IDs need to be upper-cased
            device_data['board'] = device_data['board'].upper()
        if isinstance(device_data['board'], list):
            board_ids[identifier] = device_data['board']
        else:
            board_ids[identifier] = [device_data['board']]
    return board_ids[identifier]

def get_build_version(os_str, build):
    global build_versions
    if not build_versions.get(f"{os_str}-{build}"):
        try:
            build_path = list(Path(f'osFiles/{os_str}').rglob(f'{build}.json'))[0]
            build_data = json.load(build_path.open())
            build_versions[f"{os_str}-{build}"] = build_data['version']
        except:
            if os_str == 'iPadOS':
                build_versions[f"{os_str}-{build}"] = get_build_version('iOS', build)
            elif os_str == 'iOS':
                build_versions[f"{os_str}-{build}"] = get_build_version('iPadOS', build)
            else:
                build_versions[f"{os_str}-{build}"] = 'N/A'

    return build_versions[f"{os_str}-{build}"]

def call_pallas(device_name, board_id, os_version, os_build, os_str, audience, is_rsr, time_delay, counter=5):
    global ota_list
    global newly_discovered_versions
    asset_type = 'SoftwareUpdate'
    if is_rsr:
        asset_type = 'Splat' + asset_type

    if os_str == 'macOS':
        asset_type = 'Mac' + asset_type
    elif os_str == 'Studio Display Firmware':
        asset_type = 'DarwinAccessoryUpdate.A2525'

    # links = set()
    additional_audiences = set()

    request = {
        "ClientVersion": 2,
        "CertIssuanceDay": "2023-12-10",
        "AssetType": f"com.apple.MobileAsset.{asset_type}",
        "AssetAudience": audience,
        # Device name might have an AppleDB-specific suffix; remove this when calling Pallas
        "ProductType": device_name.split("-")[0],
        "HWModelStr": board_id,
        # Ensure no beta suffix is included
        "ProductVersion": os_version.split(" ")[0],
        "Build": os_build,
        "BuildVersion": os_build
    }
    if os_str in ['iOS', 'iPadOS', 'macOS']:
        request['RestoreVersion'] = generate_restore_version(os_build)

    if "beta" in os_version.lower() and os_str in ['audioOS', 'iOS', 'iPadOS', 'tvOS', 'visionOS']:
        request['ReleaseType'] = 'Beta'

    if time_delay > 0:
        request['DelayPeriod'] = time_delay
        request['DelayRequested'] = True
        request['Supervised'] = True

    response = session.post("https://gdmf.apple.com/v2/assets", json=request, headers={"Content-Type": "application/json"}, verify=False)

    try:
        response.raise_for_status()
    except:
        if counter == 0:
            print(json.dumps(request))
            raise
        call_pallas(device_name, board_id, os_version, os_build, os_str, audience, is_rsr, time_delay, counter - 1)
    else:
        parsed_response = json.loads(base64.b64decode(response.text.split('.')[1] + '==', validate=False))
        assets = parsed_response.get('Assets', [])
        for asset in assets:
            if asset.get("AlternateAssetAudienceUUID"):
                additional_audiences.add(asset["AlternateAssetAudienceUUID"])

            updated_build = asset['Build']
            # ensure deltas from beta builds to release builds are properly filtered out as noise as well if the target build is known
            delta_from_beta = re.search(r"(6\d{3})", updated_build)
            if delta_from_beta:
                updated_build = updated_build.replace(delta_from_beta.group(), str(int(delta_from_beta.group()) - 6000))
            if build_versions.get(f"{os_str}-{updated_build}") or updated_build in parsed_args.get(os_str, []):
                continue

            cleaned_os_version = asset['OSVersion'].removeprefix('9.9.')

            if os_str == 'watchOS' and latest_watch_compatibility_versions.get(asset['CompatibilityVersion']) == cleaned_os_version:
                continue
            link = f"{asset['__BaseURL']}{asset['__RelativePath']}"
            if not ota_list.get(f"{os_str}-{updated_build}"):
                base_details = {
                    'osStr': os_str,
                    'version': cleaned_os_version,
                    'released': parsed_response['PostingDate'],
                    'build': updated_build,
                    'buildTrain': asset.get('TrainName'),
                    'restoreVersion': asset.get('RestoreVersion'),
                    'sources': {}
                }
                if asset.get('BridgeVersionInfo'):
                    base_details['bridgeVersionInfo'] = {
                        'BridgeProductBuildVersion': asset['BridgeVersionInfo']['BridgeProductBuildVersion'],
                        'BridgeVersion': asset["BridgeVersionInfo"]["BridgeVersion"]
                    }
                ota_list[f"{os_str}-{updated_build}"] = base_details
            if not ota_list[f"{os_str}-{updated_build}"]['sources'].get(link):
                ota_list[f"{os_str}-{updated_build}"]['sources'][link] = {
                    "prerequisites": set(),
                    "deviceMap": set(),
                    "boardMap": set(),
                    "links": [{
                        "url": link,
                        "key": asset.get('ArchiveDecryptionKey')
                    }]
                }
            ota_list[f"{os_str}-{updated_build}"]['sources'][link]["deviceMap"].add(device_name)
            # iPhone11,4 is weird; nothing comes back from Pallas, but it's in the BuildManifest for the actual zip in this scenario
            if ota_list[f"{os_str}-{updated_build}"]['sources'][link]["deviceMap"].intersection({"iPhone11,2", "iPhone11,6"}) == {"iPhone11,2", "iPhone11,6"}:
                ota_list[f"{os_str}-{updated_build}"]['sources'][link]["deviceMap"].add("iPhone11,4")
            ota_list[f"{os_str}-{updated_build}"]['sources'][link]["boardMap"].add(board_id)
            if asset.get('PrerequisiteBuild'):
                ota_list[f"{os_str}-{updated_build}"]['sources'][link]['prerequisites'].add(asset['PrerequisiteBuild'])
                for additional_build in added_builds.get(asset['PrerequisiteBuild'], []):
                    if '|' in additional_build:
                        additional_build_split = additional_build.split('|')
                        if additional_build_split[0] in ota_list[f"{os_str}-{updated_build}"]['sources'][link]['prerequisites']:
                            continue
                        ota_list[f"{os_str}-{updated_build}"]['sources'][link]['prerequisites'].add(additional_build_split[1])
                    elif '-' in additional_build:
                        additional_build_split = additional_build.split('-')
                        if updated_build.startswith(additional_build_split[0]):
                            ota_list[f"{os_str}-{updated_build}"]['sources'][link]['prerequisites'].add(additional_build_split[1])
                    else:
                        ota_list[f"{os_str}-{updated_build}"]['sources'][link]['prerequisites'].add(additional_build)

            if asset.get('TrainName') and not ota_list[f"{os_str}-{updated_build}"].get('buildTrain'):
                ota_list[f"{os_str}-{updated_build}"]['buildTrain'] = asset['TrainName']

            newly_discovered_versions.setdefault(os_str, {})[updated_build] = cleaned_os_version

        for additional_audience in additional_audiences:
            call_pallas(device_name, board_id, os_version, os_build, os_str, additional_audience, is_rsr, time_delay)

def merge_dicts(original, additional):
    for k in additional.keys():
        if original.get(k):
            original[k] = [original[k], additional[k]]
        else:
            original[k] = additional[k]
    return original

beta_specific_types = ['developer', 'appleseed', 'public']
for (os_str, builds) in parsed_args.items():
    print(f"Checking {os_str}")
    target_asset_audiences = asset_audiences[asset_audiences_overrides.get(os_str, os_str)]
    for build in builds:
        print(f"\tChecking {build}")
        kern_version = re.search(r"\d+(?=[a-zA-Z])", build)
        assert kern_version
        kern_version = kern_version.group()
        audiences = []
        raw_audiences = args.audience
        unfiltered_audiences = {}
        if 'alternate' in raw_audiences:
            for sub_type in beta_specific_types:
                if target_asset_audiences['alternate'].get(sub_type):
                    target_asset_audiences[sub_type] = merge_dicts(target_asset_audiences[sub_type], target_asset_audiences['alternate'][sub_type])
            if target_asset_audiences['alternate'].get('release'):
                target_asset_audiences['release'] = [target_asset_audiences['release'], target_asset_audiences['alternate']['release']]
            raw_audiences.remove('alternate')
        for audience in raw_audiences:
            if audience == 'beta':
                desired_audiences = target_asset_audiences.get('developer', target_asset_audiences.get('appleseed', {}))
                kern_offset = kernel_marketing_version_offset_map.get(os_str, default_kernel_marketing_version_offset)

                values = [v for k,v in desired_audiences.items() if (int(k) == 12 and int(kern_version) - kern_offset == 15) or int(kern_version) - kern_offset <= int(k)]
                for value in values:
                    if isinstance(value, list):
                        audiences.extend(value)
                    else:
                        audiences.append(value)
            elif audience in beta_specific_types:
                if target_asset_audiences.get(audience):
                    kern_offset = kernel_marketing_version_offset_map.get(os_str, default_kernel_marketing_version_offset)
                    values = [v for k,v in target_asset_audiences[audience].items() if (int(k) == 12 and int(kern_version) - kern_offset == 15) or int(kern_version) - kern_offset <= int(k)]
                    for value in values:
                        if isinstance(value, list):
                            audiences.extend(value)
                        else:
                            audiences.append(value)
            elif audience == 'release':
                if isinstance(target_asset_audiences['release'], list):
                    audiences.extend(target_asset_audiences['release'])
                else:
                    audiences.append(target_asset_audiences['release'])
            else:
                try:
                    uuid.UUID(audience)
                    audiences.append(audience)
                except:
                    print(f"Invalid audience {audience}, skipping")
                    continue
        build_path = list(Path(f"osFiles/{os_str}").glob(f"{kern_version}x*"))[0].joinpath(f"{build}.json")
        devices = {}
        build_data = {}
        try:
            build_data = json.load(build_path.open())
        except:
            print(f"Bad path - {build_path}")
            continue
        build_versions[f"{os_str}-{build}"] = build_data['version']

        for device in build_data['deviceMap']:
            if args.devices and device not in args.devices:
                continue
            devices.setdefault(device, {
                'boards': get_board_ids(device),
                'builds': {}
            })
        
        # RSRs are only for the latest version
        if not args.rsr and not args.no_prerequisites:
            for source in build_data.get("sources", []):
                if not source.get('prerequisiteBuild'):
                    continue

                if args.devices:
                    current_devices = set(args.devices).intersection(set(source['deviceMap']))
                    if current_devices:
                        current_devices = list(current_devices)
                    else:
                        continue
                else:
                    current_devices = source['deviceMap']

                prerequisite_builds = source['prerequisiteBuild']
                if not isinstance(prerequisite_builds, list):
                    prerequisite_builds = [prerequisite_builds]

                for current_device in current_devices:
                    for prerequisite_build in prerequisite_builds:
                        devices[current_device]['builds'][prerequisite_build] = get_build_version(os_str, prerequisite_build)

        for audience in audiences:
            for key, value in devices.items():
                for board in value['boards']:
                    if not (args.no_prerequisites or os_str == 'tvOS'):
                        for prerequisite_build, version in value['builds'].items():
                            call_pallas(key, board, version, prerequisite_build, os_str, audience, args.rsr, args.time_delay)
                    call_pallas(key, board, build_data['version'], build, os_str, audience, args.rsr, args.time_delay)

                    new_version_builds = sorted([x for x in newly_discovered_versions.get(os_str, {}).keys() if x < build])
                    for new_build in new_version_builds:
                        call_pallas(key, board, newly_discovered_versions[os_str][new_build], new_build, os_str, audience, args.rsr, args.time_delay)

for key in ota_list.keys():
    sources = []
    for source in ota_list[key]['sources'].values():
        if ota_list[key]['osStr'] == 'macOS':
            if source['deviceMap'] == mac_device_map_checks.get(ota_list[key]['version'].split('.')[0], set()):
                source['deviceMap'].update(mac_device_map_extensions[ota_list[key]['version'].split('.')[0]])
            if bool(set(mac_device_additions.keys()).intersection(source['prerequisites'])):
                for prerequisite in source['prerequisites']:
                    source['deviceMap'].update(mac_device_additions.get(prerequisite, []))
        source['deviceMap'] = sorted(list(source['deviceMap']), key=device_sort)
        source['prerequisites'] = sorted(list(source['prerequisites']), key=build_number_sort)
        source['boardMap'] = sorted(list(source['boardMap']))
        sources.append(source)
    ota_list[key]['sources'] = sources
if bool(ota_list.keys()):
    print(f"{len([x for x in ota_list.values() for y in x['sources'] for z in y['links']])} links added")
    [i.unlink() for i in Path.cwd().glob(f"{file_name_base}.*") if i.is_file()]
    json.dump(list(ota_list.values()), Path(f"{file_name_base}.json").open("w", encoding="utf-8"), indent=4, cls=SetEncoder)
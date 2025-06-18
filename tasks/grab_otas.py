from pathlib import Path
import re
import argparse
import base64
import json
import uuid
import requests
import urllib3

# Disable SSL warnings, because Apple's SSL is broken
urllib3.disable_warnings()

session = requests.session()

# Some builds show up as prerequisites in the zip file, but don't give a response from Pallas in some cases; skip those
skip_builds = {
    '19A340': [],
    '19A344': [],
    '19B74': [
        'iPad14,1'
    ],
    '19C56': [
        'iPhone14,2',
        'iPhone14,3',
        'iPhone14,4',
        'iPhone14,5'
    ],
    '21A326': [],
    '21A340': [
        'iPhone15,4',
        'iPhone15,5',
        'iPhone16,1',
        'iPhone16,2',
    ],
    '21A351': [
        'iPhone15,4',
        'iPhone15,5',
        'iPhone16,1',
        'iPhone16,2',
    ],
    '21B74': [
        'iPhone15,4',
        'iPhone15,5',
        'iPhone16,1',
        'iPhone16,2',
    ],
    '21G79': [],
    '21H15': [],
    '22A3351': [],
    '22B82': [],
}

# Ensure known versions of watchOS don't get included in import-ota.txt.
# Update this dictionary in case Apple updates watchOS for iPhones that don't support latest iOS.
latest_watch_compatibility_versions = {
    12: '5.3.9',
    18: '8.8.1',
    20: '9.6.3'
}

default_mac_devices = [
    'iMac18,1',         # Intel, only supports up to Ventura
    'MacBookAir8,1',    # Intel, only supports up to Sonoma
    'MacBookAir9,1',    # Intel, only supports up to Sequoia
    'MacPro7,1',        # Intel, supports Tahoe
    'MacBookPro18,1',   # M1 Pro, covers all released Apple Silicon builds
    'Mac14,2',          # Covers Monterey 12.4 (WWDC 2022) forked builds
    'Mac14,6',          # Covers Ventura 13.0 forked builds
    'Mac14,15',         # Covers Ventura 13.3/13.4 (WWDC 2023) forked builds
    'Mac15,3',          # Covers Ventura 13.5/13.6.2 and Sonoma 14.1 forked builds
    'Mac15,12',         # Covers Sonoma 14.3 forked builds
    'Mac16,1',          # Covers Sequoia 15.0/15.1 forked builds
    'Mac16,12',         # Covers Sequoia 15.2/15.3 forked builds
]

asset_audiences_overrides = {
    'iPadOS': 'iOS'
}

kernel_marketing_version_offset_map = {
    'macOS': 9,
    'watchOS': 11,
    'visionOS': 20
}

default_kernel_marketing_version_offset = 4

asset_audiences = asset_audiences = json.load(Path("tasks/audiences.json").open(encoding="utf-8"))

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

is_rc = args.update_type == 'rc'
is_next_major = args.update_type == 'next'
if args.os and args.build:
    parsed_args = dict(zip(args.os, args.build))
else:
    latest_builds = json.load(Path('tasks/latest_builds.json').open(encoding="utf-8"))
    beta_builds = is_next_major or any((x for x in args.audience if x in ['beta', 'developer', 'appleseed', 'public']))
    parsed_args = {}
    for os_str, types in latest_builds.items():
        if args.os and os_str not in args.os: continue
        parsed_args.setdefault(os_str, [])
        parsed_args[os_str].extend(latest_builds[os_str]['rc' if is_rc else 'beta' if beta_builds else 'release'])
        if is_next_major:
            parsed_args[os_str].extend(latest_builds[os_str]['next'])

minimum_compatibility = 0
maximum_compatibility = 1000
if parsed_args.get('watchOS'):
    compatibility_builds = sorted(parsed_args['watchOS'])
    def generate_build_compatibility_version(target_build):
        return ((int(target_build[0:2]) - 12) * 2) + 4

    minimum_compatibility = generate_build_compatibility_version(compatibility_builds[0]) - 1
    maximum_compatibility = generate_build_compatibility_version(compatibility_builds[-1]) + 1

board_ids = {}
build_versions = {}
restore_versions = {}

def generate_restore_version(build_number):
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
    if not board_ids.get(identifier):
        device_path = list(Path('deviceFiles').rglob(f"{identifier}.json"))[0]
        device_data = json.load(device_path.open())
        
        if device_data.get('iBridge'):
            device_path = Path(f"deviceFiles/iBridge/{device_data['iBridge']}.json")
            device_data = json.load(device_path.open(encoding="utf-8"))
            # iBridge board IDs need to be upper-cased
            device_data['board'] = device_data['board'].upper()
        if isinstance(device_data['board'], list):
            board_ids[identifier] = device_data['board']
        else:
            board_ids[identifier] = [device_data['board']]
    return board_ids[identifier]

def get_build_version(target_os_str, target_build):
    if not build_versions.get(f"{target_os_str}-{target_build}"):
        try:
            version_path = list(Path(f'osFiles/{target_os_str}').rglob(f'{target_build}.json'))[0]
            version_data = json.load(version_path.open())
            build_versions[f"{target_os_str}-{target_build}"] = version_data['version']
        except FileNotFoundError:
            if target_os_str == 'iPadOS':
                build_versions[f"{target_os_str}-{target_build}"] = get_build_version('iOS', target_build)
            elif target_os_str == 'iOS':
                build_versions[f"{target_os_str}-{target_build}"] = get_build_version('iPadOS', target_build)
            else:
                build_versions[f"{target_os_str}-{target_build}"] = 'N/A'

    return build_versions[f"{target_os_str}-{target_build}"]

def call_pallas(device_name, board_id, os_version, os_build, source_os_str, asset_audience, is_rsr, time_delay, counter=5):
    asset_type = 'SoftwareUpdate'
    if is_rsr:
        asset_type = 'Splat' + asset_type
    if source_os_str == 'macOS':
        asset_type = 'Mac' + asset_type
    elif source_os_str == 'Studio Display Firmware':
        asset_type = 'DarwinAccessoryUpdate.A2525'

    links = set()
    newly_added_versions = {}
    additional_audiences = set()

    request = {
        "ClientVersion": 2,
        "CertIssuanceDay": "2024-12-05",
        "AssetType": f"com.apple.MobileAsset.{asset_type}",
        "AssetAudience": asset_audience,
        # Device name might have an AppleDB-specific suffix; remove this when calling Pallas
        "ProductType": device_name.split("-")[0],
        "HWModelStr": board_id,
        # Ensure no beta suffix is included
        "ProductVersion": os_version.split(" ")[0],
        "Build": os_build,
        "BuildVersion": os_build
    }
    if source_os_str in ['iOS', 'iPadOS', 'macOS']:
        request['RestoreVersion'] = generate_restore_version(os_build)
    elif source_os_str == 'watchOS':
        request['DeviceName'] = 'Apple Watch'
        request['MinCompanionCompatibilityVersion'] = minimum_compatibility
        request['MaxCompanionCompatibilityVersion'] = maximum_compatibility

    if "beta" in os_version.lower() and source_os_str in ['audioOS', 'iOS', 'iPadOS', 'tvOS', 'visionOS']:
        request['ReleaseType'] = 'Beta'

    if time_delay > 0:
        request['DelayPeriod'] = time_delay
        request['DelayRequested'] = True
        request['Supervised'] = True

    response = session.post("https://gdmf.apple.com/v2/assets", json=request, headers={"Content-Type": "application/json"}, verify=False)

    try:
        response.raise_for_status()
    except requests.HTTPError:
        if counter == 0:
            print(json.dumps(request))
            raise
        return call_pallas(device_name, board_id, os_version, os_build, source_os_str, asset_audience, is_rsr, time_delay, counter - 1)

    parsed_response = json.loads(base64.b64decode(response.text.split('.')[1] + '==', validate=False))
    assets = parsed_response.get('Assets', [])
    for asset in assets:
        if asset.get("AlternateAssetAudienceUUID"):
            additional_audiences.add(asset["AlternateAssetAudienceUUID"])
        if build_versions.get(f"{source_os_str}-{asset['Build']}") or asset['Build'] in parsed_args.get(source_os_str, []):
            continue

        # ensure deltas from beta builds to release builds are properly filtered out as noise as well if the target build is known
        delta_from_beta = re.search(r"(6\d{3})", asset['Build'])
        if delta_from_beta:
            if build_versions.get(f"{source_os_str}-{asset['Build'].replace(delta_from_beta.group(), str(int(delta_from_beta.group()) - 6000))}"):
                continue

        cleaned_os_version = asset['OSVersion'].removeprefix('9.9.')

        if source_os_str == 'watchOS' and latest_watch_compatibility_versions.get(asset['CompatibilityVersion']) == cleaned_os_version:
            continue

        newly_added_versions[asset['Build']] = cleaned_os_version

        if asset.get('ArchiveDecryptionKey'):
            new_link = f"{asset['__BaseURL']}{asset['__RelativePath']};{asset['ArchiveDecryptionKey']}"
        else:
            new_link = f"{asset['__BaseURL']}{asset['__RelativePath']}"

        links.add(new_link)

    for additional_audience in additional_audiences:
        additional_links, additional_versions = call_pallas(device_name, board_id, os_version, os_build, source_os_str, additional_audience, is_rsr, time_delay)
        links.update(additional_links)
        newly_added_versions |= additional_versions
    return links, newly_added_versions

def merge_dicts(original, additional):
    for k in additional.keys():
        if original.get(k):
            original[k] = [original[k], additional[k]]
        else:
            original[k] = additional[k]
    return original

beta_specific_types = ['developer', 'appleseed', 'public']

ota_links = set()
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
            if not raw_audiences:
                raw_audiences.append('release')
        for audience in raw_audiences:
            if audience == 'beta':
                desired_audiences = target_asset_audiences.get('developer', target_asset_audiences.get('appleseed', {}))
                kern_offset = kernel_marketing_version_offset_map.get(os_str, default_kernel_marketing_version_offset)

                values = [v for k,v in desired_audiences.items() if (int(k) == 12 and int(kern_version) - kern_offset == 15) or int(kern_version) - kern_offset <= int(k)]
                for value in values:
                    if not value: continue
                    if isinstance(value, list):
                        audiences.extend(value)
                    else:
                        audiences.append(value)
            elif audience in beta_specific_types:
                if target_asset_audiences.get(audience):
                    kern_offset = kernel_marketing_version_offset_map.get(os_str, default_kernel_marketing_version_offset)
                    values = [v for k,v in target_asset_audiences[audience].items() if (int(k) == 12 and int(kern_version) - kern_offset == 15) or int(kern_version) - kern_offset <= int(k)]
                    for value in values:
                        if not value: continue
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
                except ValueError:
                    print(f"Invalid audience {audience}, skipping")
                    continue
        build_path = list(Path(f"osFiles/{os_str}").glob(f"{kern_version}x*"))[0].joinpath(f"{build}.json")
        devices = {}
        build_data = {}
        try:
            build_data = json.load(build_path.open())
        except FileNotFoundError:
            print(f"Bad path - {build_path}")
            continue
        build_versions[f"{os_str}-{build}"] = build_data['version']
        for device in build_data['deviceMap']:
            if args.devices and device not in args.devices:
                continue
            if os_str == 'macOS' and not args.devices and device not in default_mac_devices:
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
                elif os_str == 'macOS':
                    current_devices = set(default_mac_devices).intersection(set(source['deviceMap']))
                    if current_devices:
                        current_devices = list(current_devices)
                    else:
                        continue
                else:
                    current_devices = source['deviceMap']

                prerequisite_builds = source['prerequisiteBuild']

                for current_device in current_devices:
                    if isinstance(prerequisite_builds, list):
                        for prerequisite_build_option in prerequisite_builds:
                            if skip_builds.get(prerequisite_build_option) is not None:
                                if len(skip_builds[prerequisite_build_option]) == 0 or current_device in skip_builds[prerequisite_build_option]:
                                    continue
                            prerequisite_build = prerequisite_build_option
                            break
                    else:
                        prerequisite_build = prerequisite_builds
                    devices[current_device]['builds'][prerequisite_build] = get_build_version(os_str, prerequisite_build)

        for key, value in devices.items():
            new_versions = {}
            for audience in audiences:
                for board in value['boards']:
                    if not args.no_prerequisites:
                        for prerequisite_build, version in value['builds'].items():
                            new_links, newly_discovered_versions = call_pallas(key, board, version, prerequisite_build, os_str, audience, args.rsr, args.time_delay)
                            ota_links.update(new_links)
                            new_versions |= newly_discovered_versions
                    new_links, newly_discovered_versions = call_pallas(key, board, build_data['version'], build, os_str, audience, args.rsr, args.time_delay)
                    ota_links.update(new_links)
                    new_versions |= newly_discovered_versions

                    new_version_builds = sorted(new_versions.keys())[:-1]
                    for new_build in new_version_builds:
                        new_links, _ = call_pallas(key, board, new_versions[new_build], new_build, os_str, audience, args.rsr, args.time_delay)
                        ota_links.update(new_links)

if bool(ota_links):
    print(f"{len(ota_links)} links added")
    _ = [i.unlink() for i in Path.cwd().glob(f"{file_name_base}.*") if i.is_file()]
    Path(f"{file_name_base}.txt").write_text("\n".join(sorted(ota_links)), "utf-8")

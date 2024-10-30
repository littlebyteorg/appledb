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
    ]
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
    'MacPro7,1',        # Intel, supports Sequoia
    'MacBookPro18,1',   # M1 Pro, covers all released Apple Silicon builds
    'Mac14,2',          # Covers Monterey 12.4 (WWDC 2022) forked builds
    'Mac14,6',          # Covers Ventura 13.0 forked builds
    'Mac14,15',         # Covers Ventura 13.3/13.4 (WWDC 2023) forked builds
    'Mac15,3',          # Covers Ventura 13.5/13.6.2 and Sonoma 14.1 forked builds
    'Mac15,12',         # Covers Sonoma 14.3 forked builds
    'Mac16,1',          # Covers Sequoia 15.0/15.1 forked builds
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

asset_audiences = {
    'iOS': {
        'beta': {
            15: 'ce48f60c-f590-4157-a96f-41179ca08278',
            16: 'a6050bca-50d8-4e45-adc2-f7333396a42c',
            17: '9dcdaf87-801d-42f6-8ec6-307bd2ab9955',
            18: '41651cee-d0e2-442f-b786-85682ff6db86'
        },
        'public': {
            15: '9e12a7a5-36ac-4583-b4fb-484736c739a8',
            16: '7466521f-cc37-4267-8f46-78033fa700c2',
            17: '48407998-4446-46b0-9f57-f76b935dc223',
            18: 'c46ed8dd-1382-40bd-a153-2b6ad61292fd'
        },
        'release': '01c1d682-6e8f-4908-b724-5501fe3f5e5c',
        'security': 'c724cb61-e974-42d3-a911-ffd4dce11eda'
    },
    'macOS': {
        'alternate': '1831c3e6-1dc4-4f6b-a9dc-7ae6a41d9af4',
        'beta': {
            12: '298e518d-b45e-4d36-94be-34a63d6777ec',
            13: '683e9586-8a82-4e5f-b0e7-767541864b8b',
            14: '77c3bd36-d384-44e8-b550-05122d7da438',
            15: '98df7800-8378-4469-93bf-5912da21a1e1'
        },
        'public': {
            12: '9f86c787-7c59-45a7-a79a-9c164b00f866',
            13: '800034a9-994c-4ecc-af4d-7b3b2ee0a5a6',
            14: '707ddc61-9c3d-4040-a3d0-2a6521b1c2df',
            15: 'c8ba02c8-cc63-4388-99ee-a81d5a593283'
        },
        'release': '60b55e25-a8ed-4f45-826c-c1495a4ccc65'
    },
    'tvOS': {
        'beta': {
            17: '61693fed-ab18-49f3-8983-7c3adf843913',
            18: '98847ed4-1c37-445c-9e7b-5b95d29281f2'
        },
        'public': {
            17: 'd9159cba-c93c-4e6d-8f9f-4d77b27b3a5e',
            18: '879ce2f8-b7d1-420f-9935-58d647d6606a'
        },
        'release': '356d9da0-eee4-4c6c-bbe5-99b60eadddf0'
    },
    'watchOS': {
        'beta': {
            10: '7ae7f3b9-886a-437f-9b22-e9f017431b0e',
            11: '23d7265b-1000-47cf-8d0a-07144942db9e'
        },
        'public': {
            10: 'f3d4d255-9db8-425c-bf9a-fea7dcdb940b',
            11: '79b47e0c-cbce-4757-b84b-12a95db52f22'
        },
        'release': 'b82fcf9c-c284-41c9-8eb2-e69bf5a5269f'
    },
    'audioOS': {
        'beta': {
            17: '17536d4c-1a9d-4169-bc62-920a3873f7a5',
            18: 'bedbd9c7-738a-4060-958b-79da54a1f7ad'
        },
        'public': {
            17: 'f7655fc0-7a0a-43fa-b781-170a834a3108',
            18: '1af931ed-e171-4dd0-b944-172cdebcd89d'
        },
        'release': '0322d49d-d558-4ddf-bdff-c0443d0e6fac'
    },
    'visionOS': {
        'beta': {
            1: '4d282764-95fe-4e0e-b7da-ea218fd1f75a',
            2: '0bef3239-79ad-4d2a-99c3-2c05df2becf8'
        },
        'release': 'c59ff9d1-5468-4f6c-9e54-f68d5eeab93b'
    },
    'Studio Display Firmware': {
        'release': '02d8e57e-dd1c-4090-aa50-b4ed2aef0062'
    }
}

choice_list = list(asset_audiences.keys()).extend(list(asset_audiences_overrides.keys()))

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--os', required=True, action='append', choices=choice_list)
parser.add_argument('-b', '--build', required=True, action='append', nargs='+')
parser.add_argument('-a', '--audience', default=['release'], nargs="+")
parser.add_argument('-r', '--rsr', action='store_true')
parser.add_argument('-d', '--devices', nargs='+')
parser.add_argument('-n', '--no-prerequisites', action='store_true')
parser.add_argument('-t', '--time-delay', type=int, default=0, choices=range(0,91))
args = parser.parse_args()

parsed_args = dict(zip(args.os, args.build))

board_ids = {}
build_versions = {}
restore_versions = {}

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

def get_build_version(osStr, build):
    global build_versions
    if not build_versions.get(f"{osStr}-{build}"):
        build_path = list(Path(f'osFiles/{osStr}').rglob(f'{build}.json'))[0]
        build_data = json.load(build_path.open())
        build_versions[f"{osStr}-{build}"] = build_data['version']

    return build_versions[f"{osStr}-{build}"]

def call_pallas(device_name, board_id, os_version, os_build, os_str, audience, is_rsr, time_delay, counter=5):
    asset_type = 'SoftwareUpdate'
    if is_rsr:
        asset_type = 'Splat' + asset_type
    if os_str == 'macOS':
        asset_type = 'Mac' + asset_type
    elif os_str == 'Studio Display Firmware':
        asset_type = 'DarwinAccessoryUpdate.A2525'

    links = set()
    newly_discovered_versions = {}
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
            print(request)
            raise
        return call_pallas(device_name, board_id, os_version, os_build, os_str, audience, is_rsr, time_delay, counter - 1)

    parsed_response = json.loads(base64.b64decode(response.text.split('.')[1] + '==', validate=False))
    assets = parsed_response.get('Assets', [])
    for asset in assets:
        if asset.get("AlternateAssetAudienceUUID"):
            additional_audiences.add(asset["AlternateAssetAudienceUUID"])
        if build_versions.get(f"{os_str}-{asset['Build']}") or asset['Build'] in parsed_args.get(os_str, []):
            continue

        # ensure deltas from beta builds to release builds are properly filtered out as noise as well if the target build is known
        delta_from_beta = re.search(r"(6\d{3})", asset['Build'])
        if delta_from_beta:
            if build_versions.get(f"{os_str}-{asset['Build'].replace(delta_from_beta.group(), str(int(delta_from_beta.group()) - 6000))}"):
                continue

        cleaned_os_version = asset['OSVersion'].removeprefix('9.9.')

        if os_str == 'watchOS' and latest_watch_compatibility_versions.get(asset['CompatibilityVersion']) == cleaned_os_version:
            continue

        newly_discovered_versions[asset['Build']] = cleaned_os_version

        if asset.get('ArchiveDecryptionKey'):
            new_link = f"{asset['__BaseURL']}{asset['__RelativePath']};{asset['ArchiveDecryptionKey']}"
        else:
            new_link = f"{asset['__BaseURL']}{asset['__RelativePath']}"

        links.add(new_link)

    for additional_audience in additional_audiences:
        additional_links, additional_versions = call_pallas(device_name, board_id, os_version, os_build, os_str, additional_audience, is_rsr, time_delay)
        links.update(additional_links)
        newly_discovered_versions |= additional_versions
    return links, newly_discovered_versions

ota_links = set()
for (os_str, builds) in parsed_args.items():
    print(f"Checking {os_str}")
    for build in builds:
        print(f"\tChecking {build}")
        kern_version = re.search(r"\d+(?=[a-zA-Z])", build)
        assert kern_version
        kern_version = kern_version.group()
        audiences = []
        for audience in args.audience:
            try:
                # Allow for someone to pass in a specific asset audience UUID
                uuid.UUID(audience)
                audiences.append(audience)
            except:
                target_asset_audiences = asset_audiences[asset_audiences_overrides.get(os_str, os_str)]
                if audience in ['beta', 'public']:
                    if target_asset_audiences.get(audience):
                        kern_offset = kernel_marketing_version_offset_map.get(os_str, default_kernel_marketing_version_offset)
                        audiences.extend({k:v for k,v in target_asset_audiences[audience].items() if (k == 12 and int(kern_version) - kern_offset == 15) or int(kern_version) - kern_offset <= k}.values())
                else:
                    audiences.append(target_asset_audiences.get(audience, audience))
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
                if isinstance(prerequisite_builds, list):
                    for prerequisite_build_option in prerequisite_builds:
                        if skip_builds.get(prerequisite_build_option) is not None:
                            if len(skip_builds[prerequisite_build_option]) == 0 or current_device in skip_builds[prerequisite_build_option]:
                                continue
                        prerequisite_build = prerequisite_build_option
                        break
                else:
                    prerequisite_build = prerequisite_builds

                for current_device in current_devices:
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

[i.unlink() for i in Path.cwd().glob("import-ota.*") if i.is_file()]
Path("import-ota.txt").write_text("\n".join(sorted(ota_links)), "utf-8")

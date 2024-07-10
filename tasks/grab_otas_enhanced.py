from pathlib import Path
import re
import argparse
import base64
import json
import uuid
import requests
import urllib3

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
    '21B80': ['21B74']
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
        },
        'release': '01c1d682-6e8f-4908-b724-5501fe3f5e5c',
        'security': 'c724cb61-e974-42d3-a911-ffd4dce11eda'
    },
    'macOS': {
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
            17: 'd9159cba-c93c-4e6d-8f9f-4d77b27b3a5e'
        },
        'release': '356d9da0-eee4-4c6c-bbe5-99b60eadddf0'
    },
    'watchOS': {
        'beta': {
            10: '7ae7f3b9-886a-437f-9b22-e9f017431b0e',
            11: '23d7265b-1000-47cf-8d0a-07144942db9e'
        },
        'public': {
            10: 'f3d4d255-9db8-425c-bf9a-fea7dcdb940b'
        },
        'release': 'b82fcf9c-c284-41c9-8eb2-e69bf5a5269f'
    },
    'audioOS': {
        'beta': {
            17: '17536d4c-1a9d-4169-bc62-920a3873f7a5',
            18: 'bedbd9c7-738a-4060-958b-79da54a1f7ad'
        },
        'public': {
            17: 'f7655fc0-7a0a-43fa-b781-170a834a3108'
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

        restore_pieces = []

        restore_pieces.append(kernel_version)
        restore_pieces.append(ord(build_letter) - 64)
        restore_pieces.append(build_iteration % 1000)
        restore_pieces.append(int(build_iteration / 1000))
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
                ota_list[f"{os_str}-{updated_build}"] = {
                    'osStr': os_str,
                    'version': cleaned_os_version,
                    'released': parsed_response['PostingDate'],
                    'build': updated_build,
                    'buildTrain': asset.get('TrainName'),
                    'sources': {}
                }
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

            newly_discovered_versions[updated_build] = cleaned_os_version

        for additional_audience in additional_audiences:
            call_pallas(device_name, board_id, os_version, os_build, os_str, additional_audience, is_rsr, time_delay)

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
                        audiences.extend({k:v for k,v in target_asset_audiences[audience].items() if int(kern_version) - kern_offset <= k}.values())
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
                    if not args.no_prerequisites:
                        for prerequisite_build, version in value['builds'].items():
                            call_pallas(key, board, version, prerequisite_build, os_str, audience, args.rsr, args.time_delay)
                    call_pallas(key, board, build_data['version'], build, os_str, audience, args.rsr, args.time_delay)

                    new_version_builds = sorted(newly_discovered_versions.keys())[:-1]
                    for new_build in new_version_builds:
                        call_pallas(key, board, newly_discovered_versions[new_build], new_build, os_str, audience, args.rsr, args.time_delay)
                    newly_discovered_versions = {}

for key in ota_list.keys():
    ota_list[key]['sources'] = list(ota_list[key]['sources'].values())

[i.unlink() for i in Path.cwd().glob("import-ota.*") if i.is_file()]
json.dump(list(ota_list.values()), Path("import-ota.json").open("w", encoding="utf-8"), indent=4, cls=SetEncoder)
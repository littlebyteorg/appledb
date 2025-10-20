#!/usr/bin/env python3

import base64
from datetime import datetime
import json
import plistlib
from pathlib import Path
import re
import zoneinfo
import random

import dateutil.parser
import requests

from sort_os_files import sort_os_file
from update_links import update_links

session = requests.session()

xcode_response = session.get('https://xcodereleases.com/data.json').json()
simulator_response = plistlib.loads(session.get(f'https://devimages-cdn.apple.com/downloads/xcode/simulators/index2.dvtdownloadableindex?cachebust{random.randint(100, 1000)}').content)

simulator_pallas_mapping = {
    'iOS': 'iOSSimulatorRuntime',
    'tvOS': 'appleTVOSSimulatorRuntime',
    'watchOS': 'watchOSSimulatorRuntime',
    'visionOS': 'xrOSSimulatorRuntime'
}

def call_pallas(os, requested_build):
    request = {
        "ClientVersion": 2,
        "CertIssuanceDay": "2024-12-05",
        "AssetType": f"com.apple.MobileAsset.{simulator_pallas_mapping[os]}",
        "AssetAudience": "02d8e57e-dd1c-4090-aa50-b4ed2aef0062",
        "RequestedBuild": requested_build
    }
    response = session.post("https://gdmf.apple.com/v2/assets", json=request, headers={"Content-Type": "application/json"}, verify=False)
    parsed_response = json.loads(base64.b64decode(response.text.split('.')[1] + '==', validate=False))
    assets = parsed_response.get('Assets', [])
    parsed_assets = []
    for asset in assets:
        parsed_asset = {
            'type': asset['__RelativePath'].split('.')[-1],
            'deviceMap': [f"{os} Simulator"],
            'links': [
                {
                    'url': f"{asset['__BaseURL']}{asset['__RelativePath']}",
                    'decryptionKey': asset.get("ArchiveDecryptionKey")
                }
            ],
            'size': asset['_DownloadSize']
        }
        if asset.get('Architectures'):
            parsed_asset['arch'] = asset['Architectures']
        parsed_assets.append(parsed_asset)
    return parsed_assets, parsed_response.get("PostingDate")

def get_build_train(target_build):
    base_build_train_map = {
        '13': 'Sunriver',
        '14': 'Summit',
        '15': 'Rainbow',
        '16': 'Geode',
        '17': 'Wonder',
    }
    build_type_map = {
        '5': 'Seed',
        '7': 'HW'
    }
    build_type = ''
    if len(target_build) >= 7 and target_build[6].isdigit():
        build_type = build_type_map.get(target_build[3], '')
    
    minor_letter = target_build[2] if target_build[2] != 'A' else ''

    base_build_train = base_build_train_map[target_build[:2]]
    
    return f"{base_build_train}{minor_letter}{build_type}"

sdk_platform_mapping = {
    'iOS': 'iphoneos',
    'macOS': 'macosx',
    'tvOS': 'appletvos',
    'watchOS': 'watchos',
    'visionOS': 'xros'
}

major_version_offset = {
    'macOS': 9,
    'visionOS': 20,
    'watchOS': 11
}
    

for xcode_version in xcode_response:
    # HACK: xcodereleases.com is incomplete for this
    if xcode_version['version']['build'] == '10M25xx':
        xcode_version['version']['build'] = '10M2518'
    if xcode_version['version']['build'] == '5A2039a':
        xcode_version['version']['build'] = '5A2034a'
    if xcode_version['version']['build'] == '17A5295f' and xcode_version['version']['release'].get('beta') == 6:
        xcode_version['version']['build'] = '17A5305f'
    
    build_version = re.search(r"\d+(?=[a-zA-Z])", xcode_version['version']['build']).group()
    major_version = xcode_version['version']['number'].split(".")[0]
    if int(major_version) < 16: continue
    if major_version == '3':
        if build_version == '10':
            major_version_range = "3.2.x"
        else:
            major_version_range = "3.0.x to 3.1.x"
    else:
        major_version_range = f"{major_version}.x"
    file_path = Path(f"osFiles/Software/Xcode/{build_version}x - {major_version_range}/{xcode_version['version']['build']}.json")
    os_map = [f'macOS {x}' for x in range(int(xcode_version['requires'].split(".")[0]), int(xcode_version['version']['number'].split('.')[0]) + 1) if x not in range(16, 26)]
    if xcode_version.get('links', {}).get('download'):
        current_link = xcode_version['links']['download']['url'].replace('download.developer.apple.com', 'developer.apple.com/services-account/download?path=')
    else:
        current_link = ''
    if file_path.exists():
        new_item = json.load(file_path.open(encoding="utf-8"))
        links = [y['url'].lower() for x in new_item.get('sources', []) for y in x['links']]
        for dup in new_item.get('createDuplicateEntries', []):
            links.extend([y['url'].lower() for x in dup.get('sources', []) for y in x['links']])
        if not xcode_version.get('links'): continue

        # xcode_version['links']['download']['url'].replace('download.developer.apple.com', 'developer.apple.com/services-account/download?path=')
        if current_link.lower() in links:
            continue
        else:
            print(xcode_version['version']['build'])
            print(current_link)
    else:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        formatted_sdks = []

        for sdk_key in xcode_version['sdks'].keys():
            for sdk_item in xcode_version['sdks'][sdk_key]:
                if not sdk_item.get('build'): continue
                sdk_mapping = [mapping for mapping in simulator_response['sdkToSeedMappings'] \
                            if mapping['buildUpdate'] == sdk_item['build'] \
                                and mapping['platform'] == f"com.apple.platform.{sdk_platform_mapping[sdk_key]}"]

                sdk = {
                    'osStr': sdk_key,
                    'version': sdk_item['number'],
                    'build': sdk_item['build']
                }

                if sdk_mapping:
                    sdk_mapping = sdk_mapping[0]
                    sdk['beta'] = True
                    sdk['version'] += ' beta'
                    if int(sdk_mapping['seedNumber']) > 1:
                        sdk['version'] += f" {sdk_mapping['seedNumber']}"

                formatted_sdks.append(sdk)

        new_item = {
            'osStr': xcode_version['name'],
            'version': xcode_version['version']['number'],
            'build': xcode_version['version']['build'],
            'buildTrain': get_build_train(xcode_version['version']['build']),
            'released': dateutil.parser.parse(f"{xcode_version['date']['year']}-{xcode_version['date']['month']}-{xcode_version['date']['day']}").strftime("%Y-%m-%d"),
            'releaseNotes': xcode_version['links']['notes']['url'].replace('download.developer.apple.com', 'developer.apple.com/services-account/download?path='),
            'deviceMap': ['Xcode'],
            'osMap': os_map,
            'sdks': formatted_sdks,
            'sources': []
        }

        if xcode_version['version']['release'].get('beta'):
            new_item['beta'] = True
            if xcode_version['version']['release']['beta'] == 1:
                new_item['version'] += ' beta'
            else:
                new_item['version'] += f" beta {xcode_version['version']['release']['beta']}"
        elif xcode_version['version']['release'].get('rc'):
            new_item['rc'] = True
            if xcode_version['version']['release']['rc'] == 1:
                new_item['version'] += ' RC'
            else:
                new_item['version'] += f" RC {xcode_version['version']['release']['rc']}"

    if current_link:
        new_source = {
            'type': xcode_version['links']['download']['url'].split('.')[-1],
            'deviceMap': ['Xcode'],
            'osMap': os_map,
            'links': [
                {
                    'url': current_link,
                }
            ],
            'hashes': xcode_version['checksums']
        }
        if '_universal.' in current_link.lower():
            new_source['arch'] = [
                'arm64',
                'x86_64'
            ]
        elif '_silicon.' in current_link.lower():
            new_source['arch'] = [
                'arm64'
            ]
        new_item['sources'].append(new_source)
    json.dump(sort_os_file(None, new_item), file_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    update_links([file_path])

for simulator in simulator_response['downloadables']:
    simulator['name'] = simulator['name'].replace('xrOS', 'visionOS')
    os_str = simulator['name'].split(' ')[0]

    build = simulator['simulatorVersion']['buildUpdate']

    build_version = int(re.search(r"\d+(?=[a-zA-Z])", build).group())
    if build_version < (25 if os_str == 'macOS' else 23):
        major_version = build_version - major_version_offset.get(os_str, 4)
    else:
        major_version = build_version + (1 if os_str == 'macOS' else 3)

    file_path = Path(f"osFiles/Simulators/{os_str}/{build_version}x - {major_version}.x/{build}.json")

    file_type = 'aar' if simulator.get('downloadMethod') == 'mobileAsset' else 'dmg'

    is_new_file = False

    if file_path.exists():
        new_item = json.load(file_path.open(encoding="utf-8"))
        if bool([x for x in new_item.get('sources', []) if x['type'] == file_type]): continue
    else:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        new_item = {
            'osStr': os_str,
            'version': simulator['name'].replace(f"{os_str} ", "").replace("Simulator Runtime", "Simulator").replace("Release Candidate", "RC"),
            'build': build,
            'uniqueBuild': f"{build}-sim",
            'released': datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d"),
            'deviceMap': [f"{os_str} Simulator"]
        }

        is_new_file = True
    if simulator.get('source'):
        new_item.setdefault('sources', []).append({
            'type': 'dmg',
            'deviceMap': [f"{os_str} Simulator"],
            'links': [
                {
                    'url': simulator['source'].replace('download.developer.apple.com', 'developer.apple.com/services-account/download?path=')
                }
            ],
            'size': simulator['fileSize']
        })
    elif simulator.get('downloadMethod') == 'mobileAsset':
        (pallas_response, pallas_date) = call_pallas(os_str, build)
        if pallas_response:
            new_item.setdefault('sources', []).extend(pallas_response)
        if pallas_date and is_new_file:
            new_item['released'] = pallas_date
    if 'beta' in new_item['version']:
        new_item['beta'] = True
    elif 'RC' in new_item['version']:
        new_item['rc'] = True
    if new_item.get('sources'):
        json.dump(sort_os_file(None, new_item), file_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
        update_links([file_path])

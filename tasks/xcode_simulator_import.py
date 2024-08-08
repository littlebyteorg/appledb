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

def call_pallas(os, build):
    request = {
        "ClientVersion": 2,
        "CertIssuanceDay": "2023-12-10",
        "AssetType": f"com.apple.MobileAsset.{simulator_pallas_mapping[os]}",
        "AssetAudience": "02d8e57e-dd1c-4090-aa50-b4ed2aef0062",
        "RequestedBuild": build
    }
    response = session.post("https://gdmf.apple.com/v2/assets", json=request, headers={"Content-Type": "application/json"}, verify=False)
    parsed_response = json.loads(base64.b64decode(response.text.split('.')[1] + '==', validate=False))
    asset = parsed_response.get('Assets', [])
    if asset:
        asset = asset[0]
        return [
            {
                'type': asset['__RelativePath'].split('.')[-1],
                'deviceMap': [f"{os} Simulator"],
                'links': [
                    {
                        'url': f"{asset['__BaseURL']}{asset['__RelativePath']}",
                        'decryptionKey': asset["ArchiveDecryptionKey"]
                    }
                ],
                'size': asset['_DownloadSize']
            }
        ]
    else:
        return []
    

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
    build_version = re.search(r"\d+(?=[a-zA-Z])", xcode_version['version']['build']).group()
    major_version = xcode_version['version']['number'].split(".")[0]
    if major_version == '3':
        if build_version == '10':
            major_version_range = "3.2.x"
        else:
            major_version_range = "3.0.x to 3.1.x"
    else:
        major_version_range = f"{major_version}.x"
    file_path = Path(f"osFiles/Software/Xcode/{build_version}x - {major_version_range}/{xcode_version['version']['build']}.json")
    os_map = [f'macOS {x}' for x in range(int(xcode_version['requires'].split(".")[0]), int(xcode_version['version']['number'].split('.')[0]))]
    if file_path.exists(): continue
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    formatted_sdks = []

    for sdk_key in xcode_version['sdks'].keys():
        for sdk_item in xcode_version['sdks'][sdk_key]:
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
        'released': dateutil.parser.parse(f"{xcode_version['date']['year']}-{xcode_version['date']['month']}-{xcode_version['date']['day']}").strftime("%Y-%m-%d"),
        'releaseNotes': xcode_version['links']['notes']['url'].replace('download.developer.apple.com', 'developer.apple.com/services-account/download?path='),
        'deviceMap': ['Xcode'],
        'osMap': os_map,
        'sdks': formatted_sdks,
        'sources': [
            {
                'type': xcode_version['links']['download']['url'].split('.')[-1],
                'deviceMap': ['Xcode'],
                'osMap': os_map,
                'links': [
                    {
                        'url': xcode_version['links']['download']['url'].replace('download.developer.apple.com', 'developer.apple.com/services-account/download?path='),
                    }
                ],
                'hashes': xcode_version['checksums']
            }
        ]
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

    json.dump(sort_os_file(None, new_item), file_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    update_links([file_path])

for simulator in simulator_response['downloadables']:
    simulator['name'] = simulator['name'].replace('xrOS', 'visionOS')
    os_str = simulator['name'].split(' ')[0]

    build = simulator['simulatorVersion']['buildUpdate']

    build_version = int(re.search(r"\d+(?=[a-zA-Z])", build).group())
    major_version = build_version - major_version_offset.get(os_str, 4)

    file_path = Path(f"osFiles/Simulators/{os_str}/{build_version}x - {major_version}.x/{build}.json")

    if file_path.exists(): continue
    file_path.parent.mkdir(parents=True, exist_ok=True)

    new_item = {
        'osStr': os_str,
        'version': simulator['name'].replace(f"{os_str} ", "").replace("Simulator Runtime", "Simulator").replace("Release Candidate", "RC"),
        'build': build,
        'uniqueBuild': f"{build}-sim",
        'released': datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d"),
        'deviceMap': [f"{os_str} Simulator"]
    }
    if simulator.get('source'):
        new_item['sources'] = [
            {
                'type': 'dmg',
                'deviceMap': [f"{os_str} Simulator"],
                'links': [
                    {
                        'url': simulator['source'].replace('download.developer.apple.com', 'developer.apple.com/services-account/download?path=')
                    }
                ],
                'size': simulator['fileSize']
            }
        ]
    elif simulator.get('downloadMethod') == 'mobileAsset':
        pallas_response = call_pallas(os_str, build)
        if pallas_response:
            new_item['sources'] = pallas_response
    if 'beta' in new_item['version']:
        new_item['beta'] = True
    elif 'rc' in new_item['version']:
        new_item['rc'] = True
    json.dump(sort_os_file(None, new_item), file_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    update_links([file_path])
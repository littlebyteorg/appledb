#!/usr/bin/env python3

import json
import plistlib
from pathlib import Path
import random

import packaging
import requests
from urllib.parse import unquote

from common_update_import import OS_MAP
from sort_os_files import device_sort

# other links:
# http://ax.phobos.apple.com.edgesuite.net/WebObjects/MZStore.woa/wa/com.apple.jingle.appserver.client.MZITunesClientCheck/version
# https://s.mzstatic.com/version
# https://itunes.com/version (redirect to mzstatic)
# All are the same

# TODO: Probably put import.txt in a folder, and put it in .gitignore

urls = [
    "https://itunes.apple.com/WebObjects/MZStore.woa/wa/com.apple.jingle.appserver.client.MZITunesClientCheck/version",
    "https://mesu.apple.com/assets/macos/com_apple_macOSIPSW/com_apple_macOSIPSW.xml",
    "https://mesu.apple.com/assets/bridgeos/com_apple_bridgeOSIPSW/com_apple_bridgeOSIPSW.xml",
    "https://mesu.apple.com/assets/visionos/com_apple_visionOSIPSW/com_apple_visionOSIPSW.xml"
]

def get_os_str(supported_device, version):
    for product_prefix, os_str in OS_MAP:
        if supported_device.startswith(product_prefix):
            if os_str == "iPadOS" and packaging.version.parse(version) < packaging.version.parse("13.0"):
                os_str = "iOS"
            return os_str
        elif product_prefix in supported_device:
            return os_str
    else:
        print(supported_device)

ipsw_list = {}
known_builds = [
    # iOS
    '16H81',   # 12.5.7
    '19H386',  # 15.8.3
    '20H350',  # 16.7.10
    '21H420',  # 17.7.5
    '22C161',  # 18.2.1
    '22D72',   # 18.3.1
    '22D8075', # 18.3.1 (iPhone 16e)
    '22K557',  # tvOS 18.3
    '22N900',  # visionOS 2.3.1
    '22P3051', # bridgeOS 9.3
    '24D70',   # macOS 15.3.1
]

for url in urls:
    response = requests.get(url + f"?cachebust{random.randint(100, 1000)}", timeout=30)
    response.raise_for_status()

    plist = plistlib.loads(response.content)

    for version_group in plist["MobileDeviceSoftwareVersionsByVersion"].values():
        for device, device_info in version_group["MobileDeviceSoftwareVersions"].items():
            if device in ["iPod1,1", "iPhone1,1", "iPhone1,2", "iPod2,1", "AppleTV2,1", "AppleTV3,1", "AppleTV3,2"]:
                # Special cases not worth dealing with
                continue
            for build, build_info in device_info.items():
                if build == "Unknown":
                    if "Universal" in build_info:
                        build_info = build_info["Universal"]
                if build_info.keys() == {"SameAs"}:
                    continue
                for variant in [i for i in build_info.values() if isinstance(i, dict)]:
                    if not variant["FirmwareURL"]:
                        continue
                    # Ignore super-old IPSWs
                    if not variant["FirmwareURL"].startswith("https"):
                        continue
                    if variant.get('BuildVersion') in known_builds:
                        continue
                    if any([x for x in known_builds if f'_{x}_' in variant["FirmwareURL"]]):
                        continue
                    os_str = get_os_str(device, variant['ProductVersion'])
                    if not ipsw_list.get(f"{os_str}-{variant['BuildVersion']}"):
                        ipsw_list[f"{os_str}-{variant['BuildVersion']}"] = {
                            "osStr": os_str,
                            "version": variant['ProductVersion'],
                            "build": variant['BuildVersion'],
                            "links": {}
                        }
                    if not ipsw_list[f"{os_str}-{variant['BuildVersion']}"]["links"].get(unquote(variant["FirmwareURL"])):
                        ipsw_list[f"{os_str}-{variant['BuildVersion']}"]["links"][unquote(variant["FirmwareURL"])] = {
                            "device": set(),
                            "url": unquote(variant["FirmwareURL"])
                        }
                    ipsw_list[f"{os_str}-{variant['BuildVersion']}"]["links"][unquote(variant["FirmwareURL"])]["device"].add(device)
                    if variant.get("DocumentationURL"):
                        ipsw_list[f"{os_str}-{variant['BuildVersion']}"].setdefault('ipd', {})
                        doc_filename = variant['DocumentationURL'].split('/')[-1]

                        if doc_filename.startswith('iPad'):
                            ipsw_list[f"{os_str}-{variant['BuildVersion']}"]['ipd']['iPad'] = variant['DocumentationURL']
                        elif doc_filename.startswith('iPod'):
                            ipsw_list[f"{os_str}-{variant['BuildVersion']}"]['ipd']['iPod'] = variant['DocumentationURL']
                        elif doc_filename.startswith('iPhone') or doc_filename.startswith('iOS'):
                            ipsw_list[f"{os_str}-{variant['BuildVersion']}"]['ipd']['iPhone'] = variant['DocumentationURL']
                        elif doc_filename.startswith('AppleTV'):
                            ipsw_list[f"{os_str}-{variant['BuildVersion']}"]['ipd']['AppleTV'] = variant['DocumentationURL']
                        elif doc_filename.startswith('HomePod'):
                            ipsw_list[f"{os_str}-{variant['BuildVersion']}"]['ipd']['AudioAccessory'] = variant['DocumentationURL']
                        else:
                            print("Unrecognized prefix")

if bool(ipsw_list):
    cleaned_list = []
    count = 0
    for item in ipsw_list.values():
        raw_links = list(item["links"].values())
        item["links"] = []
        for link in raw_links:
            link["device"] = ", ".join(sorted(list(link["device"]), key=device_sort))
            item["links"].append(link)
        count += len(item["links"])
        cleaned_list.append(item)
    print(f"{count} links added")
    [i.unlink() for i in Path.cwd().glob("import.*") if i.is_file()]
    json.dump(cleaned_list, Path("import.json").open("w", encoding="utf-8"), indent=4)

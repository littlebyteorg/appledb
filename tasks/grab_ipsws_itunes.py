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
    '19H390',  # 15.8.4
    '20H360',  # 16.7.11
    '21H423',  # 17.7.6
    '22C161',  # 18.2.1
    '22E240',  # 18.4
    '22L255',  # tvOS 18.4
    '22O238',  # visionOS 2.4
    '22P4248', # bridgeOS 9.3
    '24E248',  # macOS 15.3.2
]

filename_prefix_map = {
    'AppleTV': 'AppleTV',
    'HomePod': 'AudioAccessory',
    'iOS': 'iPhone',
    'iPad': 'iPad',
    'iPhone': 'iPhone',
    'iPod': 'iPod',
}

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
                        for prefix, ipd_property in filename_prefix_map.items():
                            if doc_filename.startswith(prefix):
                                ipsw_list[f"{os_str}-{variant['BuildVersion']}"]['ipd'][ipd_property] = variant['DocumentationURL']
                                break

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

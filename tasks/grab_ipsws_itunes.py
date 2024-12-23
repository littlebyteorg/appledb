#!/usr/bin/env python3

import sys
import plistlib
from pathlib import Path
import random

import requests
from urllib.parse import unquote

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

ipsws_set = set()

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
                    # Ignore iOS 12.5.7
                    if '_16H81_' in variant["FirmwareURL"]:
                        continue
                    # Ignore iOS 15.8.3
                    if '_19H386_' in variant["FirmwareURL"]:
                        continue
                    # Ignore iOS 16.7.10
                    if '_20H350_' in variant["FirmwareURL"]:
                        continue
                    ipsws_set.add(unquote(variant["FirmwareURL"]))

[i.unlink() for i in Path.cwd().glob("import.*") if i.is_file()]
Path("import.txt").write_text("\n".join(sorted(ipsws_set)), "utf-8", newline="\n")

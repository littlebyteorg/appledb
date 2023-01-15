import plistlib
from pathlib import Path
import requests

# other links:
# http://ax.phobos.apple.com.edgesuite.net/WebObjects/MZStore.woa/wa/com.apple.jingle.appserver.client.MZITunesClientCheck/version
# https://s.mzstatic.com/version
# All are the same

response = requests.get("https://itunes.apple.com/WebObjects/MZStore.woa/wa/com.apple.jingle.appserver.client.MZITunesClientCheck/version", timeout=30)
response.raise_for_status()

plist = plistlib.loads(response.content)

ipsws_set = set()

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
                if variant["FirmwareURL"].startswith("protected"):
                    continue
                if not variant["FirmwareURL"].startswith("http"):
                    continue
                ipsws_set.add(variant["FirmwareURL"])

Path("import.txt").write_text("\n".join(sorted(ipsws_set)), "utf-8", newline="\n")

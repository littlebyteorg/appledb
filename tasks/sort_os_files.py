#!/usr/bin/env python3

import copy
import json
import re
import sys
import argparse
from pathlib import Path
from typing import Optional

key_order = [
    "osStr",
    "version",
    "iosVersion",
    "safariVersion",
    "build",
    "restoreVersion",
    "uniqueBuild",
    "embeddedOSBuild",
    "bridgeOSBuild",
    "buildTrain",
    "released",
    "rc",
    "beta",
    "rsr",
    "internal",
    "hideFromLatestVersions",
    "preinstalled",
    "createDuplicateEntries",
    "notes",
    "releaseNotes",
    "securityNotes",
    "ipd",
    "appledbWebImage",
    "deviceMap",
    "basebandVersions",
    "osMap",
    "sdks",
    "sources",
]

sources_key_order = [
    "type",
    "prerequisiteBuild",
    "deviceMap",
    "boardMap",
    "osMap",
    "windowsUpdateDetails",
    "links",
    "hashes",
    "skipUpdateLinks",
    "size",
]

ipd_key_order = ["AudioAccessory", "AppleTV", "iPad", "iPhone", "iPhone_old", "iPod"]

links_key_order = ["url", "decryptionKey", "catalog", "preferred", "active", "auth"]

source_type_order = ["ipsw", "installassistant", "ota", "combo", "update", "kdk", "xip", "aar", "dmg", "pkg", "bin", "tar", "appx", "ipa", "xpi", "apk", "exe"]

os_prefix_order = ["Mac OS", "Mac OS X", "OS X", "macOS", "Windows"]


def device_sort(device):
    match = re.match(r"([a-zA-Z]+)(\d+),(\d+)", device)
    if not match or len(match.groups()) != 3:
        # iMac,1 is a valid identifier; check for this and, if present, treat missing section as 0
        match = re.match(r"([a-zA-Z]+),(\d+)", device)
        if not match or len(match.groups()) != 2:
            # This is probably not a device identifier, so just return it
            return "", 0, 0, device
        return match.groups()[0].lower(), 0, int(match.groups()[1]), device

    # The device at the end is for instances like "BeatsStudioBuds1,1", "BeatsStudioBuds1,1-tiger"
    # However, this will sort "MacBookPro15,1-2019" before "MacBookPro15,2-2018"
    return match.groups()[0].lower(), int(match.groups()[1]), int(match.groups()[2]), device


def os_sort(os):
    if os.startswith("Windows"):
        os_split = os.split(" ", 1)
        os_remains_mapping = {"2000": "5", "XP": "5.1", "XP SP2": "5.2", "XP SP3": "5.3", "Vista": "6"}
        os_split[1] = os_remains_mapping.get(os_split[1], os_split[1])
    else:
        os_split = os.rsplit(" ", 1)
        if os_split[1].startswith("10"):
            os_split[1] = ".".join([f"{int(x):02d}" for x in os_split[1].split(".")])

    return os_prefix_order.index(os_split[0]), float(os_split[1])


def sorted_dict_by_key(data, order):
    return dict(sorted(data.items(), key=lambda item: order.index(item[0])))


def sorted_dict_by_alphasort(data):
    return dict(sorted(data.items(), key=lambda item: item[0]))


def device_map_sort(device_map):
    return sorted(set(device_map), key=device_sort)


def board_map_sort(board_map):
    return sorted(set(board_map))


def os_map_sort(os_map):
    return sorted(set(os_map), key=os_sort)


def build_number_sort(build_number):
    match = re.match(r"(\d+)([A-Z])(\d+)([A-z])?", build_number)
    if not match:
        return 0, "A", 0, 0, "a"
    kernel_version = int(match.groups()[0])
    build_train_version = match.groups()[1]
    build_version = int(match.groups()[2])
    build_prefix = 0
    build_suffix = match.groups()[3] or ""
    if build_version > 1000:
        build_prefix = int(build_version / 1000)
        build_version = build_version % 1000
    return kernel_version, build_train_version, build_version, build_prefix, build_suffix


def sort_os_file(file_path: Optional[Path], raw_data=None):
    if not file_path and not raw_data:
        raise ValueError("Must provide either a file path or raw data")

    data = copy.deepcopy(raw_data) or json.load(file_path.open())  # type: ignore
    data = sorted_dict_by_key(data, key_order)
    if set(data.keys()) - set(key_order):
        raise ValueError(f"Unknown keys: {sorted(set(data.keys()) - set(key_order))}")

    for i, duplicate_entry in enumerate(data.get("createDuplicateEntries", [])):
        data["createDuplicateEntries"][i] = sort_os_file(None, duplicate_entry)
    data.get("createDuplicateEntries", []).sort(key=lambda x: x["released"])

    if isinstance(data.get("releaseNotes"), dict):
        data["releaseNotes"] = sorted_dict_by_key(data["releaseNotes"], links_key_order)
    if isinstance(data.get("securityNotes"), dict):
        data["securityNotes"] = sorted_dict_by_key(data["securityNotes"], links_key_order)

    if "deviceMap" in data:
        data["deviceMap"] = device_map_sort(data["deviceMap"])

    if "osMap" in data:
        data["osMap"] = os_map_sort(data["osMap"])

    if "basebandVersions" in data:
        data["basebandVersions"] = sorted_dict_by_key(data["basebandVersions"], data["deviceMap"])

    if "ipd" in data:
        for key in data["ipd"].keys():
            if isinstance(data["ipd"][key], dict):
                data["ipd"][key] = sorted_dict_by_key(data["ipd"][key], links_key_order)
        data["ipd"] = sorted_dict_by_key(data["ipd"], ipd_key_order)

    for i, sdk in enumerate(data.get("sdks", [])):
        data["sdks"][i] = sorted_dict_by_key(sdk, key_order)

    data.get("sdks", []).sort(key=lambda sdk: f"{sdk['osStr']} {sdk['version']}")

    for i, source in enumerate(data.get("sources", [])):
        data["sources"][i] = sorted_dict_by_key(source, sources_key_order)
        if set(data["sources"][i].keys()) - set(sources_key_order):
            raise ValueError(f"Unknown keys: {sorted(set(data['sources'][i].keys()) - set(sources_key_order))}")

        data["sources"][i]["deviceMap"] = device_map_sort(source["deviceMap"])
        if source.get("boardMap"):
            data["sources"][i]["boardMap"] = board_map_sort(source["boardMap"])
        if source.get("osMap"):
            data["sources"][i]["osMap"] = os_map_sort(source["osMap"])
        if "hashes" in source:
            data["sources"][i]["hashes"] = sorted_dict_by_alphasort(source["hashes"])
        for j, link in enumerate(source.get("links", [])):
            data["sources"][i]["links"][j] = sorted_dict_by_key(link, links_key_order)

            if set(data["sources"][i]["links"][j].keys()) - set(links_key_order):
                raise ValueError(f"Unknown keys: {sorted(set(data['sources'][i]['links'][j].keys()) - set(links_key_order))}")
        data["sources"][i]["links"].sort(key=lambda x: (0 if x.get('preferred', True) else 1, x.get("catalog", "")))
        if isinstance(source.get("prerequisiteBuild"), list):
            data["sources"][i]["prerequisiteBuild"].sort(key=build_number_sort)

    def source_sort(source):
        prerequisite_order = None
        if "prerequisiteBuild" not in source:
            # Goes at the top
            prerequisite_order = ""
        elif isinstance(source["prerequisiteBuild"], str):
            prerequisite_order = source["prerequisiteBuild"]
        else:
            # This is a list which was already sorted previously
            prerequisite_order = source["prerequisiteBuild"][0]

        if "boardMap" not in source:
            board_order = ""
        else:
            # This is a list which was already sorted previously
            board_order = source["boardMap"][0]

        if source.get("osMap"):
            sorted_os_item = os_sort(source["osMap"][0])
        else:
            sorted_os_item = (-1, 0)

        if 'mac' in data.get('osStr', '').lower():
            return (
                source_type_order.index(source["type"]),
                build_number_sort(prerequisite_order),
                device_sort(source["deviceMap"][0]),
            )
        return (
            device_sort(source["deviceMap"][0]),
            source_type_order.index(source["type"]),
            build_number_sort(prerequisite_order),
            sorted_os_item,
            board_order,
        )

    data.get("sources", []).sort(key=source_sort)

    if not raw_data:
        json.dump(data, file_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)  # type: ignore
    else:
        return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--files", nargs="+")
    args = parser.parse_args()
    if args.files:
        for file in args.files:
            try:
                sort_os_file(Path(file))
            except Exception:
                print(f"Error while processing {file}")
                raise
    else:
        for file in Path("osFiles").rglob("*.json"):
            try:
                sort_os_file(file)
            except Exception:
                print(f"Error while processing {file}")
                raise

#!/usr/bin/env python3

import copy
import json
import re
from pathlib import Path
from typing import Optional

key_order = [
    "osStr",
    "version",
    "macosVersion",
    "iosVersion",
    "sortVersion",
    "build",
    "uniqueBuild",
    "released",
    "sdk",
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
    "iPhoneMap",
    "osMap",
    "xcodeMap",
    "sources",
]

sources_key_order = ["type", "deviceMap", "osMap", "links", "hashes", "size"]

links_key_order = ["url", "catalog", "preferred", "active"]

source_type_order = ["ipsw", "installassistant", "ota", "xip", "dmg", "pkg", "bin", "tar", "exe"]


def device_sort(device):
    match = re.match(r"([a-zA-Z]+)(\d+),(\d+)", device)
    if not match or len(match.groups()) != 3:
        # iMac,1 is a valid identifier; check for this and, if present, treat missing section as 0
        match = re.match(r"([a-zA-Z]+),(\d+)", device)
        if not match or len(match.groups()) != 2:
            # This is probably not a device identifier, so just return it
            return device
        return match.groups()[0], 0, int(match.groups()[1]), device

    # The device at the end is for instances like "BeatsStudioBuds1,1", "BeatsStudioBuds1,1-tiger"
    # However, this will sort "MacBookPro15,1-2019" before "MacBookPro15,2-2018"
    return match.groups()[0], int(match.groups()[1]), int(match.groups()[2]), device


def device_map_sort(device_map):
    return sorted(set(device_map), key=device_sort)


def sort_os_file(file_path: Optional[Path], raw_data=None):
    if not file_path and not raw_data:
        raise ValueError("Must provide either a file path or raw data")

    data = copy.deepcopy(raw_data) or json.load(file_path.open())  # type: ignore
    data = dict(sorted(data.items(), key=lambda item: key_order.index(item[0]) if item[0] in key_order else len(key_order)))
    if set(data.keys()) - set(key_order):
        raise ValueError(f"Unknown keys: {sorted(set(data.keys()) - set(key_order))}")

    for i, duplicate_entry in enumerate(data.get("createDuplicateEntries", [])):
        data["createDuplicateEntries"][i] = sort_os_file(None, duplicate_entry)
    data.get("createDuplicateEntries", []).sort(key=lambda x: x["released"])

    if "deviceMap" in data:
        data["deviceMap"] = device_map_sort(data["deviceMap"])

    for i, xcode in enumerate(data.get("xcodeMap", [])):
        data["xcodeMap"][i] = dict(
            sorted(
                xcode.items(),
                key=lambda item: key_order.index(item[0]) if item[0] in key_order else len(key_order),
            )
        )

    data.get("xcodeMap", []).sort(key=lambda xcode: xcode['released'])

    for i, source in enumerate(data.get("sources", [])):
        data["sources"][i] = dict(
            sorted(
                source.items(),
                key=lambda item: sources_key_order.index(item[0]) if item[0] in sources_key_order else len(sources_key_order),
            )
        )
        if set(data["sources"][i].keys()) - set(sources_key_order):
            raise ValueError(f"Unknown keys: {sorted(set(data['sources'][i].keys()) - set(sources_key_order))}")

        data["sources"][i]["deviceMap"] = device_map_sort(source["deviceMap"])
        for j, link in enumerate(source.get("links", [])):
            data["sources"][i]["links"][j] = dict(
                sorted(
                    link.items(), key=lambda item: links_key_order.index(item[0]) if item[0] in links_key_order else len(links_key_order)
                )
            )
            if set(data["sources"][i]["links"][j].keys()) - set(links_key_order):
                raise ValueError(f"Unknown keys: {sorted(set(data['sources'][i]['links'][j].keys()) - set(links_key_order))}")

    data.get("sources", []).sort(key=lambda source: (device_sort(source["deviceMap"][0]), source_type_order.index(source["type"])))

    if not raw_data:
        json.dump(data, file_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)  # type: ignore
    else:
        return data


if __name__ == "__main__":
    for file in Path("osFiles").rglob("*.json"):
        try:
            sort_os_file(file)
        except Exception:
            print(f"Error while processing {file}")
            raise

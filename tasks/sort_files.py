#!/usr/bin/env python3

import copy
import json
import re
from pathlib import Path
from typing import Optional

key_order = [
    "osStr",
    "version",
    "iosVersion",
    "sortVersion",
    "build",
    "uniqueBuild",
    "released",
    "rc",
    "beta",
    "hideFromLatestVersions",
    "preinstalled",
    "createDuplicateEntries",
    "notes",
    "releaseNotes",
    "securityNotes",
    "deviceMap",
    "sources",
]

sources_key_order = ["type", "deviceMap", "links", "hashes", "size"]

links_key_order = ["url", "preferred", "active"]


def device_sort(device):
    match = re.match(r"([a-zA-Z]+)(\d+),(\d+)", device)
    if not match or len(match.groups()) != 3:
        # This is probably not a device identifier, so just return it
        return device

    # The device at the end is for instances like "BeatsStudioBuds1,1", "BeatsStudioBuds1,1-tiger"
    # However, this will sort "MacBookPro15,1-2019" before "MacBookPro15,2-2018"
    return match.groups()[0], int(match.groups()[1]), int(match.groups()[2]), device


def device_map_sort(device_map):
    return sorted(set(device_map), key=device_sort)


def sort_file(file_path: Optional[Path], raw_data=None):
    if not file_path and not raw_data:
        raise ValueError("Must provide either a file path or raw data")

    data = copy.deepcopy(raw_data) or json.load(file_path.open())  # type: ignore
    data = dict(sorted(data.items(), key=lambda item: key_order.index(item[0]) if item[0] in key_order else len(key_order)))

    for i, duplicate_entry in enumerate(data.get("createDuplicateEntries", [])):
        data["createDuplicateEntries"][i] = sort_file(None, duplicate_entry)
    data.get("createDuplicateEntries", []).sort(key=lambda x: x["released"])

    if "deviceMap" in data:
        data["deviceMap"] = device_map_sort(data["deviceMap"])

    for i, source in enumerate(data.get("sources", [])):
        data["sources"][i] = dict(sorted(source.items(), key=lambda item: sources_key_order.index(item[0]) if item[0] in sources_key_order else len(sources_key_order)))
        data["sources"][i]["deviceMap"] = device_map_sort(source["deviceMap"])
        for j, link in enumerate(source.get("links", [])):
            data["sources"][i]["links"][j] = dict(sorted(link.items(), key=lambda item: links_key_order.index(item[0]) if item[0] in links_key_order else len(links_key_order)))
    data.get("sources", []).sort(key=lambda source: device_sort(source["deviceMap"][0]))

    if not raw_data:
        json.dump(data, file_path.open("w", newline="\n"), indent=4)  # type: ignore
    else:
        return data


if __name__ == "__main__":
    for file in Path("osFiles").rglob("*.json"):
        sort_file(file)

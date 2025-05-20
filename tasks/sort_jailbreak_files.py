#!/usr/bin/env python3

import copy
import json
import argparse
from pathlib import Path
from typing import Optional

from sort_files_common import build_number_sort, device_map_sort, sorted_dict_by_key


key_order = [
    "name",
    "hideFromGuide",
    "alias",
    "priority",
    "info",
    "compatibility"
]

info_key_order = ["website", "wiki", "guide", "latestVer", "color", "icon", "jailbreaksmeapp", "notes", "type", "firmwares", "soc"]
website_key_order = ["name", "url", "external"]
guide_key_order = ["text", "name", "sidebarName", "url", "pkgman", "devices", "firmwares", "updateLink", "sidebarChildren"]
guide_link_key_order = ["text", "link"]


def sort_jailbreak_file(file_path: Optional[Path], raw_data=None):
    if not file_path and not raw_data:
        raise ValueError("Must provide either a file path or raw data")

    data = copy.deepcopy(raw_data) or json.load(file_path.open())  # type: ignore
    data = sorted_dict_by_key(data, key_order)
    if set(data.keys()) - set(key_order):
        raise ValueError(f"Unknown keys: {sorted(set(data.keys()) - set(key_order))}")
    
    # handle info
    if "info" in data:
        if "website" in data["info"]:
            data["info"]["website"] = sorted_dict_by_key(data["info"]["website"], website_key_order)
        if "wiki" in data["info"]:
            data["info"]["wiki"] = sorted_dict_by_key(data["info"]["wiki"], website_key_order)
        if "guide" in data["info"]:
            for i, guide in enumerate(data["info"]["guide"]):
                data["info"]["guide"][i] = sorted_dict_by_key(guide, guide_key_order)
                if "updateLink" in data["info"]["guide"][i]:
                    for j, update_link in enumerate(data["info"]["guide"][i]["updateLink"]):
                        data["info"]["guide"][i]["updateLink"][j] = sorted_dict_by_key(update_link, guide_link_key_order)
        if "devices" in data["info"]:
            data["info"]["devices"] = device_map_sort(data["info"]["devices"])
        if "firmwares" in data["info"]:
            data["info"]["firmwares"].sort(key=build_number_sort)
        data["info"] = sorted_dict_by_key(data["info"], info_key_order)

    # handle compatibility
    for i, compatibility in enumerate(data["compatibility"]):
        compatibility["devices"] = device_map_sort(compatibility["devices"])
        compatibility["firmwares"].sort(key=build_number_sort)
        data["compatibility"][i] = compatibility

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
                sort_jailbreak_file(Path(file))
            except Exception:
                print(f"Error while processing {file}")
                raise
    else:
        for file in Path("jailbreakFiles").rglob("*.json*"):
            try:
                sort_jailbreak_file(file)
            except Exception:
                print(f"Error while processing {file}")
                raise

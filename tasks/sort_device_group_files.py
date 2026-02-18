#!/usr/bin/env python3

import copy
import json
import argparse
from pathlib import Path
from typing import Optional
from sort_files_common import sorted_dict_by_key, validate_file_name

key_order = [
    "name",
    "key",
    "type",
    "order",
    "devices",
    "imageKey",
    "subgroups"
]


def sort_device_group_file(file_path: Optional[Path], raw_data=None):
    if not file_path and not raw_data:
        raise ValueError("Must provide either a file path or raw data")
    
    data = copy.deepcopy(raw_data) or json.load(file_path.open(encoding="utf-8"))  # type: ignore
    data = sorted_dict_by_key(data, key_order)
    if set(data.keys()) - set(key_order):
        raise ValueError(f"Unknown keys: {sorted(set(data.keys()) - set(key_order))}")

    if file_path:
        validate_file_name(file_path.stem, [data.get("name"), data.get("key")])

    for i, subgroup in enumerate(data.get("subgroups", [])):
        data["subgroups"][i] = sort_device_group_file(None, subgroup)
    data.get("subgroups", []).sort(key=lambda x: x["order"])

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
                sort_device_group_file(Path(file))
            except Exception:
                print(f"Error while processing {file}")
                raise
    else:
        for file in Path("deviceGroupFiles").rglob("*.json"):
            try:
                sort_device_group_file(file)
            except Exception:
                print(f"Error while processing {file}")
                raise
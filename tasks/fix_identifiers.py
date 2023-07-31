import json
from pathlib import Path

from sort_os_files import sort_os_file

VARIANTS = {}

for device in Path("deviceFiles").rglob("*.json"):
    device_data = json.load(device.open(encoding="utf-8"))
    name = device_data["name"]
    identifiers = device_data.get("identifier", [])
    if isinstance(identifiers, str):
        identifiers = [identifiers]

    key = device_data.get("key", None)
    # Key is either the first identifier or the name
    if not key:
        key = identifiers[0] if identifiers else name

    if not identifiers:
        # If there are no identifiers, then we either go by the key or the name
        # The key is preferred to avoid incidents where there are no identifiers, but the name is not unique
        # In this case, the devices are not equal and should not be merged
        identifiers = [key]

    for identifier in identifiers:
        VARIANTS.setdefault(identifier, set()).add(key)


def augment_with_keys(identifiers):
    new_identifiers = []
    for identifier in identifiers:
        new_identifiers.extend(VARIANTS.get(identifier, [identifier]))
    return new_identifiers


if __name__ == "__main__":
    for file in Path("osFiles").rglob("*.json"):
        try:
            data = json.load(file.open(encoding="utf-8"))
            for info in [data] + data.get("createDuplicateEntries", []):
                if "deviceMap" in info:
                    info["deviceMap"] = augment_with_keys(info["deviceMap"])
                for source in info.get("sources", []):
                    if "deviceMap" in source:
                        source["deviceMap"] = augment_with_keys(source["deviceMap"])
                        info.setdefault("deviceMap", []).extend(source["deviceMap"])
            json.dump(data, file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
            sort_os_file(file)
        except Exception:
            print(f"Error while processing {file}")
            raise

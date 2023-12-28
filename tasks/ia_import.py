#!/usr/bin/env python3

import argparse
import datetime
import hashlib
import json
import plistlib
import re
import zoneinfo
from pathlib import Path

import requests
from link_info import source_has_link
from sort_os_files import sort_os_file
from update_links import update_links

# TODO: createAdditionalEntries support (would only work with JSON tho)

FULL_SELF_DRIVING = False
# Use local files if found
USE_LOCAL_IF_FOUND = True
LOCAL_IA_PATH = Path("ias")

SESSION = requests.Session()

VARIANTS = {}
BOARD_IDS = {}


for device in Path("deviceFiles").rglob("*.json"):
    device_data = json.load(device.open(encoding="utf-8"))
    name = device_data["name"]
    identifiers = device_data.get("identifier", [])
    if isinstance(identifiers, str):
        identifiers = [identifiers]
    if not identifiers:
        identifiers = [name]
    key = device_data.get("key", identifiers[0] if identifiers else name)

    for identifier in identifiers:
        VARIANTS.setdefault(identifier, set()).add(key)

        if device_data.get('board'):
            board = device_data['board'][0] if isinstance(device_data['board'], list) else device_data['board']
            BOARD_IDS.setdefault(board.upper() if device_data.get("type") == "iBridge" else board, set()).add(key)


def augment_with_keys(identifiers):
    new_identifiers = []
    for identifier in identifiers:
        new_identifiers.extend(VARIANTS.get(identifier, [identifier]))
    return new_identifiers


def get_board_mappings(devices):
    mac_identifiers = []
    bridge_identifiers = []
    for device in devices:
        device_mappings = list(BOARD_IDS.get(device, {}))
        if not device_mappings:
            continue
        if device_mappings[0].startswith("iBridge"):
            bridge_identifiers.extend(device_mappings)
        else:
            mac_identifiers.extend(device_mappings)
    return mac_identifiers, bridge_identifiers


def create_file(os_str, build, recommended_version=None, version=None, released=None, beta=None, rc=None, rsr=False):
    assert version or recommended_version, "Must have either version or recommended_version"

    kern_version = re.search(r"\d+(?=[a-zA-Z])", build)
    assert kern_version
    kern_version = kern_version.group()

    major_version = ".".join((version or recommended_version).split(".")[:1]) + ".x"  # type: ignore

    version_dir = f"{kern_version}x - {major_version}"

    db_file = Path(f"osFiles/{os_str}/{version_dir}/{build}.json")

    if db_file.exists():
        print("\tFile already exists, not replacing")
    else:
        print(f"\tNo file found for build {build}, creating new file")
        if not db_file.parent.exists() and not db_file.parent.parent.exists():
            raise RuntimeError(f"Couldn't find a subdirectory for build {build} (major {version_dir})")
        elif not db_file.parent.exists():
            print(f"Warning: no subdirectory found for major {version_dir}, creating new one")
            db_file.parent.mkdir()

        db_file.touch()
        print(f"\tCurrent version is: {version or recommended_version}")

        if version:
            friendly_version = version
        elif FULL_SELF_DRIVING:
            friendly_version = f"{recommended_version} (FIXME)"
        else:
            friendly_version = input("\tEnter version (include beta/RC), or press Enter to keep current: ").strip()
            if not friendly_version:
                friendly_version = version or recommended_version

        json_dict = {"osStr": os_str, "version": friendly_version, "build": build}

        json.dump(
            json_dict,
            db_file.open("w", encoding="utf-8", newline="\n"),
            indent=4,
            ensure_ascii=False,
        )

    db_data = json.load(db_file.open(encoding="utf-8"))

    if not db_data.get("released"):
        print("\tMissing release date")
        if released:
            print(f"\tRelease date is: {released}")
            db_data["released"] = released
        elif FULL_SELF_DRIVING:
            print("\tUsing placeholder for date")
            db_data["released"] = "YYYY-MM-DD"  # Should fail CI
            # db_data["released"] = datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
        else:
            use_today = bool(input("\tUse today's date (today in Cupertino time)? [y/n]: ").strip().lower() == "y")
            if use_today:
                db_data["released"] = datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
            else:
                db_data["released"] = input("\tEnter release date (YYYY-MM-DD): ").strip()

    if "beta" not in db_data and (beta or "beta" in db_data["version"].lower()):
        db_data["beta"] = True

    if "rc" not in db_data and (rc or "rc" in db_data["version"].lower()):
        db_data["rc"] = True

    if "internal" in db_data:
        del db_data["internal"]

    json.dump(sort_os_file(None, db_data), db_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)

    return db_file

def import_ia(
    ia_url, build=None, recommended_version=None, version=None, released=None, beta=None, rc=None, use_network=True
):
    local_path = LOCAL_IA_PATH / Path(Path(ia_url).name)
    local_available = USE_LOCAL_IF_FOUND and local_path.exists()
    info_plist = None
    catalog_name = ''

    if 'pkg;' in ia_url:
        url_split = ia_url.split(';', 1)
        ia_url = url_split[0]
        catalog_name = url_split[1]

    info_plist_url = ia_url.rsplit("/", 1)[0] + "/Info.plist"
    info_plist_response = SESSION.get(info_plist_url, headers={})

    if not local_available:
        try:
            info_plist_response.raise_for_status()
        except requests.exceptions.HTTPError:
            print(f"\tInfo.plist not found at {info_plist_url}")
        else:
            info_plist = plistlib.loads(info_plist_response.content).get('MobileAssetProperties')

    bridge_version = None

    if info_plist.get('BridgeVersionInfo'):
        bridge_version = info_plist['BridgeVersionInfo']['BridgeVersion'].split('.')
        bridge_version = f"{(int(bridge_version[0]) - 13)}.{bridge_version[2].zfill(4)[0]}"

    # Get the build, version, and supported devices
    build = build or info_plist["Build"]
    # TODO: Check MarketingVersion in Restore.plist in order to support older tvOS IPSWs
    # Maybe hardcode 4.0 to 4.3, 4.4 to 5.0.2, etc
    # Check by substring first?
    recommended_version = recommended_version or info_plist["OSVersion"]
    supported_devices, bridge_devices = get_board_mappings(info_plist['SupportedDeviceModels'])

    supported_devices = [i for i in supported_devices if i not in ["iProd99,1", "iFPGA", "iSim1,1"]]

    db_file = create_file("macOS", build, recommended_version=recommended_version, version=version, released=released, beta=beta, rc=rc)
    db_data = json.load(db_file.open(encoding="utf-8"))

    db_data.setdefault("deviceMap", []).extend(augment_with_keys(supported_devices))

    os_image_version_map = {
        '11': 'Big Sur',
        '12': 'Monterey',
        '13': 'Ventura',
        '14': 'Sonoma'
    }
    os_version_prefix = db_data["version"].split(".", 1)[0]
    if os_image_version_map.get(os_version_prefix):
        db_data['appledbWebImage'] = {
            'id': os_image_version_map[os_version_prefix],
            'align': 'left'
        }

    found_source = False
    for source in db_data.setdefault("sources", []):
        if source['type'] == "installassistant":
            found_source = True
            source.setdefault("deviceMap", []).extend(augment_with_keys(supported_devices))
            if source_has_link(source, ia_url):
                print("\tURL already exists in sources")
            else:
                new_link = {"url": ia_url, "active": True}
                if catalog_name:
                    new_link['catalog'] = catalog_name
                source['links'].append(new_link)

    if not found_source:
        file_data = SESSION.get(ia_url).content
        sha1 = hashlib.sha1()
        sha1.update(file_data)
        print("\tAdding new source")
        source = {"deviceMap": augment_with_keys(supported_devices), "type": "installassistant", "links": [{"url": ia_url, "active": True}], "hashes": {"sha1": sha1.hexdigest()}}

        if catalog_name:
            source['links'][0]['catalog'] = catalog_name

        db_data["sources"].append(source)

    json.dump(sort_os_file(None, db_data), db_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    if use_network:
        print("\tRunning update links on file")
        update_links([db_file])
    else:
        # Save the network access for the end, that way we can run it once per file instead of once per IA
        # and we can use threads to speed it up
        update_links([db_file], False)
    print(f"\tSanity check the file{', run update_links.py, ' if not use_network else ' '}and then commit it\n")

    if bridge_version and bridge_devices:
        macos_version = db_data["version"]
        bridge_version = macos_version.replace(macos_version.split(" ")[0], bridge_version)
        print(bridge_version)
        bridge_file = create_file("bridgeOS", info_plist['BridgeVersionInfo']['BridgeProductBuildVersion'], recommended_version=bridge_version, released=db_data["released"])
        bridge_data = json.load(bridge_file.open(encoding="utf-8"))
        bridge_data["deviceMap"] = bridge_devices
        json.dump(sort_os_file(None, bridge_data), bridge_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    return db_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bulk-mode', action='store_true')
    parser.add_argument('-s', '--full-self-driving', action='store_true')
    args = parser.parse_args()

    if args.full_self_driving:
        FULL_SELF_DRIVING = True

    bulk_mode = args.bulk_mode or input("Bulk mode - read data from import-ia.json/import-ia.txt? [y/n]: ").strip().lower() == "y"

    if FULL_SELF_DRIVING:
        print("Full self-driving mode enabled. Make sure to verify data before committing.")
    if bulk_mode:
        files_processed = set()

        if not FULL_SELF_DRIVING:
            print("Warning: you still need to be present, as this script will ask for input!")

        if Path("import-ia.json").exists():
            print("Reading versions from import-ia.json")
            versions = json.load(Path("import-ia.json").open(encoding="utf-8"))

            for version in versions:
                print(f"Importing {version['osStr']} {version['version']}")
                if "links" not in version:
                    files_processed.add(
                        create_file(version["osStr"], version["build"], version=version["version"], released=version["released"])
                    )
                else:
                    for link in version["links"]:
                        files_processed.add(
                            import_ia(link["url"], version=version["version"], released=version["released"], use_network=False)
                        )

        elif Path("import-ia.txt").exists():
            print("Reading URLs from import-ia.txt")

            urls = [i.strip() for i in Path("import-ia.txt").read_text(encoding="utf-8").splitlines() if i.strip()]
            for url in urls:
                print(f"Importing {url}")
                files_processed.add(import_ia(url, use_network=False))
        else:
            raise RuntimeError("No import file found")

        print("Checking processed files for alive/hashes...")
        update_links(files_processed)
    else:
        try:
            while True:
                url = input("Enter IA URL (with semicolon before catalog if applicable): ").strip()
                if not url:
                    break
                import_ia(url)
        except KeyboardInterrupt:
            pass

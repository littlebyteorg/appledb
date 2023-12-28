#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import plistlib
import re
import zipfile
import zoneinfo
from pathlib import Path

import packaging.version
import remotezip
import requests
import time
from link_info import source_has_link
from sort_os_files import sort_os_file
from update_links import update_links

# TODO: createAdditionalEntries support (would only work with JSON tho)

FULL_SELF_DRIVING = False
# Use local files if found
USE_LOCAL_IF_FOUND = True
LOCAL_OTA_PATH = Path("otas")

OS_MAP = [
    ("iPod", "iOS"),
    ("iPhone", "iOS"),
    ("iPad", "iPadOS"),
    ("AudioAccessory", "audioOS"),
    ("AppleTV", "tvOS"),
    ("MacBook", "macOS"),
    ("Mac", "macOS"),
    ("Watch", "watchOS"),
    ("iBridge", "bridgeOS"),
    ("RealityDevice", "visionOS"),
    ("AppleDisplay", "Studio Display Firmware"),
]

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
    identifiers = []
    bridge_identifiers = []
    for device in devices:
        device_mappings = list(BOARD_IDS.get(device, {}))
        if not device_mappings:
            continue
        if device_mappings[0].startswith("iBridge"):
            bridge_identifiers.extend(device_mappings)
        else:
            identifiers.extend(device_mappings)
    return identifiers, bridge_identifiers


def create_file(os_str, build, recommended_version=None, version=None, released=None, beta=None, rc=None, rsr=False):
    assert version or recommended_version, "Must have either version or recommended_version"

    # watchOS 1 override
    if os_str == "watchOS" and build.startswith("12"):
        recommended_version = recommended_version.replace("8.2", "1.0")

    kern_version = re.search(r"\d+(?=[a-zA-Z])", build)
    assert kern_version
    kern_version = kern_version.group()

    ios_version = None
    os_str_override = os_str

    major_version = ".".join((version or recommended_version).split(".")[:1]) + ".x"  # type: ignore
    if os_str == "tvOS" and int(kern_version) <= 12:
        os_str_override = "Apple TV Software"
        ios_version = recommended_version
        version_dir = [x.path.split("/")[-1] for x in os.scandir(f"osFiles/{os_str}") if x.path.startswith(f"osFiles/{os_str}/{kern_version}x")][0]
    else:
        version_dir = f"{kern_version}x - {major_version}"

    if os_str == "audioOS" and packaging.version.parse(recommended_version.split(" ")[0]) >= packaging.version.parse("13.4"):
        os_str_override = 'HomePod Software'

    file_path = f"osFiles/{os_str}/{version_dir}/{build}.json"
    if rsr:
        file_path = f"osFiles/Rapid Security Responses/{os_str}/{version_dir}/{build}.json"

    db_file = Path(file_path)

    if db_file.exists():
        print("\tFile already exists, not replacing")
    else:
        print(f"\tNo file found for build {build}, creating new file")
        if not db_file.parent.exists() and not db_file.parent.parent.exists():
            raise RuntimeError(f"Couldn't find a subdirectory in {os_str} for build {build} (major {version_dir})")
        elif not db_file.parent.exists():
            print(f"Warning: no subdirectory found for major {version_dir} in {os_str}, creating new one")
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

        json_dict = {"osStr": os_str_override, "version": friendly_version, "build": build}
        if os_str_override == "Apple TV Software":
            json_dict["iosVersion"] = ios_version

        if rsr:
            json_dict["rsr"] = True

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

def import_ota(
    ota_url, os_str=None, build=None, recommended_version=None, version=None, released=None, beta=None, rc=None, use_network=True, prerequisite_builds=None, device_map=None, rsr=False
):
    local_path = LOCAL_OTA_PATH / Path(Path(ota_url).name)
    local_available = USE_LOCAL_IF_FOUND and local_path.exists()
    ota = None
    info_plist = None

    counter = 0
    while True:
        try:
            ota = zipfile.ZipFile(local_path) if local_available else remotezip.RemoteZip(ota_url, initial_buffer_size=256*1024, session=SESSION, timeout=60)
            print(f"\tGetting Info.plist {'from local file' if local_available else 'via remotezip'}")

            info_plist = plistlib.loads(ota.read("Info.plist"))

            if info_plist.get('MobileAssetProperties'):
                info_plist = info_plist['MobileAssetProperties']

            if info_plist.get('SplatOnly'):
                rsr = True
            break
        except:
            if not build:
                time.sleep(1+counter)
                counter += 1
                if counter > 5:
                    raise
            info_plist = {}
    bridge_version = None

    if info_plist.get('BridgeVersionInfo'):
        bridge_version = info_plist['BridgeVersionInfo']['BridgeVersion'].split('.')
        bridge_version = f"{(int(bridge_version[0]) - 13)}.{bridge_version[2].zfill(4)[0]}"

    if ota:
        ota.close()

    # Get the build, version, and supported devices
    if (ota_url.endswith(".ipsw")):
        build = build or info_plist["TargetUpdate"]
        recommended_version = recommended_version or info_plist["ProductVersion"]
        supported_devices = supported_devices or [info_plist["ProductType"]]
        bridge_devices = []
        prerequisite_builds = prerequisite_builds or info_plist.get('BaseUpdate')
    else:
        build = build or info_plist["Build"]
        # TODO: Check MarketingVersion in Restore.plist in order to support older tvOS IPSWs
        # Maybe hardcode 4.0 to 4.3, 4.4 to 5.0.2, etc
        # Check by substring first?
        recommended_version = recommended_version or info_plist["OSVersion"].removeprefix("9.9.")
        if rsr:
            recommended_version = recommended_version + (f" {info_plist['ProductVersionExtra']}" if info_plist.get('ProductVersionExtra') else '')
        # Devices supported specifically in this source
        if device_map:
            supported_devices = device_map
            bridge_devices = []
        elif info_plist.get('SupportedDevices'):
            supported_devices = info_plist['SupportedDevices']
            bridge_devices = []
        else:
            supported_devices, bridge_devices = get_board_mappings(info_plist['SupportedDeviceModels'])

        prerequisite_builds = prerequisite_builds or info_plist.get('PrerequisiteBuild', '').split(';')
        if len(prerequisite_builds) == 1:
            prerequisite_builds = prerequisite_builds[0]
        elif len(prerequisite_builds) > 1:
            prerequisite_builds.sort()

        supported_devices = [i for i in supported_devices if i not in ["iProd99,1"]]

    if not os_str:
        for product_prefix, os_str in OS_MAP:
            if any(prod.startswith(product_prefix) for prod in supported_devices):
                if os_str == "iPadOS" and packaging.version.parse(recommended_version.split(" ")[0]) < packaging.version.parse("13.0"):
                    os_str = "iOS"
                print(f"\t{os_str} {recommended_version} ({build})")
                print(f"\tPrerequisite: {prerequisite_builds}")
                print(f"\tDevice Support: {supported_devices}")
                break
        else:
            if FULL_SELF_DRIVING:
                raise RuntimeError(f"Couldn't match product types to any known OS: {supported_devices}")
            else:
                print(f"\tCouldn't match product types to any known OS: {supported_devices}")
                os_str = input("\tEnter OS name: ").strip()

    db_file = create_file(os_str, build, recommended_version=recommended_version, version=version, released=released, beta=beta, rc=rc, rsr=rsr)
    db_data = json.load(db_file.open(encoding="utf-8"))

    db_data.setdefault("deviceMap", []).extend(augment_with_keys(supported_devices))

    if os_str in ('audioOS', 'iOS', 'iPadOS', 'tvOS', 'watchOS'):
        db_data['appledbWebImage'] = {
            'id': os_str.lower() + db_data["version"].split(".", 1)[0],
            'align': 'left'
        }
        if os_str == "iPadOS" and packaging.version.parse(recommended_version.split(" ")[0]) < packaging.version.parse("16.0"):
            db_data['appledbWebImage']['id'] = 'ios' + db_data["version"].split(".", 1)[0]
    elif os_str == 'macOS':
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
        if source_has_link(source, ota_url):
            print("\tURL already exists in sources")
            found_source = True
            source.setdefault("deviceMap", []).extend(augment_with_keys(supported_devices))

    if not found_source:
        print("\tAdding new source")
        source = {"deviceMap": augment_with_keys(supported_devices), "type": "ota", "links": [{"url": ota_url, "active": True}]}
        if prerequisite_builds:
            source["prerequisiteBuild"] = prerequisite_builds

        db_data["sources"].append(source)

    if bridge_version:
        db_data['bridgeOSBuild'] = info_plist['BridgeVersionInfo']['BridgeProductBuildVersion']

    json.dump(sort_os_file(None, db_data), db_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    if use_network:
        print("\tRunning update links on file")
        update_links([db_file])
    else:
        # Save the network access for the end, that way we can run it once per file instead of once per OTA
        # and we can use threads to speed it up
        update_links([db_file], False)
    print(f"\tSanity check the file{', run update_links.py, ' if not use_network else ' '}and then commit it\n")

    if bridge_version and bridge_devices:
        macos_version = db_data["version"]
        bridge_version = macos_version.replace(macos_version.split(" ")[0], bridge_version)
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

    bulk_mode = args.bulk_mode or input("Bulk mode - read data from import-ota.json/import-ota.txt? [y/n]: ").strip().lower() == "y"
    if bulk_mode:
        failed_links = []
        files_processed = set()

        if not FULL_SELF_DRIVING:
            print("Warning: you still need to be present, as this script will ask for input!")

        if Path("import-ota.json").exists():
            print("Reading versions from import-ota.json")
            versions = json.load(Path("import-ota.json").open(encoding="utf-8"))

            for version in versions:
                print(f"Importing {version['osStr']} {version['version']}")
                if "links" not in version:
                    files_processed.add(
                        create_file(version["osStr"], version["build"], version=version["version"], released=version["released"])
                    )
                else:
                    for link in version["links"]:
                        try:
                            files_processed.add(
                                import_ota(link["url"], recommended_version=version["version"], version=version["version"], released=version["released"], use_network=False, build=version["build"], prerequisite_builds=version.get("prerequisite"), device_map=version["deviceMap"])
                            )
                        except Exception:
                            failed_links.append(link["url"])

        elif Path("import-ota.txt").exists():
            print("Reading URLs from import-ota.txt")

            urls = [i.strip() for i in Path("import-ota.txt").read_text(encoding="utf-8").splitlines() if i.strip()]
            for url in urls:
                print(f"Importing {url}")
                try:
                    files_processed.add(import_ota(url, use_network=False))
                except Exception:
                    failed_links.append(url)
        else:
            raise RuntimeError("No import file found")

        print("Checking processed files for alive/hashes...")
        update_links(files_processed)
        print(f"Failed links: {failed_links}")
    else:
        while True:
            url = input("Enter OTA URL (enter to exit): ").strip()
            if not url:
                break
            import_ota(url)
#!/usr/bin/env python3

import argparse
import json
import plistlib
import re
import zipfile
from pathlib import Path

import packaging.version
import remotezip
import requests
import time
from link_info import source_has_link
from sort_os_files import sort_os_file
from update_links import update_links
from common_update_import import all_boards_covered, augment_with_keys, create_file, get_board_mapping_lower_case, get_board_mappings, OS_MAP

# TODO: createAdditionalEntries support (would only work with JSON tho)

FULL_SELF_DRIVING = False
# Use local files if found
USE_LOCAL_IF_FOUND = True
LOCAL_OTA_PATH = Path("otas")

SESSION = requests.Session()


def import_ota(
    ota_url, os_str=None, build=None, recommended_version=None, version=None, released=None, beta=None, rc=None, use_network=True, prerequisite_builds=None, device_map=None, board_map=None, rsr=False, skip_remote=False
):
    local_path = LOCAL_OTA_PATH / Path(Path(ota_url).name)
    local_available = USE_LOCAL_IF_FOUND and local_path.exists()
    ota = None
    info_plist = None
    build_manifest = None

    counter = 0
    while not skip_remote:
        try:
            ota = zipfile.ZipFile(local_path) if local_available else remotezip.RemoteZip(ota_url, initial_buffer_size=256*1024, session=SESSION, timeout=60)
            print(f"\tGetting Info.plist {'from local file' if local_available else 'via remotezip'}")

            info_plist = plistlib.loads(ota.read("Info.plist"))
            manifest_paths = [f for f in ota.namelist() if f.endswith("BuildManifest.plist")]
            build_manifest = plistlib.loads(ota.read(manifest_paths[0]))

            if info_plist.get('MobileAssetProperties'):
                info_plist = info_plist['MobileAssetProperties']

            if info_plist.get('SplatOnly'):
                rsr = True
            break
        except remotezip.RemoteIOError as e:
            if not build:
                if e.args[0].startswith('403 Client Error'):
                    print('No file')
                    raise e
                time.sleep(1+counter)
                counter += 1
                if counter > 10:
                    raise e
            info_plist = {}
    bridge_version = None

    if info_plist and info_plist.get('BridgeVersionInfo'):
        bridge_version = info_plist['BridgeVersionInfo']['BridgeVersion'].split('.')
        bridge_version = f"{(int(bridge_version[0]) - 13)}.{bridge_version[2].zfill(4)[0]}"

    if ota:
        ota.close()

    # Get the build, version, and supported devices
    buildtrain = None
    baseband_map = {}
    if build_manifest:
        # Grab baseband versions and buildtrain (both per device)
        for identity in build_manifest['BuildIdentities']:
            board_id = identity['Info']['DeviceClass']
            buildtrain = buildtrain or identity['Info']['BuildTrain']
            if 'BasebandFirmware' in identity['Manifest']:
                path = identity['Manifest']['BasebandFirmware']['Info']['Path']
                baseband_response = re.match(r'Firmware/[^-]+-([0-9.-]+)\.Release\.bbfw$', path)
                mapped_device = get_board_mapping_lower_case([board_id])[0]
                if baseband_response:
                    baseband_map[mapped_device] = baseband_response.groups(1)[0]
                else:
                    print(f"MISSING BASEBAND - {path}")
    if (ota_url.endswith(".ipsw")):
        build = build or info_plist["TargetUpdate"]
        recommended_version = recommended_version or info_plist["ProductVersion"]
        supported_devices = [info_plist["ProductType"]]
        bridge_devices = []
        prerequisite_builds = prerequisite_builds or (info_plist.get('BaseUpdate') if info_plist else [])
    else:
        build = build or info_plist["Build"]
        # TODO: Check MarketingVersion in Restore.plist in order to support older tvOS IPSWs
        # Maybe hardcode 4.0 to 4.3, 4.4 to 5.0.2, etc
        # Check by substring first?
        recommended_version = recommended_version or info_plist["OSVersion"].removeprefix("9.9.")
        if rsr:
            recommended_version = recommended_version + (f" {info_plist['ProductVersionExtra']}" if info_plist.get('ProductVersionExtra') else '')
        # Devices supported specifically in this source
        supported_boards = []
        if device_map:
            supported_devices = augment_with_keys(device_map)
            bridge_devices = []
            exclude_board_map = all_boards_covered(device_map, board_map)
            if not exclude_board_map:
                supported_boards = board_map
        elif info_plist.get('SupportedDevices'):
            supported_devices = augment_with_keys(info_plist['SupportedDevices'])

            exclude_board_map = all_boards_covered(info_plist['SupportedDevices'], info_plist['SupportedDeviceModels'])

            if not exclude_board_map:
                supported_boards = info_plist['SupportedDeviceModels']
            bridge_devices = []
        else:
            supported_devices, bridge_devices = get_board_mappings(info_plist['SupportedDeviceModels'])

        prerequisite_builds = prerequisite_builds or (info_plist.get('PrerequisiteBuild', '').split(';') if info_plist else [])
        if len(prerequisite_builds) == 1:
            prerequisite_builds = prerequisite_builds[0]
        elif len(prerequisite_builds) > 1:
            prerequisite_builds.sort()

    if not os_str:
        for product_prefix, os_str in OS_MAP:
            if any(prod.startswith(product_prefix) for prod in supported_devices):
                if os_str == "iPadOS" and packaging.version.parse(recommended_version.split(" ")[0]) < packaging.version.parse("13.0"):
                    os_str = "iOS"
                print(f"\t{os_str} {recommended_version} ({build})")
                if prerequisite_builds:
                    print(f"\tPrerequisite: {prerequisite_builds}")
                print(f"\tDevice Support: {supported_devices}")
                if supported_boards:
                    print(f"\tBoard Support: {supported_boards}")
                break
        else:
            if FULL_SELF_DRIVING:
                raise RuntimeError(f"Couldn't match product types to any known OS: {supported_devices}")
            else:
                print(f"\tCouldn't match product types to any known OS: {supported_devices}")
                os_str = input("\tEnter OS name: ").strip()

    db_file = create_file(os_str, build, FULL_SELF_DRIVING, recommended_version=recommended_version, version=version, released=released, beta=beta, rc=rc, rsr=rsr, buildtrain=buildtrain)
    db_data = json.load(db_file.open(encoding="utf-8"))

    if baseband_map:
        db_data.setdefault("basebandVersions", {}).update(baseband_map)

    db_data.setdefault("deviceMap", []).extend(supported_devices)

    found_source = False
    for source in db_data.setdefault("sources", []):
        if source_has_link(source, ota_url):
            print("\tURL already exists in sources")
            found_source = True
            source.setdefault("deviceMap", []).extend(supported_devices)

    if not found_source:
        print("\tAdding new source")
        source = {"deviceMap": supported_devices, "type": "ota", "links": [{"url": ota_url, "active": True}]}
        if prerequisite_builds:
            source["prerequisiteBuild"] = prerequisite_builds
        if supported_boards:
            source["boardMap"] = supported_boards

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
        bridge_file = create_file("bridgeOS", info_plist['BridgeVersionInfo']['BridgeProductBuildVersion'], FULL_SELF_DRIVING, recommended_version=bridge_version, released=db_data["released"])
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

    if FULL_SELF_DRIVING:
        print("Full self-driving mode enabled. Make sure to verify data before committing.")
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
                if "sources" not in version:
                    files_processed.add(
                        create_file(version["osStr"], version["build"], FULL_SELF_DRIVING, version=version["version"], released=version["released"])
                    )
                else:
                    for source in version['sources']:
                        for link in source.get('links', []):
                            try:
                                files_processed.add(
                                    import_ota(link["url"], recommended_version=version["version"], version=version["version"], released=version.get("released"), use_network=False, build=version["build"], prerequisite_builds=source.get("prerequisites", []), device_map=source["deviceMap"], board_map=source["boardMap"], skip_remote=True)
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
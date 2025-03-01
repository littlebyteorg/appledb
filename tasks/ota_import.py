#!/usr/bin/env python3

import argparse
import json
import plistlib
import re
import shutil
import zipfile
from pathlib import Path

import packaging.version
import remotezip
import requests
import time
from file_downloader import handle_ota_file
from link_info import source_has_link
from sort_os_files import sort_os_file
from update_links import update_links
from common_update_import import all_boards_covered, augment_with_keys, create_file, get_board_mapping_lower_case, get_board_mappings, OS_MAP

# TODO: createAdditionalEntries support (would only work with JSON tho)

FULL_SELF_DRIVING = False
REFRESH_EXISTING = False
# Use local files if found
USE_LOCAL_IF_FOUND = True
LOCAL_OTA_PATH = Path("otas")

SESSION = requests.Session()

def import_ota(
    ota_url, ota_key=None, os_str=None, build=None, recommended_version=None, version=None, released=None, beta=None, rc=None, \
        use_network=True, prerequisite_builds=None, device_map=None, board_map=None, rsr=False, skip_remote=False, buildtrain=None, \
        restore_version=None, bridge_version_info=None, size=None
):
    local_path = LOCAL_OTA_PATH / Path(Path(ota_url).name)
    local_available = USE_LOCAL_IF_FOUND and local_path.exists()
    ota = None
    info_plist = None
    build_manifest = None
    only_needs_baseband = False
    aea_support_filename = 'aastuff'

    # We need per-device details anyway, grab from the full OTA
    # If size is explicitly passed in, assume source is no longer active
    if skip_remote and not size:
        skip_remote = bool(prerequisite_builds) or os_str in ['iOS', 'iPadOS']
        if ota_url.endswith('.aea'):
            skip_remote = skip_remote or len(set(device_map).intersection(['Watch6,3', 'Watch6,4', 'Watch6,8', 'Watch6,9', 'Watch6,12', 'Watch6,13', 'Watch6,16', 'Watch6,17', 'Watch6,18', 'Watch7,3', 'Watch7,4', 'Watch7,5', 'Watch7,10', 'Watch7,11'])) == 0
            if not skip_remote:
                skip_remote = True
                only_needs_baseband = True

    if not skip_remote and not ota_key and ota_url.endswith('.aea'):
        ota_key = input(f"Enter OTA Key for {ota_url} (enter to skip import): ").strip()

        if not ota_key:
            raise RuntimeError(f"Couldn't determine OS details for {ota_url}")
    
    if Path('aastuff_standalone').exists():
        aea_support_filename = 'aastuff_standalone'

    counter = 0
    delete_output_dir = False
    if only_needs_baseband:
        delete_output_dir = handle_ota_file(ota_url, ota_key, aea_support_filename, only_needs_baseband)
        extracted_path = Path(str(local_path).split(".")[0])
        build_manifest = plistlib.loads(list(extracted_path.rglob("BuildManifest.plist"))[0].read_bytes())
    elif not skip_remote:
        if ota_key:
            if Path(aea_support_filename).exists():
                print('Downloading full OTA file')
                delete_output_dir = handle_ota_file(ota_url, ota_key, aea_support_filename, only_needs_baseband)
                extracted_path = Path(str(local_path).split(".")[0])
                info_plist = plistlib.loads(extracted_path.joinpath("Info.plist").read_bytes())
                build_manifest = plistlib.loads(list(extracted_path.rglob("BuildManifest.plist"))[0].read_bytes())

                if info_plist.get('MobileAssetProperties'):
                    info_plist = info_plist['MobileAssetProperties']

                if info_plist.get('SplatOnly'):
                    rsr = True
        else:
            while True:
                try:
                    ota = zipfile.ZipFile(local_path) if local_available else remotezip.RemoteZip(ota_url, initial_buffer_size=256*1024, session=SESSION, timeout=60)
                    print(f"\tGetting Info.plist {'from local file' if local_available else 'via remotezip'}")

                    info_plist = plistlib.loads(ota.read("Info.plist"))
                    manifest_paths = [f for f in ota.namelist() if f.endswith("BuildManifest.plist")]
                    if manifest_paths:
                        build_manifest = plistlib.loads(ota.read(manifest_paths[0]))

                    if info_plist.get('MobileAssetProperties'):
                        info_plist = info_plist['MobileAssetProperties']

                    if info_plist.get('SplatOnly'):
                        rsr = True
                    bridge_version_info = bridge_version_info or info_plist.get('BridgeVersionInfo')
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

    if bridge_version_info:
        bridge_version = bridge_version_info['BridgeVersion'].split('.')
        bridge_version = f"{(int(bridge_version[0]) - 13)}.{bridge_version[2].zfill(4)[-4]}"

    if ota:
        ota.close()

    # Get the build, version, and supported devices
    baseband_map = {}
    if build_manifest:
        # Grab baseband versions and buildtrain (both per device)
        for identity in build_manifest['BuildIdentities']:
            board_id = identity['Info']['DeviceClass']
            if board_id.endswith('dev'): continue
            buildtrain = buildtrain or identity['Info']['BuildTrain']
            restore_version = restore_version or identity.get('Ap,OSLongVersion')
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
        supported_boards = []
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

            if info_plist.get('SupportedDeviceModels'):
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
                break
        else:
            if FULL_SELF_DRIVING:
                raise RuntimeError(f"Couldn't match product types to any known OS: {supported_devices}")
            else:
                print(f"\tCouldn't match product types to any known OS: {supported_devices}")
                os_str = input("\tEnter OS name: ").strip()

    print(f"\t{os_str} {recommended_version} ({build})")
    if prerequisite_builds:
        print(f"\tPrerequisite: {prerequisite_builds}")
    print(f"\tDevice Support: {supported_devices}")
    if supported_boards:
        print(f"\tBoard Support: {supported_boards}")

    if restore_version is None and info_plist and info_plist.get('RestoreVersion'):
        restore_version = info_plist.get('RestoreVersion')

    db_file = create_file(os_str, build, FULL_SELF_DRIVING, recommended_version=recommended_version, version=version, released=released, beta=beta, rc=rc, rsr=rsr, buildtrain=buildtrain, restore_version=restore_version)
    db_data = json.load(db_file.open(encoding="utf-8"))

    if baseband_map:
        db_data.setdefault("basebandVersions", {}).update(baseband_map)

    db_data.setdefault("deviceMap", []).extend(supported_devices)

    found_source = False
    for source in db_data.setdefault("sources", []):
        if source_has_link(source, ota_url):
            if REFRESH_EXISTING:
                db_data['sources'].pop(db_data['sources'].index(source))
            else:
                print("\tURL already exists in sources")
                found_source = True
                source.setdefault("deviceMap", []).extend(supported_devices)
                if supported_boards:
                    source.setdefault("boardMap", []).extend(supported_boards)

    if not found_source:
        print("\tReplacing source" if REFRESH_EXISTING else "\tAdding new source")
        source = {"deviceMap": supported_devices, "type": "ota", "links": [{"url": ota_url, "active": True}]}
        if ota_key:
            source["links"][0]["decryptionKey"] = ota_key
        if prerequisite_builds:
            source["prerequisiteBuild"] = prerequisite_builds
        if supported_boards:
            source["boardMap"] = supported_boards
        if size:
            source["size"] = size

        db_data["sources"].append(source)

    if bridge_version and bridge_version_info:
        db_data['bridgeOSBuild'] = bridge_version_info['BridgeProductBuildVersion']

    json.dump(sort_os_file(None, db_data), db_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    if use_network:
        print("\tRunning update links on file")
        update_links([db_file])
    else:
        # Save the network access for the end, that way we can run it once per file instead of once per OTA
        # and we can use threads to speed it up
        update_links([db_file], False)
    print(f"\tSanity check the file{', run update_links.py, ' if not use_network else ' '}and then commit it\n")

    if bridge_version and board_map and not bridge_devices:
        _, bridge_devices = get_board_mappings(board_map)

    if bridge_version and bridge_devices:
        macos_version = db_data["version"]
        bridge_version = macos_version.replace(macos_version.split(" ")[0], bridge_version)
        bridge_file = create_file("bridgeOS", bridge_version_info['BridgeProductBuildVersion'], FULL_SELF_DRIVING, recommended_version=bridge_version, released=db_data["released"], restore_version=f"{bridge_version_info['BridgeVersion']},0")
        bridge_data = json.load(bridge_file.open(encoding="utf-8"))
        bridge_data["deviceMap"] = list(set(bridge_data.get("deviceMap", [])).union(bridge_devices))
        json.dump(sort_os_file(None, bridge_data), bridge_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    
    if delete_output_dir:
        shutil.rmtree(f"otas/{Path(ota_url).stem}")
    return db_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bulk-mode', action='store_true')
    parser.add_argument('-i', '--suffix', default="")
    parser.add_argument('-r', '--refresh-existing', action='store_true')
    parser.add_argument('-s', '--full-self-driving', action='store_true')
    args = parser.parse_args()

    if args.full_self_driving:
        FULL_SELF_DRIVING = True
    if args.refresh_existing:
        REFRESH_EXISTING = True

    bulk_mode = args.bulk_mode or input("Bulk mode - read data from import-ota.json/import-ota.txt? [y/n]: ").strip().lower() == "y"

    if FULL_SELF_DRIVING:
        print("Full self-driving mode enabled. Make sure to verify data before committing.")
    if bulk_mode:
        failed_links = []
        files_processed = set()
        file_name_base = f"import-ota-{args.suffix}" if args.suffix else "import-ota"

        if not FULL_SELF_DRIVING:
            print("Warning: you still need to be present, as this script will ask for input!")

        if Path(f"{file_name_base}.json").exists():
            print(f"Reading versions from {file_name_base}.json")
            versions = json.load(Path(f"{file_name_base}.json").open(encoding="utf-8"))

            for version in versions:
                print(f"Importing {version['osStr']} {version['version']}")
                if "sources" not in version:
                    files_processed.add(
                        create_file(version["osStr"], version["build"], FULL_SELF_DRIVING, version=version["version"], released=version["released"], buildtrain=version.get("buildTrain"), restore_version=version.get("restoreVersion"))
                    )
                else:
                    for source in version['sources']:
                        for link in source.get('links', []):
                            try:
                                files_processed.add(
                                    import_ota(
                                        link["url"], os_str=version['osStr'], ota_key=link.get('key'), recommended_version=version["version"], \
                                        released=version.get("released"), use_network=False, build=version["build"], prerequisite_builds=source.get("prerequisites", []), \
                                        device_map=source["deviceMap"], board_map=source["boardMap"], skip_remote=True, buildtrain=version.get("buildTrain"), \
                                        restore_version=version.get("restoreVersion"), bridge_version_info=version.get('bridgeVersionInfo'), size=source.get('size')
                                    )
                                )
                            except Exception:
                                failed_links.append(link["url"])

        elif Path(f"{file_name_base}.txt").exists():
            print(f"Reading URLs from {file_name_base}.txt")

            urls = [i.strip() for i in Path(f"{file_name_base}.txt").read_text(encoding="utf-8").splitlines() if i.strip()]
            for url in urls:
                print(f"Importing {url}")
                key = None
                if ';' in url:
                    url_split = url.split(';', 1)
                    url = url_split[0]
                    key = url_split[1]
                try:
                    files_processed.add(import_ota(url, ota_key=key, use_network=False))
                except Exception:
                    failed_links.append(url)
        else:
            raise RuntimeError("No import file found")

        print("Checking processed files for alive/hashes...")
        update_links(files_processed)
        if failed_links:
            print(f"Failed links: {failed_links}")
    else:
        while True:
            url = input("Enter OTA URL (enter to exit): ").strip()
            if not url:
                break
            import_ota(url)
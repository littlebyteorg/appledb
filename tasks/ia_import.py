#!/usr/bin/env python3

import argparse
import json
import plistlib
from pathlib import Path

import requests
from file_downloader import handle_pkg_file
from link_info import source_has_link
from sort_os_files import sort_os_file
from update_links import update_links
from common_update_import import create_file, get_board_mappings

# TODO: createAdditionalEntries support (would only work with JSON tho)

FULL_SELF_DRIVING = False
# Use local files if found
USE_LOCAL_IF_FOUND = True
LOCAL_IA_PATH = Path("ias")

SESSION = requests.Session()


def import_ia(
    ia_url, build=None, recommended_version=None, version=None, released=None, beta=None, rc=None, use_network=True, add_sha1_hash=False
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
    build_manifest_plist_url = ia_url.rsplit("/", 1)[0] + "/BuildManifest.plist"
    info_plist_response = SESSION.get(info_plist_url, headers={})
    build_manifest_plist_response = SESSION.get(build_manifest_plist_url, headers={})

    if not local_available:
        try:
            info_plist_response.raise_for_status()
        except requests.exceptions.HTTPError:
            print(f"\tInfo.plist not found at {info_plist_url}")
        else:
            info_plist = plistlib.loads(info_plist_response.content).get('MobileAssetProperties')

        try:
            build_manifest_plist_response.raise_for_status()
        except requests.exceptions.HTTPError:
            print(f"\tBuildManifest.plist not found at {build_manifest_plist_url}")
        else:
            build_manifest = plistlib.loads(build_manifest_plist_response.content)

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

    buildtrain = build_manifest['BuildIdentities'][0]['Info']['BuildTrain']
    restore_version = build_manifest['BuildIdentities'][0].get('Cryptex1,Version')
    print(f"\tmacOS {recommended_version} ({build})")
    print(f"\tDevice Support: {supported_devices}")

    db_file = create_file("macOS", build, FULL_SELF_DRIVING, recommended_version=recommended_version, version=version, released=released, beta=beta, rc=rc, buildtrain=buildtrain)
    db_data = json.load(db_file.open(encoding="utf-8"))

    db_data.setdefault("deviceMap", []).extend(supported_devices)

    found_source = False
    for source in db_data.setdefault("sources", []):
        if source['type'] == "installassistant":
            found_source = True
            source.setdefault("deviceMap", []).extend(supported_devices)
            if source_has_link(source, ia_url):
                print("\tURL already exists in sources")
            else:
                new_link = {"url": ia_url, "active": True}
                if catalog_name:
                    new_link['catalog'] = catalog_name
                source['links'].append(new_link)

    if not found_source:
        print("\tAdding new source")
        source = {"deviceMap": supported_devices, "type": "installassistant", "links": [{"url": ia_url, "active": True}]}
        
        (hashes, _) = handle_pkg_file(ia_url)
        source['hashes'] = hashes

        if catalog_name:
            source['links'][0]['catalog'] = catalog_name

        db_data["sources"].append(source)

    if bridge_version:
        db_data['bridgeOSBuild'] = info_plist['BridgeVersionInfo']['BridgeProductBuildVersion']

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
                        create_file(version["osStr"], version["build"], FULL_SELF_DRIVING, version=version["version"], released=version["released"])
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

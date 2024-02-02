#!/usr/bin/env python3

import argparse
import json
import plistlib
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import packaging.version
import remotezip
import requests
from link_info import needs_apple_auth, source_has_link, apple_auth_token
from sort_os_files import sort_os_file
from update_links import update_links
from common_update_import import augment_with_keys, create_file, OS_MAP

# TODO: createAdditionalEntries support (would only work with JSON tho)

FULL_SELF_DRIVING = False
# Use local files if found
USE_LOCAL_IF_FOUND = True
LOCAL_IPSW_PATH = Path("ipsws")

SESSION = requests.Session()


"""
JSON import sample:

{
    "osStr": "macOS",
    "version": "13.1 beta",
    "released": "2022-10-25",
    "build": "22C5033e",
    "links": [
        {
            "device": "Mac computers with Apple silicon", (unused field)
            "url": "https://updates.cdn-apple.com/2022FallSeed/fullrestores/012-82062/10E6B723-51B8-4B2C-BA3B-12A18ED4E719/UniversalMac_13.1_22C5033e_Restore.ipsw",
            "build": "22C5033e" (unused field)
        }
    ]
}
"""


def import_ipsw(
    ipsw_url, os_str=None, build=None, recommended_version=None, version=None, released=None, beta=None, rc=None, use_network=True
):
    local_path = LOCAL_IPSW_PATH / Path(Path(ipsw_url).name)
    local_available = USE_LOCAL_IF_FOUND and local_path.exists()

    if urlparse(ipsw_url).hostname in needs_apple_auth and not (local_available or apple_auth_token):
        raise RuntimeError(f"IPSW URL {ipsw_url} requires authentication, but no local file or auth token found")

    # Check if a BuildManifest.plist exists at the same parent directory as the IPSW
    headers = {}
    if urlparse(ipsw_url).hostname in needs_apple_auth and not local_available:
        ipsw_url = ipsw_url.replace('developer.apple.com/services-account/download?path=', 'download.developer.apple.com')
        headers = {
            "cookie": f"ADCDownloadAuth={apple_auth_token}"
        }
    build_manifest_url = ipsw_url.rsplit("/", 1)[0] + "/BuildManifest.plist"
    build_manifest_response = SESSION.get(build_manifest_url, headers=headers)

    build_manifest = None

    if not local_available:
        try:
            build_manifest_response.raise_for_status()
        except requests.exceptions.HTTPError:
            print(f"\tBuildManifest.plist not found at {build_manifest_url}, using remotezip")
        else:
            build_manifest = plistlib.loads(build_manifest_response.content)

    ipsw = None
    if not build_manifest:
        # Get it via remotezip
        ipsw = zipfile.ZipFile(local_path) if local_available else remotezip.RemoteZip(ipsw_url, headers=headers)
        print(f"\tGetting BuildManifest.plist {'from local file' if local_available else 'via remotezip'}")

        # Commented out because IPSWs should always have the BuildManifest in the root

        # manifest_paths = [file for file in ipsw.namelist() if file.endswith("BuildManifest.plist")]
        # assert len(manifest_paths) == 1, f"Expected 1 BuildManifest.plist, got {len(manifest_paths)}: {manifest_paths}"
        # build_manifest = plistlib.loads(ipsw.read(manifest_paths[0]))

        build_manifest = plistlib.loads(ipsw.read("BuildManifest.plist"))

    platform_support = None
    if os_str == "macOS" or "UniversalMac" in ipsw_url:
        if not ipsw:
            ipsw = zipfile.ZipFile(local_path) if local_available else remotezip.RemoteZip(ipsw_url)
        print(f"\tGetting PlatformSupport.plist {'from local file' if local_available else 'via remotezip'}")
        platform_support = plistlib.loads(ipsw.read("PlatformSupport.plist"))

    if ipsw:
        ipsw.close()

    # Get the build, version, and supported devices
    build = build or build_manifest["ProductBuildVersion"]
    buildtrain = build_manifest['BuildIdentities'][0]['Info']['BuildTrain']
    # TODO: Check MarketingVersion in Restore.plist in order to support older tvOS IPSWs
    # Maybe hardcode 4.0 to 4.3, 4.4 to 5.0.2, etc
    # Check by substring first?
    recommended_version = recommended_version or build_manifest["ProductVersion"]
    # Devices supported specifically in this source
    supported_devices = augment_with_keys(build_manifest["SupportedProductTypes"])
    # Devices supported in this build, but not necessarily in this source
    build_supported_devices = augment_with_keys(set(
        build_manifest["SupportedProductTypes"] + (platform_support["SupportedModelProperties"] if platform_support else [])
    ))

    if not os_str:
        for product_prefix, os_str in OS_MAP:
            if any(prod.startswith(product_prefix) for prod in supported_devices):
                if os_str == "iPadOS" and packaging.version.parse(recommended_version) < packaging.version.parse("13.0"):
                    os_str = "iOS"
                print(f"\t{os_str} {recommended_version} ({build})")
                break
        else:
            if FULL_SELF_DRIVING:
                raise RuntimeError(f"Couldn't match product types to any known OS: {supported_devices}")
            else:
                print(f"\tCouldn't match product types to any known OS: {supported_devices}")
                os_str = input("\tEnter OS name: ").strip()

    db_file = create_file(os_str, build, FULL_SELF_DRIVING, recommended_version=recommended_version, version=version, released=released, beta=beta, rc=rc, buildtrain=buildtrain)
    db_data = json.load(db_file.open(encoding="utf-8"))

    db_data.setdefault("deviceMap", []).extend(build_supported_devices)

    found_source = False
    for source in db_data.setdefault("sources", []):
        if source_has_link(source, ipsw_url):
            print("\tURL already exists in sources")
            found_source = True
            source.setdefault("deviceMap", []).extend(supported_devices)

    if not found_source:
        print("\tAdding new source")
        source = {"deviceMap": supported_devices, "type": "ipsw", "links": [{"url": ipsw_url, "active": True}]}

        db_data["sources"].append(source)

    json.dump(sort_os_file(None, db_data), db_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    if use_network:
        print("\tRunning update links on file")
        update_links([db_file])
    else:
        # Save the network access for the end, that way we can run it once per file instead of once per ipsw
        # and we can use threads to speed it up
        update_links([db_file], False)
    print(f"\tSanity check the file{', run update_links.py, ' if not use_network else ' '}and then commit it\n")
    return db_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bulk-mode', action='store_true')
    parser.add_argument('-s', '--full-self-driving', action='store_true')
    args = parser.parse_args()

    if args.full_self_driving:
        FULL_SELF_DRIVING = True

    bulk_mode = args.bulk_mode or input("Bulk mode - read data from import.json/import.txt? [y/n]: ").strip().lower() == "y"

    if FULL_SELF_DRIVING:
        print("Full self-driving mode enabled. Make sure to verify data before committing.")
    if bulk_mode:
        files_processed = set()

        if not FULL_SELF_DRIVING:
            print("Warning: you still need to be present, as this script will ask for input!")

        if Path("import.json").exists():
            print("Reading versions from import.json")
            versions = json.load(Path("import.json").open(encoding="utf-8"))

            for version in versions:
                print(f"Importing {version['osStr']} {version['version']}")
                if "links" not in version:
                    files_processed.add(
                        create_file(version["osStr"], version["build"], FULL_SELF_DRIVING, version=version["version"], released=version["released"])
                    )
                else:
                    for link in version["links"]:
                        files_processed.add(
                            import_ipsw(link["url"], version=version["version"], released=version["released"], use_network=False)
                        )

        elif Path("import.txt").exists():
            print("Reading URLs from import.txt")

            urls = [i.strip() for i in Path("import.txt").read_text(encoding="utf-8").splitlines() if i.strip()]
            for url in urls:
                print(f"Importing {url}")
                files_processed.add(import_ipsw(url, use_network=False))
        else:
            raise RuntimeError("No import file found")

        print("Checking processed files for alive/hashes...")
        update_links(files_processed)
    else:
        try:
            while True:
                url = input("Enter IPSW URL: ").strip()
                if not url:
                    break
                import_ipsw(url)
        except KeyboardInterrupt:
            pass

#!/usr/bin/env python3

import datetime
import json
import plistlib
import re
import string
import zipfile
import zoneinfo
from pathlib import Path
from urllib.parse import urlparse

import packaging.version
import remotezip
import requests
from link_info import needs_apple_auth, source_has_link, apple_auth_token
from sort_os_files import sort_os_file
from update_links import update_links

# TODO: createAdditionalEntries support (would only work with JSON tho)

FULL_SELF_DRIVING = False
# Use local files if found
USE_LOCAL_IF_FOUND = True
LOCAL_IPSW_PATH = Path("ipsws")

OS_MAP = [
    ("iPod", "iOS"),
    ("iPhone", "iOS"),
    ("iPad", "iPadOS"),
    ("AudioAccessory", "audioOS"),
    ("AppleTV", "tvOS"),
    ("Mac", "macOS"),
    ("Watch", "watchOS"),
    ("iBridge", "bridgeOS"),
]

SESSION = requests.Session()

VARIANTS = {}

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


def augment_with_keys(identifiers):
    new_identifiers = []
    for identifier in identifiers:
        new_identifiers.extend(VARIANTS.get(identifier, [identifier]))
    return new_identifiers


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


def create_file(os_str, build, recommended_version=None, version=None, released=None, beta=None, rc=None):
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
        json.dump(
            {"osStr": os_str, "version": friendly_version, "build": build},
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

    if "beta" not in db_data and (beta or "beta" in db_data["version"].lower()) or build.endswith(tuple(string.ascii_lowercase)):
        db_data["beta"] = True

    if "rc" not in db_data and (rc or "rc" in db_data["version"].lower()):
        db_data["rc"] = True

    json.dump(sort_os_file(None, db_data), db_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)

    return db_file


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
    # TODO: Check MarketingVersion in Restore.plist in order to support older tvOS IPSWs
    # Maybe hardcode 4.0 to 4.3, 4.4 to 5.0.2, etc
    # Check by substring first?
    recommended_version = recommended_version or build_manifest["ProductVersion"]
    # Devices supported specifically in this source
    supported_devices = build_manifest["SupportedProductTypes"]
    # Devices supported in this build, but not necessarily in this source
    build_supported_devices = set(
        build_manifest["SupportedProductTypes"] + (platform_support["SupportedModelProperties"] if platform_support else [])
    )

    # Get Restore.plist from the IPSW
    # restore = plistlib.loads(ipsw.read("Restore.plist"))

    # assert restore["ProductBuildVersion"] == build
    # assert restore["ProductVersion"] == version
    # assert restore["SupportedProductTypes"] == supported_devices

    supported_devices = [i for i in supported_devices if i not in ["iProd99,1", "iFPGA"]]
    build_supported_devices = [i for i in build_supported_devices if i not in ["iProd99,1", "iFPGA"]]

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

    db_file = create_file(os_str, build, recommended_version=recommended_version, version=version, released=released, beta=beta, rc=rc)
    db_data = json.load(db_file.open(encoding="utf-8"))

    db_data.setdefault("deviceMap", []).extend(augment_with_keys(build_supported_devices))

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
    elif os_str == "audioOS" and packaging.version.parse(recommended_version) >= packaging.version.parse("13.4"):
        # Apple renamed it, but we still use the old name
        os_str = "HomePod Software"

    found_source = False
    for source in db_data.setdefault("sources", []):
        if source_has_link(source, ipsw_url):
            print("\tURL already exists in sources")
            found_source = True
            source.setdefault("deviceMap", []).extend(augment_with_keys(supported_devices))

    if not found_source:
        print("\tAdding new source")
        source = {"deviceMap": augment_with_keys(supported_devices), "type": "ipsw", "links": [{"url": ipsw_url, "active": True}]}

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
    if FULL_SELF_DRIVING:
        print("Full self-driving mode enabled. Make sure to verify data before committing.")

    bulk_mode = input("Bulk mode - read data from import.json/import.txt? [y/n]: ").strip().lower() == "y"
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
                        create_file(version["osStr"], version["build"], version=version["version"], released=version["released"])
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

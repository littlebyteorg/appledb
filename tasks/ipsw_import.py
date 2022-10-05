import datetime
import json
import plistlib
import re
import string
import zoneinfo
from pathlib import Path
import packaging.version

import remotezip
import requests

from sort_files import sort_file
from update_links import update_links

FULL_SELF_DRIVING = False

OS_MAP = [
    ("iPod", "iOS"),
    ("iPhone", "iOS"),
    ("iPad", "iPadOS"),
    ("AudioAccessory", "audioOS"),
    ("AppleTV", "tvOS"),
    ("MacBook", "macOS"),
    ("Watch", "watchOS"),
    ("iBridge", "bridgeOS"),
]

SESSION = requests.Session()


def import_ipsw(ipsw_url):
    # Check if a BuildManifest.plist exists at the same parent directory as the IPSW
    build_manifest_url = ipsw_url.rsplit("/", 1)[0] + "/BuildManifest.plist"
    build_manifest_response = SESSION.get(build_manifest_url)

    build_manifest = None

    try:
        build_manifest_response.raise_for_status()
    except requests.exceptions.HTTPError:
        print("\tBuildManifest.plist not found at {}, using remotezip".format(build_manifest_url))
    else:
        build_manifest = plistlib.loads(build_manifest_response.content)

    if not build_manifest:
        # Get it via remotezip
        ipsw = remotezip.RemoteZip(ipsw_url)
        print("\tGetting BuildManifest.plist via remotezip")
        build_manifest = plistlib.loads(ipsw.read("BuildManifest.plist"))

    # Get the build, version, and supported devices
    build = build_manifest["ProductBuildVersion"]
    version = build_manifest["ProductVersion"]
    supported_devices = build_manifest["SupportedProductTypes"]

    # Get Restore.plist from the IPSW
    # restore = plistlib.loads(ipsw.read("Restore.plist"))

    # assert restore["ProductBuildVersion"] == build
    # assert restore["ProductVersion"] == version
    # assert restore["SupportedProductTypes"] == supported_devices

    supported_devices = [i for i in supported_devices if i not in ["iProd99,1", "ADP3,1"]]

    for product_prefix, os_str in OS_MAP:
        if any(prod.startswith(product_prefix) for prod in supported_devices):
            if os_str == "iPadOS" and packaging.version.parse(version) < packaging.version.parse("13.0"):
                os_str = "iOS"
            print(f"\t{os_str} {version} ({build})")
            break
    else:
        if FULL_SELF_DRIVING:
            raise RuntimeError(f"Couldn't match product types to any known OS: {supported_devices}")
        else:
            print(f"\tCouldn't match product types to any known OS: {supported_devices}")
            os_str = input("\tEnter OS name: ").strip()

    kern_version = re.search(r"\d+(?=[a-zA-Z])", build)
    assert kern_version
    kern_version = kern_version.group()

    major_version = ".".join(version.split(".")[:1]) + ".x"
    version_dir = f"{kern_version}x - {major_version}"

    db_file = Path(f"osFiles/{os_str}/{version_dir}/{build}.json")
    if db_file.exists():
        print("\tFile already exists, not replacing")
    else:
        print("\tNo file found for build {}, creating new file".format(build))
        if not db_file.parent.exists():
            raise RuntimeError(f"Couldn't find a subdirectory in {os_str} for build {build} (major {version_dir})")

        db_file.touch()
        print(f"\tCurrent version is: {version}")

        if FULL_SELF_DRIVING:
            friendly_version = f"{version} (FIXME)"
        else:
            friendly_version = input("\tEnter version (include beta/RC), or press Enter to keep current: ").strip()
            if not friendly_version:
                friendly_version = version

        json.dump({"osStr": os_str, "version": friendly_version, "build": build}, db_file.open("w", newline="\n"), indent=4)

    db_data = json.load(db_file.open())

    if not db_data.get("released"):
        print("\tMissing release date")
        if FULL_SELF_DRIVING:
            print("\tUsing placeholder for date")
            db_data["released"] = "YYYY-MM-DD"  # Should fail CI
            db_data["released"] = datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
        else:
            use_today = bool(input("\tUse today's date? [y/n]: ").strip().lower() == "y")
            if use_today:
                db_data["released"] = datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
            else:
                db_data["released"] = input("\tEnter release date (YYYY-MM-DD): ").strip()

    if "beta" not in db_data and ("beta" in version.lower() or "rc" in version.lower()) or build.endswith(tuple(string.ascii_lowercase)):
        db_data["beta"] = True

    db_data.setdefault("deviceMap", []).extend(supported_devices)

    found_source = False
    for source in db_data.setdefault("sources", []):
        for link in source["links"]:
            if link["url"] == ipsw_url:
                print("\tIPSW URL already exists in sources")
                found_source = True
                source.setdefault("deviceMap", []).extend(supported_devices)

    if not found_source:
        print("\tAdding new source")
        source = {
            "deviceMap": supported_devices,
            "type": "ipsw",
            "links": [
                {
                    "url": ipsw_url,
                },
            ],
        }

        db_data["sources"].append(source)

    json.dump(sort_file(None, db_data), db_file.open("w", newline="\n"), indent=4)
    if FULL_SELF_DRIVING:
        print("\tRunning update links on file")
        update_links([db_file])
    else:
        # Save the network access for the end, that way we can run it once per file instead of once per ipsw
        # and we can use threads to speed it up
        update_links([db_file], False)
    print(f"\tSanity check the file{', run update_links.py, ' if not FULL_SELF_DRIVING else ''}and then commit it\n")
    return db_file


if __name__ == "__main__":
    if FULL_SELF_DRIVING:
        print("Full self-driving mode enabled")

    bulk_mode = input("Bulk mode - read URLs from import.txt? [y/n]: ").strip().lower() == "y"
    if bulk_mode:
        files_processed = set()

        if not FULL_SELF_DRIVING:
            print("Warning: you still need to be present, as this script will ask for input!")
        urls = [i.strip() for i in Path("import.txt").read_text().splitlines() if i.strip()]
        for url in urls:
            print(f"Importing {url}")
            files_processed.add(import_ipsw(url))

        print("Checking processed files for alive/hashes...")
        update_links(files_processed)
    else:
        try:
            while True:
                url = input("Enter IPSW URL: ").strip()
                import_ipsw(url)
        except KeyboardInterrupt:
            pass

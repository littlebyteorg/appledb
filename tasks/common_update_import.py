#!/usr/bin/env python3

import datetime
import json
import re
import zoneinfo
from pathlib import Path

import packaging.version
from image_info import get_image
from support_page_info import get_release_notes_link
from sort_os_files import sort_os_file

OS_MAP = [
    ("iPod", "iOS"),
    ("iPhone", "iOS"),
    ("iPad", "iPadOS"),
    ("AudioAccessory", "audioOS"),
    ("AppleTV", "tvOS"),
    ("ComputeModule", "cloudOS"),
    ("Mac", "macOS"),
    ("Watch", "watchOS"),
    ("iBridge", "bridgeOS"),
    ("RealityDevice", "visionOS"),
    ("AppleDisplay", "Studio Display Firmware"),
]

FILTERED_OUT_DEVICES = ["iProd99,1", "iFPGA", "iSim1,1", "Watch1,2-Store-Dock"]

VARIANTS = {}
BOARD_IDS = {}

MULTI_BOARD_DEVICES = {}

for device in Path("deviceFiles").rglob("*.json"):
    device_data = json.load(device.open(encoding="utf-8"))
    name = device_data["name"]
    identifiers = device_data.get("identifier", [])
    if isinstance(identifiers, str):
        identifiers = [identifiers]
    if not identifiers:
        identifiers = [name]
    key = device_data.get("key", identifiers[0] if identifiers else name)
    if key in FILTERED_OUT_DEVICES: continue

    for identifier in identifiers:
        VARIANTS.setdefault(identifier, set()).add(key)
        if device_data.get('board'):
            if isinstance(device_data['board'], list):
                for board in device_data['board']:
                    BOARD_IDS.setdefault(board.upper() if device_data.get("type") == "iBridge" else board, set()).add(key)
                MULTI_BOARD_DEVICES[key] = device_data['board']
            else:
                board = device_data['board']
                BOARD_IDS.setdefault(board.upper() if device_data.get("type") == "iBridge" else board, set()).add(key)

def augment_with_keys(identifiers):
    new_identifiers = []
    for identifier in identifiers:
        if identifier in FILTERED_OUT_DEVICES: continue
        new_identifiers.extend(VARIANTS.get(identifier, [identifier]))
    return new_identifiers

def get_board_mapping_lower_case(devices):
    modified_mapping = {k.lower(): v for k,v in BOARD_IDS.items()}
    identifiers = []
    for device in devices:
        device_mappings = list(modified_mapping.get(device, []))
        if not device_mappings:
            continue
        identifiers.extend(augment_with_keys(device_mappings))
    return identifiers

def get_board_mappings(devices):
    identifiers = []
    bridge_identifiers = []
    for device in devices:
        device_mappings = list(BOARD_IDS.get(device, []))
        if not device_mappings:
            continue
        if device_mappings[0].startswith("iBridge"):
            bridge_identifiers.extend(device_mappings)
        else:
            identifiers.extend(augment_with_keys(device_mappings))
    return identifiers, bridge_identifiers

def all_boards_covered(identifiers, boards):
    has_boards = True
    for identifier in identifiers:
        if MULTI_BOARD_DEVICES.get(identifier):
            has_boards = has_boards and set(MULTI_BOARD_DEVICES[identifier]).intersection(boards) == set(MULTI_BOARD_DEVICES[identifier])
    return has_boards

def create_file(os_str, build, full_self_driving, recommended_version=None, version=None, released=None, beta=None, rc=None, buildtrain=None, rsr=False, restore_version=None):
    assert version or recommended_version, "Must have either version or recommended_version"

    file_updated = False

    kern_version = re.search(r"\d+(?=[a-zA-Z])", build)
    assert kern_version
    kern_version = kern_version.group()

    major_version = ".".join((version or recommended_version).split(".")[:1]) + ".x"  # type: ignore
    version_dir = f"{kern_version}x - {major_version}"

    os_str_override = os_str

    if os_str == "audioOS" and packaging.version.parse(recommended_version.split(" ")[0]) >= packaging.version.parse("13.4"):
        os_str_override = 'HomePod Software'

    file_path = f"osFiles/{os_str}/{version_dir}/{build}.json"
    if rsr:
        file_path = file_path.replace("osFiles", "osFiles/Rapid Security Responses")

    db_file = Path(file_path)
    if db_file.exists():
        print("\tFile already exists, not replacing")
        db_data = json.load(db_file.open(encoding="utf-8"))
    else:
        file_updated = True
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
        elif full_self_driving:
            friendly_version = f"{recommended_version} (FIXME)"
        else:
            friendly_version = input("\tEnter version (include beta/RC), or press Enter to keep current: ").strip()
            if not friendly_version:
                friendly_version = version or recommended_version
        # HACK: Apple sometimes screws up in the dev portal
        friendly_version = " ".join(filter(None, friendly_version.split(" ")))
        db_data = {"osStr": os_str_override, "version": friendly_version, "build": build}

        web_image = get_image(os_str, friendly_version)
        if web_image:
            db_data['appledbWebImage'] = web_image

    if buildtrain and buildtrain != db_data.get('buildTrain'):
        file_updated = True
        db_data['buildTrain'] = buildtrain

    if restore_version and restore_version != db_data.get('restoreVersion'):
        file_updated = True
        db_data['restoreVersion'] = restore_version

    if not db_data.get("released"):
        file_updated = True
        print("\tMissing release date")
        if released:
            print(f"\tRelease date is: {released}")
            db_data["released"] = released
        elif full_self_driving:
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
        file_updated = True
        db_data["beta"] = True

    if "rc" not in db_data and (rc or "rc" in db_data["version"].lower()):
        file_updated = True
        db_data["rc"] = True

    if "releaseNotes" not in db_data and not db_data.get("beta") and not db_data.get("rc"):
        release_notes_link = get_release_notes_link(os_str, db_data["version"])
        if release_notes_link:
            file_updated = True
            db_data["releaseNotes"] = release_notes_link

    # Only write to file if required
    if file_updated:
        json.dump(
            sort_os_file(None, db_data),
            db_file.open("w", encoding="utf-8", newline="\n"),
            indent=4,
            ensure_ascii=False,
        )

    return db_file
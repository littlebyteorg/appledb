#!/usr/bin/env python3

import enum
import io
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
import zipfile

import dateutil.parser
import remotezip
import requests
from sort_os_files import sort_os_file


class Platforms(enum.IntEnum):
    UNIVERSAL = 0
    DESKTOP = 3
    MOBILE = 4
    XBOX = 5
    TEAM = 6
    HOLOGRAPHIC = 10
    CORE = 16


# Map device name to name in AppleDB
OSSTR_MAP = {}
for f in Path("deviceFiles/Software").rglob("*.json"):
    data = json.load(f.open(encoding="utf-8"))
    if "windowsStoreId" in data:
        OSSTR_MAP[data["windowsStoreId"]] = data["name"]

IDENTITY_FILTER = {"9PB2MZ1ZMB1S": "AppleInc.iTunes"}

SESSION = requests.Session()


def import_appx(store_id, released, file):
    # Get version
    version = None
    # with remotezip.RemoteZip(file["url"]) as appx_bundle:
    with zipfile.ZipFile(io.BytesIO(requests.get(file["url"]).content)) as appx_bundle:
        if "AppxManifest.xml" in appx_bundle.namelist():
            bundle_manifest = ET.fromstring(appx_bundle.read("AppxManifest.xml").decode("utf-8"))
        else:
            bundle_manifest = ET.fromstring(appx_bundle.read("AppxMetadata/AppxBundleManifest.xml").decode("utf-8"))
        identity = bundle_manifest.find("./{http://schemas.microsoft.com/appx/2013/bundle}Identity")
        if identity is None:
            identity = bundle_manifest.find("./{http://schemas.microsoft.com/appx/2016/bundle}Identity")
        if identity is None:
            identity = bundle_manifest.find("./{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Identity")
        if identity is None:
            raise RuntimeError("Couldn't find Identity in bundle manifest")
        version = identity.attrib["Version"]

    if not version:
        raise RuntimeError("Couldn't find version")

    os_str = OSSTR_MAP[store_id]
    db_file = Path(f"osFiles/Software/{os_str}/{version}.json")
    if db_file.exists():
        print("\tFile already exists, not replacing")
    else:
        print(f"\tNo file found for version {version}, creating new file")
        if not db_file.parent.exists() and not db_file.parent.parent.exists():
            raise RuntimeError(f"Couldn't find a Software directory for {os_str}")
        elif not db_file.parent.exists():
            print(f"Warning: no subdirectory found for {os_str}, creating new one")
            db_file.parent.mkdir()

        db_file.touch()
        print(f"\tCurrent version is: {version}")

        json.dump(
            {"osStr": os_str, "version": version, "deviceMap": [os_str]},
            db_file.open("w", encoding="utf-8", newline="\n"),
            indent=4,
            ensure_ascii=False,
        )

    db_data = json.load(db_file.open(encoding="utf-8"))

    if not db_data.get("released"):
        db_data["released"] = dateutil.parser.parse(released).strftime("%Y-%m-%d")

    update_id = file["update_id"]
    revision = file["revision_number"]

    for source in db_data.setdefault("sources", []):
        windows_update_details = source.get("windowsUpdateDetails")
        if windows_update_details.get("updateId") == update_id and windows_update_details.get("revisionId") == revision:
            print("\tUpdate ID already exists in sources")
            break
    else:
        print("\tAdding new source")
        source = {
            "windowsUpdateDetails": {
                "updateId": update_id,
                "revisionId": revision,
            },
            "deviceMap": [os_str],
            "type": "appx",
            "links": [{"url": f"https://apps.microsoft.com/store/detail/{store_id}", "active": True}],
            "size": int(file["size"]),
            "hashes": {},
        }

        for digest, digest_type in [(file["digest"], file["digest_type"]), (file["additional_digest"], file["additional_digest_type"])]:
            if digest_type == "SHA1":
                source["hashes"]["sha1"] = digest
            elif digest_type == "SHA256":
                source["hashes"]["sha2-256"] = digest
            else:
                raise RuntimeError(f"Unknown digest type: {digest_type}")

        db_data["sources"].append(source)

    json.dump(sort_os_file(None, db_data), db_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)

    return db_file


if __name__ == "__main__":
    if Path("import_wu.json").exists():
        print("Reading apps from import_wu.json")
        apps = json.load(Path("import_wu.json").open(encoding="utf-8"))

        for app in apps:
            files = [i for i in app["files"] if i["main"]]
            files = [
                i
                for i in files
                if not (
                    i["filename"].endswith(".eappxbundle")
                    or i["filename"].endswith(".eappx")
                    or i["filename"].endswith(".emsixbundle")
                    or i["filename"].endswith(".emsix")
                )
            ]
            # files = [i for i in files if not set(i["platforms"]) & {Platforms.UNIVERSAL, Platforms.DESKTOP}]
            if app["product_id"] in IDENTITY_FILTER:
                files = [i for i in files if i["identity"] == IDENTITY_FILTER[app["product_id"]]]
            for file in files:
                print(f"Importing {file['installer_specific_identifier']} ")
                import_appx(app["product_id"], app["last_update_date"], file)
    else:
        print("No import_wu.json found")
        sys.exit(1)

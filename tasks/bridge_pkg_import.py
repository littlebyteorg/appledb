#!/usr/bin/env python3

from datetime import date, timezone
import json
import plistlib
import random
from pathlib import Path
import argparse
from zoneinfo import ZoneInfo

import requests

from file_downloader import handle_pkg_file
from sort_os_files import sort_os_file
from link_info import source_has_link
from update_links import update_links
from common_update_import import create_file

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--versions', default=['15'], nargs="+")
parser.add_argument('-r', '--release-types', default=['release'], nargs="+", choices=['dev', 'public', 'release'])
parser.add_argument('-a', '--all', action='store_true')
args = parser.parse_args()

max_version = int(sorted([str(x).split(" - ")[1] for x in list(Path('osFiles/macOS').glob("*")) if not str(x).endswith('.DS_Store')])[-2].removesuffix('.x'))

SESSION = requests.session()

RELEASE_CATALOG_NAME_MAP = {
    'dev': 'dev-beta',
    'public': 'public-beta',
    'release': ''
}

RELEASE_CATALOG_MAP = {
    'dev': 'seed',
    'public': 'beta',
    'release': ''
}

def convert_version_to_build(base_version):
    version_split = base_version.split('.')
    version_split[2] = version_split[2][-4:]
    if version_split[3] == "0":
        version_split[2] = str(int(version_split[2]))
    return f"{version_split[0]}{chr(int(version_split[1]) + 64)}{version_split[3] if version_split[3] != "0" else ""}{version_split[2]}{chr(int(version_split[4])+96) if version_split[4] != "0" else ""}"

updated_files = set()
manifest_path = 'usr/standalone/firmware/bridgeOSCustomer.bundle/Contents/Resources/BuildManifest.plist'
file_hashes = {}
manifest = {}
for version in args.versions:
    print(version)
    for release_type in args.release_types:
        print(release_type)
        raw_sucatalog = SESSION.get(f'https://swscan.apple.com/content/catalogs/others/index-{version}{RELEASE_CATALOG_MAP[release_type]}-1.sucatalog?cachebust{random.randint(100, 1000)}')
        raw_sucatalog.raise_for_status()

        catalog_name = RELEASE_CATALOG_NAME_MAP.get(release_type, "")

        file_suffix = "-bridge"
        if catalog_name:
            file_suffix = f"{file_suffix}-{catalog_name}"

        plist = plistlib.loads(raw_sucatalog.content).get('Products', {})
        for product in plist.values():
            if product.get('ExtendedMetaInfo', {}).get('ProductType') != 'bridgeOS':
                continue
            if product['PostDate'].date() != date.today() and not args.all:
                continue
            url = product['ServerMetadataURL'].replace('.smd', '.pkg')
            build = convert_version_to_build(product['ExtendedMetaInfo']['BridgeOSPredicateProductOrdering'])
            print(build)
            file_location = Path(f'osFiles/bridgeOS/{build[0:2]}x - {int(build[0:2]) - 13}.x/{build}.json')
            if not file_location.exists():
                (file_hashes, manifest) = handle_pkg_file(download_link=url, extracted_manifest_file_path=manifest_path, file_suffix=file_suffix)
                create_file("bridgeOS", build, False, recommended_version=manifest['ProductVersion'], released=product['PostDate'].replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d"), buildtrain=manifest['BuildIdentities'][0]['Info']['BuildTrain'])
            db_data = json.load(file_location.open(encoding="utf-8"))
            found_source = False
            has_new_link = False

            new_sources = []

            file_size = int(SESSION.head(url).headers["Content-Length"])

            for source in db_data.setdefault("sources", []):
                if source_has_link(source, url):
                    found_source = True
                elif source['size'] == file_size:
                    new_link = {
                        'url': url,
                        'active': True
                    }
                    if catalog_name:
                        new_link['catalog'] = catalog_name

                    source['links'].append(new_link)
                    found_source = True
                    has_new_link = True
                new_sources.append(source)
            if not found_source:
                if not file_hashes or not manifest:
                    (file_hashes, manifest) = handle_pkg_file(download_link=url, extracted_manifest_file_path=manifest_path, file_suffix=file_suffix)
                db_data['buildTrain'] = manifest['BuildIdentities'][0]['Info']['BuildTrain']
                db_data.setdefault('deviceMap', []).extend(manifest["SupportedProductTypes"])
                new_link = {
                    'url': url,
                    'active': True
                }
                if catalog_name:
                    new_link['catalog'] = catalog_name
                source = {"deviceMap": db_data['deviceMap'], "type": "pkg", "links": [new_link], "hashes": file_hashes}
                new_sources.append(source)
                has_new_link = True
            if has_new_link:
                db_data['sources'] = new_sources
                json.dump(sort_os_file(None, db_data), file_location.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
                update_links([file_location])

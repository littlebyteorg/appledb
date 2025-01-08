#!/usr/bin/env python3

import json
import plistlib
import random
from pathlib import Path
import argparse

import requests

from file_downloader import handle_pkg_file
from sort_os_files import sort_os_file
from link_info import source_has_link
from update_links import update_links

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--version', default=15)
parser.add_argument('-b', '--beta', action='store_true')
parser.add_argument('-p', '--public-beta', action='store_true')
args = parser.parse_args()

SESSION = requests.session()

MAC_CATALOG_SUFFIX = ''
if args.beta:
    MAC_CATALOG_SUFFIX = 'seed'
elif args.public_beta:
    MAC_CATALOG_SUFFIX = 'beta'

def convert_version_to_build(version):
    version_split = version.split('.')
    version_split[2] = version_split[2][-4:]
    if version_split[3] == "0":
        version_split[2] = str(int(version_split[2]))
    return f"{version_split[0]}{chr(int(version_split[1]) + 64)}{version_split[3] if version_split[3] != "0" else ""}{version_split[2]}{chr(int(version_split[4])+96) if version_split[4] != "0" else ""}"

updated_files = set()
raw_sucatalog = SESSION.get(f'https://swscan.apple.com/content/catalogs/others/index-{args.version}{MAC_CATALOG_SUFFIX}-1.sucatalog?cachebust{random.randint(100, 1000)}')
raw_sucatalog.raise_for_status()

plist = plistlib.loads(raw_sucatalog.content).get('Products', {})
for product in plist.values():
    if product.get('ExtendedMetaInfo', {}).get('ProductType') != 'bridgeOS':
        continue
    url = product['ServerMetadataURL'].replace('.smd', '.pkg')
    build = convert_version_to_build(product['ExtendedMetaInfo']['BridgeOSPredicateProductOrdering'])
    print(build)
    file_location = Path(f'osFiles/bridgeOS/{build[0:2]}x - {int(build[0:2]) - 13}.x/{build}.json')
    if not file_location.exists():
        print('File missing, import macOS OTAs first')
        continue
    db_data = json.load(file_location.open(encoding="utf-8"))
    found_source = False

    new_sources = []

    file_size = int(SESSION.head(url).headers["Content-Length"])

    for source in db_data.setdefault("sources", []):
        if source_has_link(source, url):
            found_source = True
            print("\tURL already exists in sources")
        elif source['size'] == file_size:
            new_link = {
                'url': url,
                'active': True
            }
            if args.beta:
                new_link['catalog'] = 'dev-beta'
            elif args.public_beta:
                new_link['catalog'] = 'public-beta'

            source['links'].append(new_link)
            found_source = True
        new_sources.append(source)
    if not found_source:
        manifest_path = 'usr/standalone/firmware/bridgeOSCustomer.bundle/Contents/Resources/BuildManifest.plist'
        (file_hashes, manifest) = handle_pkg_file(download_link=url, extracted_manifest_file_path=manifest_path)
        db_data['buildTrain'] = manifest['BuildIdentities'][0]['Info']['BuildTrain']
        db_data['deviceMap'].extend(manifest["SupportedProductTypes"])
        new_link = {
            'url': url,
            'active': True
        }
        if args.beta:
            new_link['catalog'] = 'dev-beta'
        elif args.public_beta:
            new_link['catalog'] = 'public-beta'
        source = {"deviceMap": db_data['deviceMap'], "type": "pkg", "links": [new_link], "hashes": file_hashes}
        new_sources.append(source)
    db_data['sources'] = new_sources
    json.dump(sort_os_file(None, db_data), file_location.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    updated_files.add(file_location)

update_links(list(updated_files))

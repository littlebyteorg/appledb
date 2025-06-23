#!/usr/bin/env python3

import plistlib
import random
from pathlib import Path
import argparse
from datetime import date
import string

import requests

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--min-version', default=13, type=int)
parser.add_argument('-b', '--beta', action='store_true')
parser.add_argument('-a', '--all', action='store_true')
args = parser.parse_args()

VARIATION_CATALOG_MAPS = {
    'seed': 'dev-beta',
    'beta': 'public-beta'
}

max_version = int(sorted([str(x).split(" - ")[1] for x in list(Path('osFiles/macOS').glob("*")) if not str(x).endswith('.DS_Store')])[-2].removesuffix('.x'))

SESSION = requests.session()

variations = []

if args.beta:
    variations.append('seed')
    variations.append('beta')
else:
    variations.append('')

links = set()

mac_version_overrides = {
    11: '10.16',
    # force corrections in both directions
    16: '26',
    23: '13',
    24: '14',
    25: '15'
}

mac_versions = [mac_version_overrides.get(args.min_version, args.min_version)]
if args.beta and args.min_version < max_version:
    mac_versions.append(mac_version_overrides.get(args.min_version + 1, args.min_version + 1))

for mac_version in mac_versions:
    for variation in variations:
        raw_sucatalog = SESSION.get(f'https://swscan.apple.com/content/catalogs/others/index-{mac_version}{variation}-1.sucatalog?{random.choice(string.ascii_letters)}cachebust{random.randint(100, 1000)}')
        raw_sucatalog.raise_for_status()

        plist = plistlib.loads(raw_sucatalog.content).get('Products', {})
        for product in plist.values():
            if not product.get('ExtendedMetaInfo', {}).get('InstallAssistantPackageIdentifiers'):
                continue
            if 'InstallAssistantAuto' in product.get('ServerMetadataURL', ''):
                continue
            if product['PostDate'].date() != date.today() and not args.all:
                continue
            base_url = product['Packages'][0]['URL'].rsplit("/", 1)[0]
            if VARIATION_CATALOG_MAPS.get(variation):
                links.add(f"{base_url}/InstallAssistant.pkg;{VARIATION_CATALOG_MAPS[variation]}")
            else:
                links.add(f"{base_url}/InstallAssistant.pkg")

if len(links):
    print(f"{len(links)} links added")
    _ = [i.unlink() for i in Path.cwd().glob("import-ia.*") if i.is_file()]
    Path("import-ia.txt").write_text("\n".join(sorted(links)), "utf-8")

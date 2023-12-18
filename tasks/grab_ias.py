#!/usr/bin/env python3

import json
import plistlib
import random
from pathlib import Path
import argparse

import requests

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--min-version', default=12, type=int)
parser.add_argument('-b', '--beta', action='store_true')
args = parser.parse_args()

VARIATION_CATALOG_MAPS = {
    'seed': 'dev-beta',
    'beta': 'public-beta'
}


SESSION = requests.session()

variations = []

if args.beta:
    variations.append('seed')
    variations.append('beta')
else:
    variations.append('')

links = set()

mac_versions = [args.min_version]
if args.beta:
    mac_versions.append(args.min_version + 1)

for mac_version in mac_versions:
    for variation in variations:
        raw_sucatalog = SESSION.get(f'https://swscan.apple.com/content/catalogs/others/index-{mac_version}{variation}-1.sucatalog?cachebust{random.randint(100, 1000)}')
        raw_sucatalog.raise_for_status()

        plist = plistlib.loads(raw_sucatalog.content)['Products']
        for product in plist.values():
            if not product.get('ExtendedMetaInfo', {}).get('InstallAssistantPackageIdentifiers'):
                continue
            base_url = product['Packages'][0]['URL'].rsplit("/", 1)[0]
            if VARIATION_CATALOG_MAPS.get(variation):
                links.add(f"{base_url}/InstallAssistant.pkg;{VARIATION_CATALOG_MAPS[variation]}")
            else:
                links.add(f"{base_url}/InstallAssistant.pkg")

[i.unlink() for i in Path.cwd().glob("import-ia") if i.is_file()]
Path("import-ia.txt").write_text("\n".join(sorted(links)), "utf-8")

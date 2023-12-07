#!/usr/bin/env python3

import sys
import json
import plistlib
import random
from pathlib import Path
import html

import dateutil.parser
import lxml.etree
import lxml.html
import requests

from sort_os_files import sort_os_file
from update_links import update_links

result = requests.get(f"https://developer.apple.com/safari/resources/?cachebust{random.randint(100, 1000)}")
result.raise_for_status()
element = lxml.html.fromstring(result.text)

section = element.xpath('.//div[@class="callout"]')[0]

links = section.xpath('.//ul/li')

table = section.xpath('.//div[@class="column"]/p')

sources = {
    'dmg': {},
    'pkg': {}
}

mac_versions = set()

for link in links:
    a_tag = link.xpath('a')[0]
    if not a_tag.attrib.get("class", ""):
        continue
    span_text = html.unescape(link.xpath('span')[0].text).split()[2]
    mac_versions.add(span_text)
    sources['dmg'][span_text] = a_tag.attrib.get("href")

properties = {}
property_name = ""
for cell in table:
    if "sosumi" in cell.attrib.get("class", ""):
        property_name = cell.text
    else:
        properties[property_name] = cell.text

if Path(f"osFiles/Software/Safari Technology Preview/{properties['Release']}.json").exists():
    print(f"{properties['Release']}.json already exists, exiting...")
    sys.exit(0)

properties['Posted'] = dateutil.parser.parse(properties["Posted"]).date()

mac_versions = list(mac_versions)

for mac_version in mac_versions:
    raw_sucatalog = requests.get(f'https://swscan.apple.com/content/catalogs/others/index-{mac_version}-1.sucatalog?cachebust{random.randint(100, 1000)}')
    raw_sucatalog.raise_for_status()

    plist = plistlib.loads(raw_sucatalog.content)['Products']
    catalog_safari = None
    for product in plist.values():
        if "SafariTechPreview" not in product.get("ServerMetadataURL", ""):
            continue

        dist_response = requests.get(product['Distributions']['English']).text
        dist_version = dist_response.split('"SU_VERS" = "')[1].split('"')[0]
        if dist_version != properties['Release']:
            print(f'Version mismatch - macOS {mac_version}')
            continue
        catalog_safari = product
        break

    if not catalog_safari:
        print(f'Missing Safari Tech Preview for macOS {mac_version}')
        continue

    safari_metadata = plistlib.loads(requests.get(catalog_safari['ServerMetadataURL']).content)
    safari_version = safari_metadata['CFBundleShortVersionString']
    sources['pkg'][mac_version] = catalog_safari['Packages'][0]['URL']

source = {
    "osStr": "Safari Technology Preview",
    "version": properties["Release"],
    "safariVersion": safari_version,
    "released": properties["Posted"].strftime("%Y-%m-%d"),
    "beta": True,
    "releaseNotes": f"https://developer.apple.com/documentation/safari-technology-preview-release-notes/stp-release-{properties['Release']}",
    "deviceMap": [
        "Safari Technology Preview"
    ],
    "osMap": [f"macOS {x}" for x in sources['dmg'].keys()],
    "sources": []
}

for package_type, type_sources in sources.items():
    for mac_version, link in type_sources.items():
        source["sources"].append({
            "type": package_type,
            "deviceMap": [
                "Safari Technology Preview"
            ],
            "osMap": [f"macOS {mac_version}"],
            "links": [{"url": link}]
        })
stp_file = Path(f"osFiles/Software/Safari Technology Preview/{properties['Release']}.json")
if not stp_file.exists():
    json.dump(sort_os_file(None, source), stp_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)

    update_links([stp_file])

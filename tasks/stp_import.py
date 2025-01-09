#!/usr/bin/env python3

import argparse
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

from file_downloader import handle_pkg_file
from sort_os_files import sort_os_file
from update_links import update_links

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--force', action='store_true')
args = parser.parse_args()

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
    try:
        a_tag = link.xpath('a')[0]
    except:
        continue
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

properties['Release'] = properties['Release'].split(" ")[0]

if Path(f"osFiles/Software/Safari Technology Preview/{properties['Release']}.json").exists() and not args.force:
    print(f"{properties['Release']}.json already exists, exiting...")
    sys.exit(0)

properties['Posted'] = dateutil.parser.parse(properties["Posted"]).date()

mac_versions = list(mac_versions)

safari_version = None

link_version_map = {}

for mac_version in mac_versions:
    raw_sucatalog = requests.get(f'https://swscan.apple.com/content/catalogs/others/index-{mac_version}-1.sucatalog?appledbcachebust{random.randint(100, 1000)}')
    raw_sucatalog.raise_for_status()

    plist = plistlib.loads(raw_sucatalog.content).get('Products', {})
    catalog_safari = []
    for product in plist.values():
        if "SafariTechPreview" not in product.get("ServerMetadataURL", ""):
            continue

        metadata_url = product['ServerMetadataURL']

        dist_response = requests.get(product['Distributions']['English']).text
        os_version = dist_response.split("system.compareVersions(myTargetSystemVersion.ProductVersion, '")[1].split(".")[0]
        dist_version = dist_response.split('"SU_VERS" = "')[1].split('"')[0]
        if dist_version != properties['Release']:
            print(f'Version mismatch - macOS {mac_version}')
            continue
        catalog_safari.append(product)
        sources['pkg'][os_version] = product['Packages'][0]['URL']

    if not catalog_safari:
        print(f'Missing Safari Tech Preview for macOS {mac_version}')
        continue

    safari_metadata = plistlib.loads(requests.get(metadata_url).content)
    safari_version = safari_metadata['CFBundleShortVersionString']

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
        (file_hashes, _) = handle_pkg_file(download_link=link, hashes=['md5', 'sha1', 'sha2-256'])
        source["sources"].append({
            "type": package_type,
            "deviceMap": ["Safari Technology Preview"],
            "osMap": [f"macOS {mac_version}"],
            "hashes": file_hashes,
            "links": [{"url": link}]
        })
stp_file = Path(f"osFiles/Software/Safari Technology Preview/{properties['Release']}.json")
if args.force or not stp_file.exists():
    json.dump(sort_os_file(None, source), stp_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)

    update_links([stp_file])

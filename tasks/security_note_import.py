#!/usr/bin/env python3

import json
from pathlib import Path
import argparse

import dateutil.parser
import lxml.etree
import lxml.html
import requests

from sort_os_files import sort_os_file

supported_product_list = [
    'iOS',
    'iPadOS',
    'macOS',
    'Safari',
    'tvOS',
    'visionOS',
    'watchOS',
    'Xcode',
]

software_list = [
    'Safari',
    'Xcode'
]

build_prefix_offset = {
    'iOS': 4,
    'iPadOS': 4,
    'macOS': 9,
    'tvOS': 4,
    'visionOS': 20,
    'watchOS': 11,
    'Xcode': 0,
}

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--product', choices=supported_product_list)
parser.add_argument('-v', '--version')
parser.add_argument('-d', '--date')
args = parser.parse_args()


if bool(args.version) != bool(args.product):
    parser.error("product and version must either both be provided or both be absent")

result = requests.get("https://support.apple.com/en-us/100100?cachebust111")
result.raise_for_status()
element = lxml.html.fromstring(result.text)

rows = element.xpath('.//table//td/..')
found_links = {}
break_loop = False
for row in rows:
    cells = row.getchildren()
    if cells[2].text == 'Preinstalled': continue
    date = dateutil.parser.parse(cells[2].text_content()).strftime("%Y-%m-%d")
    if args.date:
        if date < args.date: break
        if date > args.date: continue
    link_element = cells[0].getchildren()[0].getchildren()
    if not link_element: continue
    link_element = link_element[0]
    link = f"https://support.apple.com/{link_element.attrib.get("href").split("/")[-1]}"
    impacted_versions = link_element.text

    for impacted_version in impacted_versions.split(' and '):
        impacted_version_split = impacted_version.replace(' for Windows', '').split(' ')
        if impacted_version_split[0] not in supported_product_list: continue
        if args.product and impacted_version_split[0] != args.product: continue
        if args.version:
            if args.version != impacted_version_split[-1]: continue
            found_links.setdefault(impacted_version_split[0], {})[impacted_version_split[-1]] = link
            break_loop = True
            break
        else:
            found_links.setdefault(impacted_version_split[0], {})[impacted_version_split[-1]] = link

    if break_loop: break

for product in found_links.keys():
    product_subfolder = product
    if product in software_list:
        product_subfolder = f"Software/{product}"

    for version, link in found_links[product].items():
        parsed_version = int(version.split('.', 1)[0])
        build_subfolder = ''
        if build_prefix_offset.get(product) is not None:
            build_subfolder = f"/{parsed_version + build_prefix_offset[product]}x - {parsed_version}"
        else:
            build_subfolder = f"/{parsed_version}"
        build_paths = Path(f"osFiles/{product_subfolder}{build_subfolder}.x").rglob("*.json")
        for build_path in build_paths:
            build_data = json.load(build_path.open(encoding="utf-8"))
            if build_data['version'].removesuffix('.0') != version: continue
            # Explicit True check for preinstalled to prevent arrays from causing a skip
            if build_data.get('internal', False) or build_data.get('preinstalled', False) == True: continue
            build_data['securityNotes'] = link
            json.dump(sort_os_file(None, build_data), build_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
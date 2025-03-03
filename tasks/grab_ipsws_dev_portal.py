#!/usr/bin/env python3

import json
import os
import re
import sys
from pathlib import Path

import dateutil.parser
import lxml.etree
import lxml.html
import requests
import lxml.etree
from lxml.etree import _Element as Element  # pylint: disable=no-name-in-module

# TODO: Probably put import.txt/import.json/import_raw.html in a folder, and put it in .gitignore

# If you have a proxy to access the dev portal, pass it on the command line, set the DEV_PORTAL_PROXY environment variable, or set it here
# Otherwise, leave it blank and save the HTML to import_raw.html
if sys.argv[1:]:
    DEV_PORTAL_PROXY = sys.argv[1].strip()
elif os.environ.get("DEV_PORTAL_PROXY"):
    DEV_PORTAL_PROXY = os.environ["DEV_PORTAL_PROXY"].strip()
else:
    DEV_PORTAL_PROXY = ""  # Set your proxy here

if DEV_PORTAL_PROXY:
    result = requests.get(DEV_PORTAL_PROXY, timeout=30)
    result.raise_for_status()

    Path("import_raw.html").write_bytes(result.content)

    ipsws = re.findall(r"href=\"(.*\.ipsw)\"", result.text)

    Path("import.txt").write_text("\n".join(ipsws), "utf-8", newline="\n")

    element = lxml.html.fromstring(result.text)
else:
    element = lxml.html.fromstring(Path("import_raw.html").read_text("utf-8"))  # result.text)

sections = element.xpath(".//section")
for section in sections:
    if "section-downloads" in section.attrib.get("class", ""):
        element = section
        break

group: Element

out = []

HEADING_PATTERN = re.compile(r"(?P<os_str>^\w+) (?P<version>\d+(\.\d+(\.\d+)?)?)(?P<additional> .+)?")

skip_builds = [
    "20H343", # iOS/iPadOS 16.7.8
    "21G101", # iOS 17.6.1
    "21H414", # iPadOS 17.7.4
    "21H420", # iPadOS 17.7.5
    "22D63", # iOS/iPadOS 18.3
    "22D72", # iOS/iPadOS 18.3.1
    "22E5216h", # iOS/iPadOS 18.4
    "22K557", # tvOS 18.3
    "22L5234e", # tvOS 18.4
    "22N896", # visionOS 2.3
    "22N900", # visionOS 2.3.1
    "22O5215f", # visionOS 2.4
    "22S555", # watchOS 11.3
    "22S560", # watchOS 11.3.1
    "22T5228e", # watchOS 11.4
    "24D60", # macOS 15.3
    "24D70", # macOS 15.3.1
    "24E5222f", # macOS 15.3.1
]

for group in element.xpath(".//h3/.."):
    name: str = group.find("h3", None).text.strip()
    match = HEADING_PATTERN.match(name)
    if not match:
        if name.startswith("Device Support"):
            # Bruh
            continue
        assert match, "Name does not match pattern"
    version = match.groupdict()["version"]
    if "." not in version:
        version += ".0"
    data = {"osStr": match.groupdict()["os_str"], "version": version + (match.groupdict()["additional"] or "").replace("Release Candidate", "RC")}

    build_info_container: list[Element] = group.xpath("./ul[@class='version typography-caption']")
    if not build_info_container:
        continue
    build_info_raw = [i.strip() for i in build_info_container[0].itertext(None) if i.strip()]
    build_info = dict(zip(build_info_raw[::2], build_info_raw[1::2]))
    data.update({i.lower(): v for i, v in build_info.items()})
    if data["build"] in skip_builds: continue

    if "released" in data:
        data["released"] = dateutil.parser.parse(data["released"]).strftime("%Y-%m-%d")

    direct_download = group.xpath("..//a[@class='button direct-download']")
    has_profile_download = bool(direct_download)

    try:
        links: Element = group.xpath(".//div/ul/li/a/../..")[0]
        for i in links.iterchildren(None):
            device = i.find("a", None).text.strip()
            url = i.find("a", None).attrib["href"].strip()
            if url.startswith("/"):
                url = "https://developer.apple.com" + url
            build = i.find("p", None).text.strip()
            if build not in build_info["Build"].split(" | "):
                print(f"WARNING: {build_info["Build"]} isn't the same as {build}, skipping")
                continue

            data.setdefault("links", []).append({"device": device, "url": url, "build": build})
    except IndexError:
        if direct_download and direct_download[0].attrib["href"].endswith('.ipsw'):
            has_profile_download = False
            data.setdefault("links", []).append({"device": 'Mac computers with Apple Silicon', "url": direct_download[0].attrib["href"], "build": build})
        else:
            assert data["osStr"] == "watchOS" or (
                any(("macappstore" in i.get("href") or "apps.apple.com" in i.get("href")) for i in group.findall(".//a"))  # type: ignore
                and data["osStr"] == "macOS"
                and "beta" not in data["version"].lower()
            )

    
    if has_profile_download:
        data["profile_link"] = direct_download[0].attrib["href"]

    out.append(data)

if bool(out):
    print([f"{d['osStr']} {d['version']} ({len(d.get('links', []))})" for d in out])
    [i.unlink() for i in Path.cwd().glob("import.*") if i.is_file()]
    json.dump(out, Path("import.json").open("w", encoding="utf-8"), indent=4)

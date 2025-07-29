#!/usr/bin/env python3

import json
import os
import re
import sys
from pathlib import Path

import dateutil.parser
import lxml.html
import requests
from lxml.etree import _Element as Element  # pylint: disable=no-name-in-module

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
    "19H390", # iOS/iPadOS 15.8.4
    "20H360", # iOS/iPadOS 16.7.11
    "21G101", # iOS 17.6.1
    "21H423", # iPadOS 17.7.6
    "21H446", # iPadOS 17.7.9
    "22F76",  # iOS/iPadOS 18.5
    "22G86", # iOS/iPadOS 18.6
    "22L572", # tvOS 18.5
    "22M84", # tvOS 18.6
    "22O473", # visionOS 2.5
    "22O785", # visionOS 2.6
    "22T572", # watchOS 11.5
    "22U84", # watchOS 11.6
    "24F74",  # macOS 15.5
    "24G84", # macOS 15.6
    # betas
    "23A5297i", # iOS/iPadOS 26
    "23J5316g", # tvOS 26
    "23M5300g", # visionOS 26
    "23R5317g", # watchOS 26
    "25A5316i", # macOS 26
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
    _ = [i.unlink() for i in Path.cwd().glob("import.*") if i.is_file()]
    json.dump(out, Path("import.json").open("w", encoding="utf-8"), indent=4)

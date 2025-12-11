#!/usr/bin/env python3

import json
import os
import re
import sys
import string
from pathlib import Path

import dateutil.parser
import lxml.html
import requests
from lxml.etree import _Element as Element  # pylint: disable=no-name-in-module

HEADERS = {}

# If you have a proxy to access the dev portal, pass it on the command line, set the DEV_PORTAL_PROXY environment variable, or set it here
# Otherwise, leave it blank and save the HTML to import_raw.html
if sys.argv[1:]:
    DEV_PORTAL_PROXY = sys.argv[1].strip()
elif os.environ.get("DEV_PORTAL_PROXY"):
    DEV_PORTAL_PROXY = os.environ["DEV_PORTAL_PROXY"].strip()
else:
    DEV_PORTAL_PROXY = ""  # Set your proxy here

if sys.argv[2:]:
    DEV_AUTH_VALUE = sys.argv[2]
elif os.environ.get("DEV_AUTH_VALUE"):
    DEV_AUTH_VALUE = os.environ["DEV_AUTH_VALUE"].strip()
else:
    DEV_AUTH_VALUE = ""  # Set your value here for an authorization header

if DEV_AUTH_VALUE:
    HEADERS = {"Authorization": DEV_AUTH_VALUE}

if DEV_PORTAL_PROXY:
    result = requests.get(DEV_PORTAL_PROXY, headers=HEADERS, timeout=30)
    result.raise_for_status()

    Path("import_raw.html").write_bytes(result.content)

element = lxml.html.fromstring(Path("import_raw.html").read_text("utf-8"))

sections = element.xpath(".//section")
for section in sections:
    if "section-downloads" in section.attrib.get("class", ""):
        element = section
        break

group: Element

out = []

HEADING_PATTERN = re.compile(r"(?P<os_str>^\w+) (?P<version>\d+(\.\d+(\.\d+)?)?)(?P<additional> .+)?")

skip_builds = [
    "22H124", # iOS/iPadOS 18.7.2
    "23B85", # iOS/iPadOS 26.1
    "23J582", # tvOS 26.1
    "23N49", # visionOS 26.1
    "23S37", # watchOS 26.1
    "25B78", # macOS 26.1
    # betas
    "22H217", # iOS/iPadOS 18.7.3
    "23C52", # iPadOS 26.2
    "23C54", # iOS 26.2
    "23K53", # tvOS 26.2
    "23N301", # visionOS 26.2
    "23S303", # watchOS 26.2
    "25C56", # macOS 26.2
]

for group in element.xpath(".//h3/.."):
    name: str = group.find("h3", None).text.strip()
    match = HEADING_PATTERN.match(name)
    if not match:
        if name.startswith("Device Support"):
            # Bruh
            continue
        assert match, f"Name does not match pattern: {name}"
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
            # HACK: dev portal builds are inconsistent
            if build[2] not in string.ascii_uppercase:
                build = build[1:]
            if build not in build_info["Build"].split(" | "):
                print(f"WARNING: {build_info['Build']} isn't the same as {build} ({device}), skipping")
                continue

            # HACK: dev portal links are inconsistent
            if url.startswith('hhttp'):
                url = url[1:]
            elif url.startswith('ttp'):
                url = f"h{url}"

            data.setdefault("links", []).append({"device": device, "url": url, "build": build})
    except IndexError:
        if direct_download and direct_download[0].attrib["href"].endswith('.ipsw'):
            has_profile_download = False
            data.setdefault("links", []).append({"device": 'Mac computers with Apple Silicon', "url": direct_download[0].attrib["href"].replace("hhttp", "http"), "build": build})
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

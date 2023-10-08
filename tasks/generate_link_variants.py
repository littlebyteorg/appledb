#!/usr/bin/env python3

import json
import time
from pathlib import Path
from typing import Collection

from sort_os_files import sort_os_file

# TODO: Move this to separate file so that all domain information is in one place
# Preferred -> other variants
rewrite_map_v2 = {
    "https://updates.cdn-apple.com/": ["http://updates-http.cdn-apple.com/"],
    "https://mesu.apple.com/": ["http://mesu.apple.com/"],
    "https://secure-appldnld.apple.com/": ["http://appldnld.apple.com/"],
    "https://developer.apple.com/services-account/download?path=/": [
        "https://download.developer.apple.com/",
        "http://adcdownload.apple.com/",
    ],
    "https://swcdn.apple.com/": ["http://swcdn.apple.com/"],
    "http://a1408.g.akamai.net/": [],
    "https://download.info.apple.com/": ["http://download.info.apple.com/"],
    "https://support.apple.com/downloads/": ["http://support.apple.com/downloads/"],
    "https://devimages-cdn.apple.com/": ["http://devimages-cdn.apple.com/"],
    # It's archive.org
    "https://archive.org/": [],
    # Placeholder because APPX links expire
    "https://apps.microsoft.com/": [],
}


def appendable(iterable, link):
    # Only append if it's not already in the list

    for i, existing_link in enumerate(iterable):
        if link["url"] == existing_link["url"]:
            break
    else:
        # No existing link, append it
        iterable.append(link)


# We use this to set up the sort order for hosts (first the preferred host, then the other hosts in order)
url_host_sorted = []
for preferred_host, other_hosts in rewrite_map_v2.items():
    url_host_sorted.append(preferred_host)
    url_host_sorted.extend(other_hosts)


def get_host(url: str):
    for preferred_host, alternative_hosts in rewrite_map_v2.items():
        if url.startswith(preferred_host):
            return preferred_host
        for alternative_host in alternative_hosts:
            if url.startswith(alternative_host):
                return alternative_host

    assert False, f"Could not find host for {url}"
    return None


def get_preferred_host(url: str):
    for preferred_host, alternative_hosts in rewrite_map_v2.items():
        if url.startswith(preferred_host):
            return preferred_host
        for alternative_host in alternative_hosts:
            if url.startswith(alternative_host):
                return preferred_host

    assert False, f"Could not find preferred host for {url}"
    return None


def get_host_group(url: str):
    preferred_host = get_preferred_host(url)
    return [preferred_host] + rewrite_map_v2[preferred_host]


def rewrite_links(links: list[dict]):
    if not links:
        return links

    new_links = links.copy()

    for link in links:
        # Remove preferred if it's for some reason present
        if "preferred" in link:
            del link["preferred"]

        current_host = get_host(link["url"])
        if not current_host:
            # No host found, skip
            appendable(new_links, link)
            continue

        path = link["url"].replace(current_host, "", 1)
        for host in get_host_group(link["url"]):
            appendable(new_links, {**link, "url": host + path})

    def get_sort_order(link):
        # Sort by host order. If not in host order, put at bottom in original order

        # Special casing for InstallAssistants from catalogs
        catalog_position = None
        catalog_order = ["dev-beta", "public-beta"]
        if "catalog" in link:
            catalog_position = catalog_order.index(link["catalog"])
        else:
            catalog_position = len(catalog_order)

        host_order = url_host_sorted.index(get_host(link["url"]))

        return catalog_position, host_order

    new_links.sort(key=get_sort_order)

    for link in new_links:
        if link["url"].startswith(get_preferred_host(link["url"])):
            link["preferred"] = True
            break

    for link in new_links:
        if "preferred" not in link:
            link["preferred"] = False

    if links:
        # Top link should be preferred
        assert new_links[0]["preferred"], new_links
        # There should only be one preferred link
        assert len([i for i in new_links if i["preferred"]]) == 1, new_links

    return new_links


def process_file(ios_file: Path):
    data = json.loads(ios_file.read_text())

    for source in data.get("sources", []):
        links = source.setdefault("links", [])
        new_links = rewrite_links(links)
        source["links"] = new_links

    for entry in data.get("createDuplicateEntries", []):
        for source in entry.get("sources", []):
            links = source.setdefault("links", [])
            new_links = rewrite_links(links)
            source["links"] = new_links

    json.dump(sort_os_file(None, raw_data=data), ios_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)


def generate_link_variants(files: Collection[Path]):
    total = len(files)

    start = time.time()
    for i, file in enumerate(files):  # pylint: disable=unused-variable
        try:
            process_file(file)
        except Exception:
            print(f"Error while processing {file}")
            raise
        # print(f"Processed {i+1}/{total} ({(i+1)/total*100:.2f}%) files")

    end = time.time()

    print(f"Processed {total} files in {end-start} seconds")


if __name__ == "__main__":
    generate_link_variants(list(Path("osFiles").rglob("*.json")))

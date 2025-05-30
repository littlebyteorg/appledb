#!/usr/bin/env python3

import json
import time
from pathlib import Path
from typing import Collection

from sort_os_files import sort_os_file
from link_info import rewrite_map_v2, needs_apple_auth

def appendable(iterable, link):
    # Only append if it's not already in the list

    for existing_link in iterable:
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
    for preferred, alternatives in rewrite_map_v2.items():
        if url.startswith(preferred):
            return preferred
        for alternative in alternatives:
            if url.startswith(alternative):
                return alternative

    assert False, f"Could not find host for {url}"
    return None


def get_preferred_host(url: str):
    for preferred, alternatives in rewrite_map_v2.items():
        if url.startswith(preferred):
            return preferred
        for alternative in alternatives:
            if url.startswith(alternative):
                return preferred

    assert False, f"Could not find preferred host for {url}"
    return None


def get_host_group(url: str):
    preferred = get_preferred_host(url)
    return [preferred] + rewrite_map_v2[preferred]


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
        for hostname in needs_apple_auth:
            if hostname in current_host:
                link["auth"] = True
                break
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

    has_existing_active_link = bool([x for x in links if x['active']])
    preferred_link_override = False

    for link in new_links:
        if link["url"].startswith(get_preferred_host(link["url"])):
            if has_existing_active_link and not link["active"]:
                preferred_link_override = True
            else:
                link["preferred"] = True
            break

    for link in new_links:
        if "preferred" not in link:
            if preferred_link_override and link["active"]:
                link["preferred"] = True
                preferred_link_override = False
            else:
                link["preferred"] = False

    if links:
        new_links.sort(key=lambda x: x['preferred'], reverse=True)
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

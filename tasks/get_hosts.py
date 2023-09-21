import json
from pathlib import Path
from urllib.parse import urlparse

hosts = set()

for file in Path("osFiles").rglob("*.json"):
    data = json.load(file.open())
    for source in data.get("sources", []):
        links = source.get("links", [])
        if not links:
            continue

        for link in links:
            url = urlparse(link["url"])
            hosts.add(url.netloc)

print("\n".join(sorted(hosts)))

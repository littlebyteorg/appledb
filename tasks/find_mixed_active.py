import json
from pathlib import Path

files = []

for file in Path("osFiles").rglob("*.json"):
    data = json.load(file.open())
    for source in data.get("sources", []):
        links = source.get("links", [])
        if not links:
            continue

        links = [i for i in links if "appldnld.apple.com" not in i["url"]]

        if len(set(link["active"] for link in links)) > 1:
            print(f"Found mixed active/inactive links in {file}")
            for link in links:
                print(f"\t{link['url']}: {'active' if link['active'] else 'inactive'}")
            files.append(file)
            continue

        # secure_link = next((link for link in links if "/secure-appldnld.apple.com" in link["url"]), None)
        # if not secure_link:
        #     continue
        # if not secure_link["active"]:
        #     continue
        # insecure_link = next((link for link in links if "/appldnld.apple.com" in link["url"]), None)
        # if not insecure_link:
        #     print(f"Found secure link but no insecure link in {file}")
        #     print(f"Secure link: {secure_link}")
        #     continue
        # if insecure_link["active"]:
        #     continue
        # print("Found active secure link and inactive insecure link in {file}")
        # print(f"Secure link: {secure_link}")
        # print(f"Insecure link: {insecure_link}")

print(json.dumps(sorted(set(files)), indent=4, default=str))

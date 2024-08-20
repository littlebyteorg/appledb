#!/usr/bin/env python3

import plistlib
from pathlib import Path
import random

import requests

urls = [
    "https://mesu.apple.com/assets/audio/com_apple_MobileAsset_SoftwareUpdate/com_apple_MobileAsset_SoftwareUpdate.xml",
    "https://mesu.apple.com/assets/com_apple_MobileAsset_SoftwareUpdate/com_apple_MobileAsset_SoftwareUpdate.xml"
]

ota_links=set()

for url in urls:
    response = requests.get(url + f"?cachebust{random.randint(100, 1000)}", timeout=30)
    response.raise_for_status()

    assets = plistlib.loads(response.content)['Assets']

    for asset in assets:
        ota_links.add(f"{asset['__BaseURL']}{asset['__RelativePath']}")

[i.unlink() for i in Path.cwd().glob("import-ota.*") if i.is_file()]
Path("import-ota.txt").write_text("\n".join(sorted(ota_links)), "utf-8")
#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--files", nargs="+")
args = parser.parse_args()

for file in args.files or Path(".").rglob("*.json"):
    relative_path = str(file)
    if relative_path.startswith('out') or relative_path.startswith('node_modules'): continue
    try:
        json.load(Path(file).open(encoding="utf-8"))
    except:
        print(f"Error while processing {file}")
        raise

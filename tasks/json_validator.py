import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--files", nargs="+")
args = parser.parse_args()

if args.files:
    for file in args.files:
        try:
            json.load(Path(file).open(encoding="utf-8"))
        except:
            print(f"Error while processing {file}")
            raise
else:
    for file in Path("appledb-web").rglob("*.json"):
        try:
            json.load(Path(file).open(encoding="utf-8"))
        except:
            print(f"Error while processing {file}")
            raise

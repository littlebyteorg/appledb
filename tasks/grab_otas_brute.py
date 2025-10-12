from pathlib import Path
import argparse
import base64
import json
import requests
import urllib3

# Disable SSL warnings, because Apple's SSL is broken
urllib3.disable_warnings()

session = requests.session()

previously_checked = set()

asset_audiences = json.load(Path("tasks/audiences.json").open(encoding="utf-8"))

asset_audiences_overrides = {
    'iPadOS': 'iOS'
}

def call_pallas(board_id, os_build, os_str, audience, identifier, product_version, counter=5):
    asset_type = 'SoftwareUpdate'
    if os_str == 'macOS':
        asset_type = 'Mac' + asset_type

    request = {
        "ClientVersion": 2,
        "CertIssuanceDay": "2023-12-10",
        "AssetType": f"com.apple.MobileAsset.{asset_type}",
        "AssetAudience": audience,
        "ProductType": identifier,
        "ProductVersion": product_version,
        "HWModelStr": board_id,
        "BuildVersion": os_build
    }
    # print(json.dumps(request))

    response = session.post("https://gdmf.apple.com/v2/assets", json=request, headers={"Content-Type": "application/json"}, verify=False)

    try:
        response.raise_for_status()
    except Exception:
        if counter == 0:
            print(request)
            raise
        return call_pallas(board_id, os_build, os_str, audience, identifier, product_version, counter - 1)

    parsed_response = json.loads(base64.b64decode(response.text.split('.')[1] + '==', validate=False))
    for asset in parsed_response['Assets']:
        if not asset.get('PrerequisiteBuild'): continue
        # print(asset.keys())
        print(f"{asset['PrerequisiteOSVersion']} ({asset['PrerequisiteBuild']})")
        break

choice_list = list(asset_audiences.keys())
choice_list.extend(list(asset_audiences_overrides.keys()))

parser = argparse.ArgumentParser()
parser.add_argument('-b', '--boards', nargs="+", required=True)
parser.add_argument('-f', '--forks', nargs="+", type=int, required=True)
parser.add_argument('-i', '--identifiers', nargs="+", required=True)
parser.add_argument('-o', '--os', choices=choice_list, required=True)
parser.add_argument('-p', '--build-prefix', required=True)
parser.add_argument('-r', '--range', nargs='+', type=int, required=True)
parser.add_argument('-v', '--versions', nargs='+', required=True)
args = parser.parse_args()
if len(args.range) != 2:
    raise argparse.ArgumentTypeError("Must be exactly two values for range")
if len(args.boards) != len(args.identifiers):
    raise argparse.ArgumentTypeError("Same number of boards and identifiers must be passed in")

board_identifier_map = dict(zip(args.boards, args.identifiers))

for fork in args.forks:
    if fork == 0:
        start_range = args.range[0]
        end_range = args.range[1]
    else:
        start_range = int(f"{fork}{args.range[0]:03d}")
        end_range = int(f"{fork}{args.range[1]:03d}")

    asset_audience = asset_audiences[asset_audiences_overrides.get(args.os, args.os)]['release']

    for build in range(start_range, end_range+1):
        for board, identifier in board_identifier_map.items():
            for version in args.versions:
                call_pallas(board, f"{args.build_prefix}{build}", args.os, asset_audience, identifier, version)
import datetime
import gzip
import json
import zoneinfo
from pathlib import Path

import dateutil
import dateutil.parser


def check_duplicate_keys(oses: list[dict]):
    failed = False

    seen = set()
    for os in oses:
        if os["key"] in seen:
            print(f"Duplicate key {os['key']}")
            failed = True
        seen.add(os["key"])

    return failed


def check_duplicate_hashes(oses: list[dict]):
    failed = False

    seen = {}
    for os in oses:
        for source in os.get("sources", []):
            for hash_type, hash_value in source.get("hashes", {}).items():
                seen.setdefault((hash_type, hash_value), {}).setdefault((source["type"], source.get("size")), set()).add(os["key"])

    for (hash_type, hash_value), sources in seen.items():
        if len(sources) > 1:
            print(f"Duplicate hash {hash_type} {hash_value} found:")
            for source in sources:
                print(f" - {source}: {', '.join(sorted(sources[source]))}")
            failed = True

    return failed


def check_map_consistency(os: dict):
    failed = False

    for key in ["deviceMap", "osMap"]:
        if key not in os:
            continue

        from_root = set(os[key])
        for i, source in enumerate(os.get("sources", [])):
            from_source = set(source.get(key, set()))
            if from_source - from_root:
                print(f"Mismatch for {key} in {os['key']}: extra {'/'.join(sorted(from_source - from_root))} found in source {i}")
                failed = True

    return failed


def check_beta_rc_consistency(os: dict):
    if os["beta"] and os["rc"]:
        print(f"Both beta and rc are true for {os['key']}")
        return True

    return False


def check_release_date(os: dict):
    if os.get("released"):
        try:
            parsed = dateutil.parser.parse(os["released"])
        except Exception as e:
            print(f"Release date {os['released']} for {os['key']} is not parseable: {e}")
            return True
        now = datetime.datetime.now(tz=zoneinfo.ZoneInfo("America/Los_Angeles"))
        future = (parsed > now) if parsed.tzinfo else (parsed.replace(tzinfo=zoneinfo.ZoneInfo("America/Los_Angeles")) > now)
        if future:
            print(f"Release date {os['released']} for {os['key']} is in the future")
            return True

    return False


def check_placeholders(os: dict):
    if "FIXME" in os["version"] or "YYYY-MM-DD" in os.get("released", ""):
        print(f"Placeholder in {os['version']} for {os['key']}")
        return True
    return False


def main():
    oses: list[dict] = json.loads(gzip.decompress(Path("out/ios/main.json.gz").read_bytes()))

    failed = False

    # Must be first because we use keys as unique values in later checks
    failed |= check_duplicate_keys(oses)
    failed |= check_duplicate_hashes(oses)
    for os in oses:
        failed |= check_map_consistency(os)
        failed |= check_beta_rc_consistency(os)
        failed |= check_placeholders(os)
        failed |= check_release_date(os)

    print(f"Validation {'failed' if failed else 'succeeded'}")
    if failed:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()

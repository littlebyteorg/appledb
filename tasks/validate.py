import datetime
import gzip
import json
import zoneinfo
from pathlib import Path

import dateutil
import dateutil.parser


NOW = datetime.datetime.now(tz=zoneinfo.ZoneInfo("America/Los_Angeles"))
FUTURE_THRESHOLD = datetime.timedelta(days=40)


def force_tz(dt: datetime.datetime):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=zoneinfo.ZoneInfo("America/Los_Angeles"))
    return dt


def check_duplicate_keys(items: list[dict]):
    failed = False

    seen = set()
    for item in items:
        if item["key"] in seen:
            print(f"Duplicate key {item['key']}")
            failed = True
        seen.add(item["key"])

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


def check_release_date_os(os: dict):
    if os.get("released"):
        try:
            parsed = dateutil.parser.parse(os["released"])
        except Exception as e:
            print(f"Release date {os['released']} for {os['key']} is not parseable: {e}")
            return True
        future = force_tz(parsed) > NOW
        if future and not os.get("preinstalled"):
            print(f"Release date {os['released']} for {os['key']} is in the future")
            return True

    return False


def check_placeholders(os: dict):
    if "FIXME" in os["version"] or "YYYY-MM-DD" in os.get("released", ""):
        print(f"Placeholder in {os['version']} for {os['key']}")
        return True
    return False


def check_release_date_device(device: dict):
    failed = False
    released = device.get("released")

    if not released:
        return False

    if isinstance(released, str):
        released = [released]

    earliest = NOW
    threshold = NOW + FUTURE_THRESHOLD

    for date_str in released:
        try:
            parsed = dateutil.parser.parse(date_str)
            earliest = min(earliest, force_tz(parsed))
        except Exception as e:
            print(f"Release date {date_str} for {device['key']} is not parseable: {e}")
            failed = True
            continue
        future = force_tz(parsed) > threshold
        if future and not device.get("preinstalled"):
            print(f"Release date {date_str} for {device['key']} is too far in the future")
            failed = True

    if failed:
        return failed

    for color in device.get("colors", []):
        if "released" in color:
            try:
                color_parsed = dateutil.parser.parse(color["released"])
            except Exception as e:
                print(f"Release date {color['released']} for color {color.get('name', 'unknown')} of {device['key']} is not parseable: {e}")
                failed = True
                continue
            color_past = force_tz(color_parsed) < earliest
            if color_past:
                print(
                    f"Release date {color['released']} for color {color.get('name', 'unknown')} of {device['key']} is before device release date {device['released']}"
                )
                failed = True
            color_future = force_tz(color_parsed) > threshold
            if color_future:
                print(
                    f"Release date {color['released']} for color {color.get('name', 'unknown')} of {device['key']} is too far in the future"
                )
                failed = True

    return failed


def main():
    oses: list[dict] = json.loads(gzip.decompress(Path("out/ios/main.json.gz").read_bytes()))
    devices: list[dict] = json.loads(gzip.decompress(Path("out/device/main.json.gz").read_bytes()))

    failed = False

    # Must be first because we use keys as unique values in later checks
    failed |= check_duplicate_keys(oses)
    failed |= check_duplicate_keys(devices)

    failed |= check_duplicate_hashes(oses)
    for os in oses:
        failed |= check_map_consistency(os)
        failed |= check_beta_rc_consistency(os)
        failed |= check_placeholders(os)
        failed |= check_release_date_os(os)

    for device in devices:
        failed |= check_release_date_device(device)

    print(f"Validation {'failed' if failed else 'succeeded'}")
    if failed:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()

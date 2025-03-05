import datetime
import json
import urllib
import urllib.parse
import zoneinfo
from pathlib import Path

import dateutil.parser
from ics import Calendar, Event

DATA = json.loads(Path("out/iOS/main.json").read_bytes())
CUPERTINO = zoneinfo.ZoneInfo("America/Los_Angeles")


def process_event(data: dict, all_day: bool = True):
    DATE_THRESHOLD = datetime.datetime(1970, 1, 1) if all_day else datetime.datetime(1970, 1, 1, 10, 0, 0, tzinfo=CUPERTINO)
    # DATE_THRESHOLD = datetime.datetime(2024, 1, 1) if all_day else datetime.datetime(2024, 1, 1, 10, 0, 0, tzinfo=CUPERTINO)

    if not data.get("released"):
        return

    event = Event()
    event.name = f"{data['osStr']} {data['version']}"
    if data.get("build"):
        event.name += f" ({data['build']})"

    event.uid = data["key"]

    event.description = f"""
{data['osStr']} {data['version']}{f" ({data['build']})" if data.get("build") else ""}

Released on {data['released']}.

"""

    if data.get("deviceMap"):
        event.description += "Supported devices:\n"
        event.description += ", ".join(data["deviceMap"])
        event.description += "\n\n"

    if data.get("osMap"):
        event.description += "Supported OSes:\n"
        event.description += ", ".join(data["osMap"])
        event.description += "\n\n"

    if data.get("preinstalled"):
        if isinstance(data["preinstalled"], list):
            event.description += "This build is preinstalled on the following devices:\n"
            event.description += ", ".join(data["preinstalled"])
            event.description += "\n\n"
        else:
            event.description += "This build is a preinstalled build on all devices it was available for.\n\n"

    if data.get("internal"):
        event.description += "This is an internal build.\n"
    # if data.get("simulator"):
    #     event.description += "This is a simulator build.\n"
    if data.get("sdk"):
        event.description += "This is an SDK build.\n"
    if data.get("beta"):
        event.description += "This is a beta build.\n"
    if data.get("rc"):
        event.description += "This is a release candidate build.\n"
    if data.get("rsr"):
        event.description += "This is a Rapid Security Response.\n"

    event.description = event.description.strip()

    event.url = data["appledburl"]

    if len(data["released"]) < 10:
        # print(data)
        return

    # released = datetime.datetime.fromisoformat(data["released"])
    released = dateutil.parser.parse(data["released"])

    if all_day:
        if released.tzinfo:
            released = released.astimezone(CUPERTINO)
            released = released.replace(tzinfo=None)
        if released < DATE_THRESHOLD:
            return
        event.begin = released
        event.end = released
        event.make_all_day()
    else:
        if not released.tzinfo:
            released = released.replace(hour=10, minute=0, second=0, tzinfo=CUPERTINO)
        if released < DATE_THRESHOLD:
            return
        event.begin = released
        event.end = released

    event.transparent = True

    return event


README = """
# Calendars

Calendars generated based on released firmwares in AppleDB.

"""


def generate(all_day: bool = True):
    global README

    main_calendar = Calendar()
    calendars = {}

    if all_day:
        README += """## All Day Events

The events in these calendars are marked as all day.

"""
    else:
        README += """## Time-Based Events

The events in these calendars are marked as starting and ending at 10AM Cupertino time.

"""

    for i in DATA:
        # Create calendars for this osType
        # This is before event creation, so that we can ensure there are calendars for all osTypes,
        # even if they will be empty
        if i["osType"] not in calendars:
            calendars[i["osType"]] = Calendar()

        event = process_event(i, all_day)
        if not event:
            continue

        main_calendar.events.add(event)
        calendars[i["osType"]].events.add(event)

    main_path = Path(f"out/iOS/main{'-timed' if not all_day else ''}.ics")
    main_path.write_text(main_calendar.serialize())
    main_url = f"https://api.appledb.dev/{urllib.parse.quote(str(main_path.relative_to(Path('out'))))}"
    README += f"- [Main Calendar]({main_url})\n"

    def sort_key(x):
        try:
            index = [
                "iOS",
                "macOS",
                "tvOS",
                "watchOS",
                "HomePod Software",
                "visionOS",
                "bridgeOS",
                "Xcode",
                "Safari",
                "Bluetooth Headset Firmware",
                "Rosetta",
            ].index(x)
        except ValueError:
            index = 99

        return (index, x)

    for i in sorted(calendars.keys(), key=sort_key):
        calendar_path = Path(f"out/iOS/{i}/main{'-timed' if not all_day else ''}.ics")
        calendar_path.write_text(calendars[i].serialize())
        calendar_url = f"https://api.appledb.dev/{urllib.parse.quote(str(calendar_path.relative_to(Path('out'))))}"
        README += f"- [{i}]({calendar_url})\n"

    README += "\n"


if __name__ == "__main__":
    generate(True)
    generate(False)
    Path("out/CALENDARS.md").write_text(README, encoding="utf-8")

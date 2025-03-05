import datetime
import json
import urllib
import urllib.parse
import zoneinfo
from pathlib import Path
from typing import Optional

import dateutil.parser
from ics import Calendar, Event

FIRMWARE_DATA = json.loads(Path("out/ios/main.json").read_bytes())
DEVICE_DATA = json.loads(Path("out/device/main.json").read_bytes())
CUPERTINO = zoneinfo.ZoneInfo("America/Los_Angeles")


def handle_date(event: Event, date: str, all_day: bool):
    released = dateutil.parser.parse(date)

    if all_day:
        if released.tzinfo:
            released = released.astimezone(CUPERTINO)
            released = released.replace(tzinfo=None)
        event.begin = released
        event.end = released
        event.make_all_day()
    else:
        if not released.tzinfo:
            released = released.replace(hour=10, minute=0, second=0, tzinfo=CUPERTINO)
        event.begin = released
        event.end = released


def process_firmware_event(data: dict, all_day: bool = True):
    if not data.get("released"):
        return

    event = Event()
    event.name = f"{data['osStr']} {data['version']}"
    if data.get("build"):
        event.name += f" ({data['build']})"

    event.uid = "FIRMWARE;" + data["key"]

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
        if data["preinstalled"] == data["deviceMap"]:
            event.description += "This build is a preinstalled build on all devices it was available for.\n\n"
        else:
            event.description += "This build is preinstalled on the following devices:\n"
            event.description += ", ".join(data["preinstalled"])
            event.description += "\n\n"

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
    handle_date(event, data["released"], all_day)

    event.transparent = True

    return [event]


def process_device_event(data: dict, all_day: bool = True):
    release_dates = data.get("released")
    if not release_dates:
        return
    elif isinstance(release_dates, str):
        release_dates = [release_dates]

    multiple = len(release_dates) > 1
    discontinued = data.get("discontinued")

    events = []
    for i, release_date in enumerate(release_dates):
        event = Event()
        event.name = f"{data['name']} release"
        if multiple:
            event.name += f" ({i + 1}/{len(release_dates)})"

        event.uid = ";".join(["DEVICE;", data["key"], release_date])

        event.description = f"""
{data['name']} release{f" ({i + 1}/{len(release_dates)})" if multiple else ""}.
"""
        if len(release_date) < 10:
            print(data)
            return

        handle_date(event, release_date, all_day)

        events.append(event)

    if discontinued:
        event = Event()
        event.name = f"{data['name']} discontinued"

        event.uid = ";".join(["DEVICE;", data["key"], discontinued])

        event.description = f"""
{data['name']} discontinued.
"""
        if len(discontinued) < 10:
            print(data)
            return

        handle_date(event, discontinued, all_day)

        events.append(event)

    for event in events:
        event.description += f"""
Released on {', '.join(release_dates)}.{(' Discontinued on ' + data['discontinued'] + '.') if data.get('discontinued') else ''}

Type: {data['type']}

"""

        if data.get("model"):
            event.description += "Models:\n"
            event.description += ", ".join(data["model"])
            event.description += "\n\n"

        if data.get("identifier"):
            event.description += "Identifiers:\n"
            event.description += ", ".join(data["identifier"])
            event.description += "\n\n"

        if data.get("board"):
            event.description += "Boardconfigs:\n"
            event.description += ", ".join(data["board"])
            event.description += "\n\n"

        if data.get("internal"):
            event.description += "This is an internal device.\n"

        event.description = event.description.strip()

        event.url = f"https://appledb.dev/device/identifier/{data['key'].replace(' ', '-').replace('/', '-')}"

        event.transparent = True

    # TODO: List
    return events


def generate():
    README = """
# Calendars

Calendars generated based on released firmwares and devices in AppleDB.

All day calendars have events marked as taking place all day, while time-based calendars have events
marked as starting and ending at 10AM Cupertino time.

    """

    all_day_calendars = {
        "all": Calendar(),
        "all_firmware": Calendar(),
        "all_device": Calendar(),
        "firmwares": {},
        "devices": {},
    }

    timed_calendars = {
        "all": Calendar(),
        "all_firmware": Calendar(),
        "all_device": Calendar(),
        "firmwares": {},
        "devices": {},
    }

    for all_day, calendars in [(True, all_day_calendars), (False, timed_calendars)]:
        for i in FIRMWARE_DATA:
            # Create calendars for this osType
            # This is before event creation, so that we can ensure there are calendars for all osTypes,
            # even if they will be empty
            if i["osType"] not in calendars["firmwares"]:
                calendars["firmwares"][i["osType"]] = Calendar()

            events = process_firmware_event(i, all_day)
            if not events:
                continue

            calendars["all"].events.update(events)
            calendars["all_firmware"].events.update(events)
            calendars["firmwares"][i["osType"]].events.update(events)

        for i in DEVICE_DATA:
            # Create calendars for this type
            # This is before event creation, so that we can ensure there are calendars for all types,
            # even if they will be empty
            if i["type"] not in calendars["devices"]:
                calendars["devices"][i["type"]] = Calendar()

            events = process_device_event(i, all_day)
            if not events:
                continue

            calendars["all"].events.update(events)
            calendars["all_device"].events.update(events)
            calendars["devices"][i["type"]].events.update(events)

    def path_to_url(path: Path) -> str:
        return f"https://api.appledb.dev/{str(path.relative_to(Path('out')))}"

    def save_calendar(all_day_calendar: Calendar, timed_calendar: Calendar, path: Path):
        (path / "main.ics").write_text(all_day_calendar.serialize())
        (path / "main-timed.ics").write_text(timed_calendar.serialize())

        return f"[all day]({path_to_url(path / 'main.ics')}) | [time-based]({path_to_url(path / 'main-timed.ics')})"

    README += f"""## All

- All (devices & firmwares): {save_calendar(all_day_calendars["all"], timed_calendars["all"], Path("out"))}
- Firmwares: {save_calendar(all_day_calendars["all_firmware"], timed_calendars["all_firmware"], Path("out/ios"))}
- Devices: {save_calendar(all_day_calendars["all_device"], timed_calendars["all_device"], Path("out/device"))}

"""

    def sort_firmware_key(x):
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

    # TODO: Sort device key

    README += "## Firmwares\n\n"

    for i in sorted(all_day_calendars["firmwares"], key=sort_firmware_key):
        README += f"- {i}: {save_calendar(all_day_calendars['firmwares'][i], timed_calendars['firmwares'][i], Path(f'out/ios/{i}'))}\n"

    # README += "\n## Devices\n\n"
    # for i in sorted(all_day_calendars["devices"]):
    #     README += f"- {i}: {save_calendar(all_day_calendars['devices'][i], timed_calendars['devices'][i], Path(f'out/device/{i}'))}\n"

    README += "\n"

    Path("out/CALENDARS.md").write_text(README, encoding="utf-8")


if __name__ == "__main__":
    generate()

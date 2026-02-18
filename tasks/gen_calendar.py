import json
import urllib.parse
import zoneinfo
from pathlib import Path

import dateutil.parser
from icalendar import Calendar, Event

FIRMWARE_DATA = json.loads(Path("out/ios/main.json").read_bytes())
DEVICE_DATA = json.loads(Path("out/device/main.json").read_bytes())
CUPERTINO = zoneinfo.ZoneInfo("America/Los_Angeles")


def handle_date(event: Event, date: str, all_day: bool):
    released = dateutil.parser.parse(date)

    if all_day:
        if released.tzinfo:
            released = released.astimezone(CUPERTINO)
            released = released.replace(tzinfo=None)
        event.add("dtstart", released.date())
    else:
        if not released.tzinfo:
            released = released.replace(hour=10, minute=0, second=0, tzinfo=CUPERTINO)
        event.add("dtstart", released)
        event.add("dtend", released)


def process_firmware_event(data: dict, all_day: bool = True):
    if not data.get("released"):
        return

    event = Event()
    name = f"{data['osStr']} {data['version']}"
    if data.get("build"):
        name += f" ({data['build']})"

    event.add("summary", name)

    event.add("uid", "APPLEDB;FIRMWARE;" + data["key"])

    description = f"""
{data["osStr"]} {data["version"]}{f" ({data['build']})" if data.get("build") else ""}

Released on {data["released"]}.

"""

    if data.get("deviceMap"):
        description += "Supported devices:\n"
        description += ", ".join(data["deviceMap"])
        description += "\n\n"

    if data.get("osMap"):
        description += "Supported OSes:\n"
        description += ", ".join(data["osMap"])
        description += "\n\n"

    if data.get("preinstalled"):
        if data["preinstalled"] == data["deviceMap"]:
            description += "This build is a preinstalled build on all devices it was available for.\n\n"
        else:
            description += "This build is preinstalled on the following devices:\n"
            description += ", ".join(data["preinstalled"])
            description += "\n\n"

    if data.get("internal"):
        description += "This is an internal build.\n"
    # if data.get("simulator"):
    #     description += "This is a simulator build.\n"
    if data.get("sdk"):
        description += "This is an SDK build.\n"
    if data.get("beta"):
        description += "This is a beta build.\n"
    if data.get("rc"):
        description += "This is a release candidate build.\n"
    if data.get("rsr"):
        description += "This is a Rapid Security Response.\n"
    if data.get("bsi"):
        description += "This is a Background Security Improvement.\n"

    description = description.strip()

    description += "\n\n" + data["appledburl"]

    event.add("description", description)

    # event.add("url", data["appledburl"])

    if len(data["released"]) < 10:
        # print(data)
        return

    handle_date(event, data["released"], all_day)

    event.add("transp", "TRANSPARENT")

    return [event]


def process_device_event(data: dict, all_day: bool = True):
    release_dates = data.get("released")
    if not release_dates:
        return
    elif isinstance(release_dates, str):
        release_dates = [release_dates]

    multiple = len(release_dates) > 1
    discontinued = data.get("discontinued")

    events: list[Event] = []
    for i, release_date in enumerate(release_dates):
        event = Event()
        name = f"{data['name']} release"
        if multiple:
            name += f" ({i + 1}/{len(release_dates)})"

        event.add("summary", name)

        event.add("uid", "-".join(["APPLEDB", "DEVICE", data["key"], release_date]))

        event.add(
            "description",
            f"""
{data["name"]} release{f" ({i + 1}/{len(release_dates)})" if multiple else ""}.
""",
        )
        if len(release_date) < 10:
            print(data)
            return

        handle_date(event, release_date, all_day)

        events.append(event)

    if discontinued:
        event = Event()
        event.add("summary", f"{data['name']} discontinued")

        event.add("uid", "-".join(["APPLEDB", "DEVICE", data["key"], discontinued]))

        event.add(
            "description",
            f"""
{data["name"]} discontinued.
""",
        )
        if len(discontinued) < 10:
            print(data)
            return

        handle_date(event, discontinued, all_day)

        events.append(event)

    for event in events:
        description = (
            event.pop("description", "")
            + f"""
Released on {", ".join(release_dates)}.{(" Discontinued on " + data["discontinued"] + ".") if data.get("discontinued") else ""}

Type: {data["type"]}

"""
        )

        if data.get("model"):
            description += "Models:\n"
            description += ", ".join(data["model"])
            description += "\n\n"

        if data.get("identifier"):
            description += "Identifiers:\n"
            description += ", ".join(data["identifier"])
            description += "\n\n"

        if data.get("board"):
            description += "Boardconfigs:\n"
            description += ", ".join(data["board"])
            description += "\n\n"

        if data.get("internal"):
            description += "This is an internal device.\n"

        description = description.strip()

        description += "\n\n" + f"https://appledb.dev/device/identifier/{data['key'].replace(' ', '-').replace('/', '-')}"

        event.add("description", description)

        # event.add("url", f"https://appledb.dev/device/identifier/{data['key'].replace(' ', '-').replace('/', '-')}")

        event.add("transp", "TRANSPARENT")

    # TODO: List
    return events


def new_calendar(name: str, description: str) -> Calendar:
    cal = Calendar()
    cal.add("name", name)
    cal.add("X-WR-CALNAME", name)
    cal.add("timezone-id", "America/Los_Angeles")
    cal.add("X-WR-TIMEZONE", "America/Los_Angeles")
    cal.add("prodid", "-//AppleDB//AppleDB//EN")
    cal.add("version", "2.0")
    return cal


def generate():
    README = """
# Calendars

Calendars generated based on released firmwares and devices in AppleDB.

All day calendars have events marked as taking place all day, while time-based calendars have events
marked as starting and ending at 10AM Cupertino time.

"""

    all_day_calendars = {
        "all": new_calendar("AppleDB", "AppleDB device and firmware calendar."),
        "all_firmware": new_calendar("AppleDB - Firmware", "AppleDB firmware calendar."),
        "all_device": new_calendar("AppleDB - Devices", "AppleDB device calendar."),
        "firmwares": {},
        "devices": {},
    }

    timed_calendars = {
        "all": new_calendar("AppleDB", "AppleDB device and firmware calendar."),
        "all_firmware": new_calendar("AppleDB - Firmware", "AppleDB firmware calendar."),
        "all_device": new_calendar("AppleDB - Devices", "AppleDB device calendar."),
        "firmwares": {},
        "devices": {},
    }

    for all_day, calendars in [(True, all_day_calendars), (False, timed_calendars)]:
        for i in FIRMWARE_DATA:
            # Create calendars for this osType
            # This is before event creation, so that we can ensure there are calendars for all osTypes,
            # even if they will be empty
            if i["osType"] not in calendars["firmwares"]:
                calendars["firmwares"][i["osType"]] = new_calendar(f"AppleDB - {i['osType']}", f"AppleDB calendar for {i['osType']}.")

            events = process_firmware_event(i, all_day)
            if not events:
                continue

            for j in events:
                calendars["all"].add_component(j)
                calendars["all_firmware"].add_component(j)
                calendars["firmwares"][i["osType"]].add_component(j)

        for i in DEVICE_DATA:
            # Create calendars for this type
            # This is before event creation, so that we can ensure there are calendars for all types,
            # even if they will be empty
            if i["type"] not in calendars["devices"]:
                calendars["devices"][i["type"]] = new_calendar(f"AppleDB - {i['type']}", f"AppleDB calendar for {i['type']}.")

            events = process_device_event(i, all_day)
            if not events:
                continue

            for j in events:
                calendars["all"].add_component(j)
                calendars["all_device"].add_component(j)
                calendars["devices"][i["type"]].add_component(j)

    def path_to_url(path: Path) -> str:
        return f"https://api.appledb.dev/{urllib.parse.quote(str(path.relative_to(Path('out'))))}"

    def save_calendar(all_day_calendar: Calendar, timed_calendar: Calendar, path: Path):
        (path / "main.ics").write_bytes(all_day_calendar.to_ical())
        (path / "main-timed.ics").write_bytes(timed_calendar.to_ical())

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

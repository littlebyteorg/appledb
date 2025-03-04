import datetime
from pathlib import Path
import json
import zoneinfo
import dateutil.parser
from ics import Calendar, Event

# TODO: Make events have predictable IDs

calendar = Calendar()

CUPERTINO = zoneinfo.ZoneInfo("America/Los_Angeles")

ALL_DAY = True
DATE_THRESHOLD = datetime.datetime(2024, 1, 1) if ALL_DAY else datetime.datetime(2024, 1, 1, 10, 0, 0, tzinfo=CUPERTINO)


def process_event(data: dict):
    if not data.get("released"):
        return

    event = Event()
    event.name = f"{data['osStr']} {data['version']}"
    if data.get("build"):
        event.name += f" ({data['build']})"

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

    event.url = (
        f"https://appledb.dev/firmware/{data['osStr'].replace(' ', '-')}/{data.get('uniqueBuild') or data.get('build') or data['version']}"
    )

    # if len(data["released"]) <= 7:
    #     continue
    # released = datetime.datetime.fromisoformat(data["released"])
    released = dateutil.parser.parse(data["released"])

    if ALL_DAY:
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
    calendar.events.add(event)


for i in Path("osFiles").rglob("*.json"):
    try:
        os_file = json.loads(i.read_text())
        process_event(os_file)
        for changes in os_file.get("createDuplicateEntries", []):
            duplicate = os_file | changes
            duplicate.pop("createDuplicateEntries")
            process_event(duplicate)
        # TODO: Handle SDKs
    except:
        print(f"Error parsing {i}")
        raise

Path("calendar.ics").write_text(calendar.serialize())

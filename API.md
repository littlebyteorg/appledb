# AppleDB API Usage

The AppleDB API is located on api.appledb.dev and hosted from the [`gh-pages`](https://github.com/littlebyteorg/appledb/tree/gh-pages) branch of this repo.

All requests should be `GET` requests, this API is currently just static data.

## Structure

- `/bypass/` - jailbreak detection bypasses for apps
  - [`/bypass/index.json`](https://api.appledb.dev/bypass/index.json) - list all bundle IDs where information is available
  - `/bypass/<bundle id>.json` - information on a specific app's jailbreak detection bypass
  - [`/bypass/main.json`](https://api.appledb.dev/bypass/main.json) - contains information for all apps
- `/compat/` - jailbreak compatibility information for devices
  - `/compat/<key>/` - compatibility information for a specific device
    - `/compat/<key>/<build>.json` - compatibility information for a specific build for a specific device
- `/device/` - information on devices
  - [`/device/index.json`](https://api.appledb.dev/device/index.json) - list of all keys
  - `/device/<key>.json` - information on a specific device
  - [`/device/main.json`](https://api.appledb.dev/device/main.json) - contains information for all devices
- `/group/` - information on device groups
  - [`/group/index.json`](https://api.appledb.dev/group/index.json) - list of all keys
  - `/group/<key>.json` - information on a specific device group
  - [`/group/main.json`](https://api.appledb.dev/group/main.json) - contains information for all device groups
- `/ios/` - information on OS versions (not just iOS)
  - [`/ios/index.json`](https://api.appledb.dev/ios/index.json) - list of all keys (`<osStr>;<build>`)
  - `/ios/<osStr>;<build>.json` - information on a specific OS build
  - [`/ios/main.json`](https://api.appledb.dev/ios/main.json) - contains information for all OS builds
  - `/ios/<osType>/` - information for a specific OS
    - `/ios/<osType>/index.json` - list of all keys for a specific OS, relative to the `/ios/` path
    - `/ios/<osType>/main.json` - contains information for all OS builds for a specific OS
  - Note: `<osStr>` is the marketing name of the operating system (ie. `Mac OS X`, `OS X`, `macOS`), while `<osType>` is an AppleDB-determined name that does not change with marketing changes (ie. `macOS`)
    - Endpoints using `<osType>` may change to using `<osStr>` in the future
- `/jailbreak/` - information on jailbreaks
  - [`/jailbreak/index.json`](https://api.appledb.dev/jailbreak/index.json) - list of all jailbreaks
  - `/jailbreak/<name>.json` - information on a specific jailbreak
  - [`/jailbreak/main.json`](https://api.appledb.dev/jailbreak/main.json) - contains information for all jailbreaks
- [`/main.json`](https://api.appledb.dev/main.json) - contains information for all endpoints, *excluding* jailbreak compatibility information

## API Changelog

To stay updated on changes to the API (and AppleDB development in general), you can join our [Discord](https://discord.gg/QBj8pBa).

### 2023-09-13

- Initial version of this document

<!---

I'm not sure if we should include this granular information as it may change rapidly and is somewhat self evident if you just look at the files.

### `/bypass/`

Contains information on jailbreak detection bypasses for various apps.

#### `/bypass/index.json`

Contains a list of all apps with jailbreak detection bypasses.

#### `/bypass/<bundle id>.json`

Contains information on a specific app's jailbreak detection bypass.

##### Schema

```json
{
    "name": "ALHOSN UAE",
    "bundleId": "ae.healthshield.app.ios",
    "uri": "https://apps.apple.com/us/app/alhosn-uae/id1505380329",
    "icon": "https://is4-ssl.mzstatic.com/image/thumb/Purple126/v4/71/3a/f4/713af4e1-9746-0cee-abef-e39680723c3f/source/512x512bb.jpg",
    "bypasses": [
        {
            "guide": "https://hekatos.github.io/tools/tweaks/#a-bypass",
            "repository": {
                "uri": "https://repos.slim.rocks/repo/?repoUrl=https://repo.co.kr"
            },
            "name": "A-Bypass"
        }
    ]
}
```

-->

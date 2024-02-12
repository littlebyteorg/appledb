# AppleDB API Usage

The AppleDB API is located on api.appledb.dev and hosted from the [`gh-pages`](https://github.com/littlebyteorg/appledb/tree/gh-pages) branch of this repo.

All requests should be `GET` requests, this API is currently just static data.

URLs are case sensitive.

## Structure

- `/bypass/` - jailbreak detection bypasses for apps
  - [`/bypass/index.json`](https://api.appledb.dev/bypass/index.json) - list all bundle IDs where information is available
  - `/bypass/<bundle id>.json` ([example](https://api.appledb.dev/bypass/com.freecharge.ios.json)) - information on a specific app's jailbreak detection bypass
  - [`/bypass/main.json`](https://api.appledb.dev/bypass/main.json) ([`.gz`](https://api.appledb.dev/bypass/main.json.gz)/[`.xz`](https://api.appledb.dev/bypass/main.json.xz)) - contains information for all apps
- `/compat/` - jailbreak compatibility information for devices
  - `/compat/<key>/` - compatibility information for a specific device
    - `/compat/<key>/<build>.json` ([example](https://api.appledb.dev/compat/iPhone12,1/19B74.json)) - compatibility information for a specific build and device
- `/device/` - information on devices
  - [`/device/index.json`](https://api.appledb.dev/device/index.json) - list of all keys
  - `/device/<key>.json` ([example](https://api.appledb.dev/device/Mac14,2.json)) - information on a specific device
  - [`/device/main.json`](https://api.appledb.dev/device/main.json) ([`.gz`](https://api.appledb.dev/device/main.json.gz)/[`.xz`](https://api.appledb.dev/device/main.json.xz)) - contains information for all devices
- `/group/` - information on device groups
  - [`/group/index.json`](https://api.appledb.dev/group/index.json) - list of all keys
  - `/group/<key>.json` ([example](https://api.appledb.dev/group/Mac%20Pro%20(2023).json)) - information on a specific device group
  - [`/group/main.json`](https://api.appledb.dev/group/main.json) ([`.gz`](https://api.appledb.dev/group/main.json.gz)/[`.xz`](https://api.appledb.dev/group/main.json.xz)) - contains information for all device groups
- `/ios/` - information on OS versions (not just iOS)
  - [`/ios/index.json`](https://api.appledb.dev/ios/index.json) - list of all keys (`<osStr>;<build>`)
  - `/ios/<osStr>;<build>.json` ([example](https://api.appledb.dev/ios/macOS;22F66.json)) - information on a specific OS build
  - [`/ios/main.json`](https://api.appledb.dev/ios/main.json) ([`.gz`](https://api.appledb.dev/ios/main.json.gz)/[`.xz`](https://api.appledb.dev/ios/main.json.xz)) - contains information for all OS builds
  - `/ios/<osType>/` - information for a specific OS
    - `/ios/<osType>/index.json` ([example](https://api.appledb.dev/ios/macOS/index.json)) - list of all keys for a specific OS, relative to the `/ios/` path
    - `/ios/<osType>/main.json` ([example](https://api.appledb.dev/ios/macOS/main.json) ([`.gz`](https://api.appledb.dev/ios/macOS/main.json.gz)/[`.xz`](https://api.appledb.dev/ios/macOS/main.json.xz))) - contains information for all OS builds for a specific OS
  - Note: `<osStr>` is the marketing name of the operating system (ie. `Mac OS X`, `OS X`, `macOS`), while `<osType>` is an AppleDB-determined name that does not change with marketing changes (ie. `macOS`)
    - Endpoints using `<osType>` may change to using `<osStr>` in the future
- `/jailbreak/` - information on jailbreaks
  - [`/jailbreak/index.json`](https://api.appledb.dev/jailbreak/index.json) - list of all jailbreaks
  - `/jailbreak/<name>.json` ([example](https://api.appledb.dev/jailbreak/Dopamine.json)) - information on a specific jailbreak
  - [`/jailbreak/main.json`](https://api.appledb.dev/jailbreak/main.json) ([`.gz`](https://api.appledb.dev/jailbreak/main.json.gz)/[`.xz`](https://api.appledb.dev/jailbreak/main.json.xz)) - contains information for all jailbreaks
- [`/main.json`](https://api.appledb.dev/main.json) ([`.gz`](https://api.appledb.dev/main.json.gz)/[`.xz`](https://api.appledb.dev/main.json.xz)) - contains information for all endpoints, *excluding* jailbreak compatibility information

## API Changelog

To stay updated on changes to the API (and AppleDB development in general), you can join our [Discord](https://discord.gg/QBj8pBa).

### 2024-02-01

- Add compressed endpoints for `main.json`

> [!IMPORTANT]
> With the previous iteration of the API, OTAs were stripped from all endpoints to deal with space issues. With this iteration of the API, OTAs are only stripped from the uncompressed `main.json` endpoints. This is a stopgap until we can figure out how to deal with this issue and make OTAs available on all endpoints.

### 2023-09-13

- Initial version of this document

<!---

I'm not sure if we should include this granular information as it is somewhat self evident if you just look at the files, especially since you don't need to pass parameters or data to get the information.

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

# Automation scripts
These scripts are primarily used to assist with adding new software versions to AppleDB.

## Importing IPSW files
### Grabbing IPSW links from the Developer Portal
Run `grab_ipsws_dev_portal.py`. This takes in a positional argument for a dev portal proxy, but if one isn't passed in or provided by a manual edit of the script, will instead look at `import_raw.html` for an HTML dump of the Operating Systems page. This script outputs link data to `import.json`.

### Grabbing IPSW links from Apple plist links
Run `grab_ipsws_itunes.py`. This script will check the iTunes plist for most OSes, and will also check for macOS and bridgeOS IPSWs in their respective locations. This script outputs links to `import.txt`

### Importing grabbed links into AppleDB
Run `ipsw_import.py`.

Arguments:
1. `-b`, `--bulk-mode`: Automatically run the import in bulk mode, importing from `import.json`, if it exists, or `import.txt`. If this is not passed in, a prompt at execution will ask which mode to proceed in. If not running in bulk mode, this script will ask for links one at a time.
2. `-s`, `--fule-self-driving`: No prompts for release dates or version numbers. `(FIXME)` will be added as a suffix to any new version numbers and any release dates will be `YYYY-MM-DD`, forcing a CI failure if pushed to the repo.

## Importing InstallAssistant.pkg files
### Grabbing InstallAssistant links from Apple catalogs
Run `grab_ias.py`. This script outputs links to `import-ia.txt`.

Arguments:
1. `-b`, `--beta`: Check for beta versions instead. This will grab **both** developer and public beta links, and the catalog name (`dev-beta` or `public-beta`) will be appended to the link after a semicolon (`;`).
2. `-m`, `--min-version`: Minimum version to check the installer catalog for. Currently defaults to `12` (Monterey)
### Importing grabbed links into AppleDB
Run `ia_import.py`.

Arguments:
1. `-b`, `--bulk-mode`: Automatically run the import in bulk mode, importing from `import-ia.json`, if it exists, or `import-ia.txt`. If this is not passed in, a prompt at execution will ask which mode to proceed in. If not running in bulk mode, this script will ask for links one at a time.
2. `-s`, `--fule-self-driving`: No prompts for release dates or version numbers. `(FIXME)` will be added as a suffix to any new version numbers and any release dates will be `YYYY-MM-DD`, forcing a CI failure if pushed to the repo.
3. `-h`, `--add-sha1-hash`: Include grabbing the sha1 hash for the imported IAs, if they're not already in the repo. This requires downloading the full IA, and can take a significant amount of time. Defaults to false.

## Importing Over-the-Air (OTA) files
### Grabbing links from Pallas
Run `grab_otas.py`. This script outputs links to `import-ota.txt`.

Arguments:
1. `-o`, `--os`: The OS to check updates for. Valid values include:
    a. audioOS
    b. iOS
    c. iPadOS
    d. macOS
    e. Studio Display Firmware
    f. tvOS
    g. visionOS
    h. watchOS
2. `-b`, `--build`: The build(s) to read to get the full prerequisite list for calls to pallas. Each time this is specified, one or more builds must be passed in.
3. `-a`, `--audience`: The pallas asset audience(s) to check. This supports `beta`, `release`, as well as specific UUIDs.
4. `-r`, `--rsr`: Specify to check for Rapid Security Responses instead of OTA updates
5. `-d`, `--devices`: Specify to only check for a subset of devices rather than all devices
6. `-n`, `--no-prerequisites`: Only check for OTAs available for the specified build, rather than that build and all builds that are listed as a prerequisite for the specified build. This is assumed to be passed in when passing in `-r`

For example, calling this script with `-o iOS -b 21E5184i` will check pallas for all devices in deviceMap from build 21E5184i, and for all sources with a `prerequisiteBuild` value, the script will also check pallas for __those__ builds as well (such as, in this example, 21D5044a).

Caveats:
1. `-o` and `-b` must be passed in an equal number of times, with a minimum of 1. They can be passed in multiple times, but it must be an equal number.
2. Order matters for these parameters. If checking for iOS and tvOS updates, ensure the parameters are passed in such as `-o iOS -b <iOS build> -o tvOS -b <tvOS build>`. The order of each OS doesn't matter, as long as the first instance of `-o` lines up with the builds specified in the first instance of `-b`.
3. The `beta` and `public` audience listings are special; for example, if checking for a beta build of macOS 12, all deltas will be checked for the macOS 12, 13, and 14 beta audiences. For macOS 13, in this example, only the macOS 13 and 14 beta audiences will be checked. The `beta` audience utilizes the developer/AppleSeed beta listings, while `public` is for public betas.

### Importing grabbed links into AppleDB
Run `ota_import.py`.

Arguments:
1. `-b`, `--bulk-mode`: Automatically run the import in bulk mode, importing from `import-ota.json`, if it exists, or `import-ota.txt`. If this is not passed in, a prompt at execution will ask which mode to proceed in. If not running in bulk mode, this script will ask for links one at a time.
2. `-s`, `--fule-self-driving`: No prompts for release dates or version numbers. `(FIXME)` will be added as a suffix to any new version numbers and any release dates will be `YYYY-MM-DD`, forcing a CI failure if pushed to the repo.

## Importing bridgeOS from update catalog
Run `bridge_pkg_import.py`. Passing in `-b` (`--beta`) will check for beta versions instead of release versions.

## Importing firmware for other devices
Run `mesu_import.py`. Passing in `-b` (`--beta`) will only check AirPods, with the `AirPods2022Seed` prefix applied to the URL for the beta builds. This currently supports AirPods, Beats, and Keyboards.

## Importing other software
### iTunes
Run `itunes_import.py`. No arguments are passed in, and this will only add the **latest** iTunes version.

### Rosetta
Run `rosetta_import.py`. No arguments are passed in, and this will automatically create all versions of Rosetta that are defined in the Rosetta catalog.

If there's no corresponding macOS build for a given Rosetta build, there will be a prompt to ensure that the version number specified is desired; this is where beta versions will need to be provided.

### Safari
Run `safari_import.py`.
Arguments:
1. `-v`, `--version`: an optional argument to specify which version of Safari that's being looked for. Currently defaults to 17.
2. `-b`, `--beta`: an optional argument to specify beta checks. This will also include placeholder links for the developer portal.
This will check catalogs for macOS versions 4 and 5 lower than the Safari version (for example, a Safari version of 17 will check the catalogs for macOS 12 (Monterey) and 13 (Ventura)).
If a beta version is being added, `releaseNotes` will point to the dev portal PDF. Otherwise, it'll be to the developer portal page for Safari

### Safari Technology Preview
Run `stp_import.py`. No arguments are passed in, and it will only check as long as the dev portal site has the new build.

### Xcode (and device simulators)
Run `xcode_simulator_import.py`. No arguments are passed in, but it will use the current date as the release date for any new simulator versions.

## Ancilliary scripts
### embedded_os_import.py
This script adds the `embeddedOSBuild` for any Monterey and Ventura OS release that would support the `MacBookPro14,1` (2017 Touchbar Mac) and grabs the embeddedOS firmware within an OTA and parses the build out of there.

### ipd_import.py
This script populates the `ipd` section for all IPSW files referenced from the catalog utilized by iTunes. No arguments are passed in, and this will automatically update all references.

## security_note_import.py
This script is designed to add the `securityNotes` attribute to all builds of a given release version.
Arguments:
1. `-p`, `--product`: The product to get notes for
2. `-v`, `--version`: The version of the provided product to look for
3. `-d`, `--date`: The date to get notes for
If `-p` or `-v` are specified, **both** must be present, and `-d` can also be provided.
On the other hand, `-d` can be specified without specifying `-p` or `-v`, which is particularly useful for events such as release day
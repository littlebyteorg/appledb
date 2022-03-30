# appledb

Hosted at [api.appledb.dev](https://api.appledb.dev/).

This is intended for use in [appledb.dev](https://appledb.dev/) and [ios.cfw.guide](https://ios.cfw.guide), however you may also use this information in your projects.

## Website/API structure

The `index.json` file contains a list of all the names of `.json` files in each folder.

The `main.json` file contains all the information in a folder.

```
main.json
bypass/
  index.json
  main.json
  Citibank.UAE.json
  ae.healthshield.app.ios.json
  ...
compat/
  AppleTV1,1/
    8N5107.json
    8N5622.json
    8N5880.json
    ...
  AppleTV2,1/
    10A406e.json
    10A831.json
    10B144b.json
    ...
  ...
device/
  index.json
  main.json
  AppleTV1,1.json
  AppleTV2,1.json
  ...
group/
  index.json
  main.json
  Apple TV (1st generation).json
  Apple TV (2nd generation).json
  ...
ios/
  index.json
  main.json
  10A403.json
  10A405.json
  ...
jailbreak/
  index.json
  main.json
  4039.json
  Absinthe.json
  ...
```

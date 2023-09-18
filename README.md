# AppleDB

Hosted at [api.appledb.dev](https://api.appledb.dev/).

This is intended for use in [appledb.dev](https://appledb.dev/) and [ios.cfw.guide](https://ios.cfw.guide), however you may also use this information in your projects.

For more API usage information, see [this page](API.md).

## Repo structure

File structure is broken up like follows:

```text

.github/
    This folder contains various definitions for GitHub actions and Issues
   
.husky/
    This is a helper tool to make sure your changes are "clean" before a `git commit`.  More can be leaned
    about husky at https://typicode.github.io/husky/#/

appledb-web/

bypassApps/
    *define me*

bypassTweaks/
    *define me*

chipFiles/
    Each of these files describes a particular Apple designed processor (such as the M1, A15, etc).

deviceFiles/
    Each of these files describes an Apple device (such as the iPhone 13 Pro Max, iPad Air, etc).

deviceGroupFiles/
    These files group related devices in to related groups (e.g. Cellular and Wi-Fi models of iPads are grouped together).

osFiles/
    These are files that describe a particular OS software bundles.

jailbreakFiles/
    These describe particular tools for achieving a jailbreak on a device.

node_modules/
    Third party code that isn't checked into the repository that helps with the deploy, testing etc of this repo.

tests/
    These are bits of TypeScript/JavaScript that ensure that there are no errors like missing quotation marks or such
    in the files before trying to deploy them.

.eslintrc.js
    This provides EcmaScript/JavaScript/TypeScript style and warnings when you run `npm run lint`

.gitignore
    These are files that are never checked into the GitHub copy
    
deploy.js
    *legacy deploy code* - Will move to grunt

jest.config.json
    Configuration for the `jest` test runner for the files in `tests/`

LICENSE

package.json
    Declares the various tools and commands that the repo uses such as `npm test`

package-lock.json
    A set of the correct versions of tools to install to `node_modules/` - Do not hand edit

README.md
    This File
    
tsconfig.json
    Configuration to allow for the use of TypeScript as well as JavaScript
    
update_links.py
    *legacy link updater* - Move to grunt task
```

## Contributing

First fork the repository

Perform a `git clone` to your own computer and ensure you have NodeJS (https://nodejs.org/en/) installed.

In the working directory run `npm install` which will bring down the tools to check the code or to perform a build or
other automated task.

Make edits

Run a `git add . && git commit` to save your work, and then `git push` to your fork.  After
that go to GitHub and open a Pull Request.

## License

The data here is provided under a MIT license as described in the `LICENSE` file.

## Credits

This repository is provided by `littlebyteorg`.

Portions of the data have been sourced from [`hack-different/apple-knowledge`](https://github.com/hack-different/apple-knowledge)
and the [`apple-data` node package](https://www.npmjs.com/package/apple-data)

Portions of the data have been sourced from [theapplewiki.com](https://www.theapplewiki.com)

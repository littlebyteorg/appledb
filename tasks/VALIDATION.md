# AppleDB data validation

This document describes how AppleDB keeps JSON data well-formed, schema-valid, and consistently formatted.

## Overview

Validation runs in layers:

1. **Parse** — every JSON file must parse as UTF-8 JSON
2. **Normalize / structure** — sort scripts rewrite files with canonical key order, sorted lists, and filename checks
3. **Schema** — AJV validates each data file against Draft-07 schemas in `schemas/`
4. **CI** — GitHub Actions runs full schema validation on push and pull request

```text
Edit JSON
   │
   ▼
pre-commit (husky → lint-staged)
   ├─ npm run parse-test     → tasks/json_validator.py
   └─ npm run sort-*-files   → tasks/sort_*.py
   │
   ▼
CI job "validate" (.github/workflows/deploy.yml)
   └─ yarn validate          → tasks/schema_validator.js + schemas/*.json
```

Local pre-commit does **not** run AJV schema validation. Run `yarn validate` (or `npm run validate`) before opening a PR if you want the same check CI runs.

## npm scripts

Defined in `package.json`:

| Script | Command | Purpose |
|--------|---------|---------|
| `parse-test` | `./tasks/json_validator.py` | Ensure JSON parses |
| `sort-os-files` | `./tasks/sort_os_files.py` | Canonicalize `osFiles/**/*.json` |
| `sort-device-files` | `./tasks/sort_device_files.py` | Canonicalize `deviceFiles/**/*.json` |
| `sort-device-group-files` | `./tasks/sort_device_group_files.py` | Canonicalize `deviceGroupFiles/**/*.json` |
| `sort-jailbreak-files` | `./tasks/sort_jailbreak_files.py` | Canonicalize `jailbreakFiles/**/*.json*` |
| `sort-bypass-app-files` | `./tasks/sort_bypass_app_files.py` | Canonicalize `bypassApps/**/*.json` |
| `sort-bypass-tweak-files` | `./tasks/sort_bypass_tweak_files.py` | Canonicalize `bypassTweaks/**/*.json` |
| `validate` | `node tasks/schema_validator.js` | AJV schema validation for all data trees |

Most sort/parse scripts accept `-f` / `--files` so lint-staged can run only on staged paths.

## Layer 1 — JSON parse (`tasks/json_validator.py`)

- Loads each file with Python `json.load` (UTF-8)
- Skips paths under `out/` and `node_modules/`
- On failure: prints the path and re-raises (non-zero exit)

```bash
# all JSON under the repo (from repo root)
npm run parse-test

# specific files
npm run parse-test -- -f path/to/file.json
```

## Layer 2 — Sort and structural checks (`tasks/sort_*.py`)

Shared helpers live in `tasks/sort_files_common.py` (device/build/version sort keys, filename validation).

For each file, sort scripts typically:

1. Reorder object keys to a fixed allowlist (`key_order`)
2. **Reject unknown keys** not in that allowlist
3. Sort nested arrays (devices, builds, sources, colors, etc.)
4. Validate the **filename stem** against identity fields where applicable
5. Rewrite the file as indented UTF-8 JSON (`indent=4`, `ensure_ascii=False`)

### Filename rules

| Tree | Stem must match one of |
|------|-------------------------|
| `osFiles` | `uniqueBuild`, `build`, or `version` |
| `deviceFiles` | `name`, `identifier`, or `key` |
| `deviceGroupFiles` | `name` or `key` |

Bypass app/tweak sort scripts canonicalize keys but do not enforce filename ↔ field matching.

### Example

```bash
npm run sort-os-files -- -f osFiles/macOS/21x\ -\ 12.x/21G365.json
```

## Layer 3 — JSON Schema / AJV (`tasks/schema_validator.js`)

### Runtime

- Changes working directory to `tasks/`
- Creates `Ajv({ allErrors: true })` and registers `ajv-formats`
- Compiles one schema per data tree and validates every matching file
- Prints each failure path plus AJV error objects
- Exit `1` if any file fails; otherwise prints `N files passed`

### Schema map

| Schema | Data glob |
|--------|-----------|
| `schemas/bypassApps.json` | `bypassApps/**/*.json` |
| `schemas/bypassTweaks.json` | `bypassTweaks/**/*.json` |
| `schemas/deviceFiles.json` | `deviceFiles/**/*.json` |
| `schemas/deviceGroupFiles.json` | `deviceGroupFiles/**/*.json` |
| `schemas/jailbreakFiles.json` | `jailbreakFiles/**/*.json*` (includes `.json.archive`) |
| `schemas/osFiles.json` | `osFiles/**/*.json` |

### How to run

```bash
# preferred (matches CI)
yarn
yarn validate

# if yarn is unavailable, install JS deps then validate
# note: full install may need liblzma headers for node-liblzma (deploy only)
npm install --ignore-scripts   # enough for validate (ajv, ajv-formats, glob)
npm run validate
```

Schema validation requires Node packages: `ajv`, `ajv-formats`, `glob` (see `package.json` `devDependencies`).

### Key constraints in `schemas/osFiles.json`

The OS/firmware schema is the strictest. Highlights:

| Area | Rules |
|------|--------|
| Root | Object; **required** `osStr`, `version` |
| Closed object | `additionalProperties: false` on the OS definition |
| `version` | String; **must not** contain `FIXME` |
| `buildId` | UUID format |
| `released` | `date-time`, `date`, `YYYY-MM`, `YYYY`, or `""` |
| `deviceMap` / `osMap` | Non-empty unique string arrays when present |
| `sources[]` | Each requires `type`, `links`, `deviceMap`; closed object |
| `sources[].type` | Enum (`ipsw`, `ota`, `installassistant`, `pkg`, …) |
| `links[]` | ≥1 `sourceLink`: required `url` (URI) + `active` (boolean) |
| `hashes` | Optional `md5` / `sha1` / `sha2-256` / `sha2-512`; lowercase hex only |
| `size` | Integer |
| `createDuplicateEntries` | Nested full OS objects; cannot nest further duplicates |
| `sdks[]` | Closed SDK stub objects; UUID `buildId` when set |

Other schemas follow the same idea: closed property sets, required identity fields where needed, URI/date/hex formats via `ajv-formats` and patterns.

Schemas do **not** check cross-file references (for example, whether a `deviceMap` entry exists under `deviceFiles/`).

## Pre-commit hooks

- `.husky/pre-commit` runs `npx lint-staged`
- `package.json` → `lint-staged`:

| Glob | Action |
|------|--------|
| `*.json` | `parse-test -- -f` |
| `osFiles/**/*.json` | `sort-os-files -- -f` |
| `deviceFiles/**/*.json` | `sort-device-files -- -f` |
| `deviceGroupFiles/**/*.json` | `sort-device-group-files -- -f` |
| `jailbreakFiles/**/*.json` | `sort-jailbreak-files -- -f` |
| `bypassApps/**/*.json` | `sort-bypass-app-files -- -f` |
| `bypassTweaks/**/*.json` | `sort-bypass-tweak-files -- -f` |

Husky is installed via the `prepare` script when you install dependencies outside CI.

## CI (`.github/workflows/deploy.yml`)

Two jobs:

| Job | Role |
|-----|------|
| `validate` | Checkout → setup Node → `yarn` → **`yarn validate`** |
| `deploy` | Build static API (`generate_link_variants.py`, `deploy.js`, `gen_calendar.py`); publish `out/` to `gh-pages` on `main` (or `workflow_dispatch`) |

Schema validation is the dedicated gate. Deploy assumes source JSON is already valid.

## Related operational checks (not CI gates)

These help keep data accurate but are not part of `yarn validate`:

| Script | Purpose |
|--------|---------|
| `tasks/find_mixed_active.py` | Find sources whose links mix `active: true` and `false` |
| `tasks/check_signing_status.py` | Refresh `signed` from Apple signing / manifests |
| Import `--full-self-driving` | Writes `FIXME` / placeholder dates so incomplete rows fail schema or review |

## Quick contributor checklist

1. Edit or add JSON under the appropriate data directory
2. From repo root: ensure dependencies are installed (`yarn` recommended)
3. Optionally sort the files you touched (`npm run sort-os-files -- -f …`, etc.)
4. Run **`yarn validate`** (or `npm run validate`)
5. Commit; pre-commit will parse and re-sort staged JSON
6. Push; CI `validate` job must stay green

## Verifying the validator locally

To confirm AJV is working:

**Expect failure** — `version` containing `FIXME` violates `osFiles.json`:

```json
{
  "osStr": "macOS",
  "version": "99.0 (FIXME)"
}
```

AJV reports something like:

```text
instancePath: '/version'
schemaPath: '#/properties/version/not'
keyword: 'not'
message: 'must NOT be valid'
```

**Expect success** — minimal valid shape plus optional valid `sources`:

```json
{
  "osStr": "macOS",
  "version": "99.0",
  "build": "99A999",
  "released": "2026-01-01",
  "deviceMap": ["VirtualMac2,1"],
  "sources": [
    {
      "type": "ipsw",
      "deviceMap": ["VirtualMac2,1"],
      "links": [
        { "url": "https://example.com/file.ipsw", "active": true }
      ]
    }
  ]
}
```

Place temporary files under a disposable folder such as `osFiles/_validation_test/`, run `npm run validate`, then **delete that folder** so it is not committed.

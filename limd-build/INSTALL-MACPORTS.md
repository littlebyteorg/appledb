# idevicerestore: MacPorts install (libirecovery API fix)

## Problem

MacPorts `idevicerestore @1.0.0` fails to build against current `libirecovery` (e.g. `@1.3.1`):

```text
dfu.c: error: use of undeclared identifier 'irecv_init'
recovery.c: error: use of undeclared identifier 'irecv_init'
```

`irecv_init()` was removed from libirecovery’s public API. Callers should use
`irecv_open_with_ecid()` directly (no library init step).

## Verified local binary (pre-MacPorts install)

A patched `idevicerestore` 1.0.0 tree was built and smoke-tested locally, then
removed as a temporary build artifact (not kept in git). Re-create it via the
MacPorts overlay (Option A) or a one-off source build using
`patch-remove-irecv_init.diff`.

Smoke checks (2026-09-06, no device attached):

| Check | Result |
| --- | --- |
| `file` | Mach-O 64-bit executable arm64 |
| `-v` | `idevicerestore 1.0.0` (exit 0) |
| `-h` | usage printed (exit 0) |
| Linked dylibs | All resolve under `/opt/local` + system |
| Undefined `irecv_init` | None |
| Device discover (no device) | Fails cleanly: *Unable to discover device mode* (exit 255) |
| `irecovery -q` | Available from MacPorts |

Linked libraries include `libirecovery-1.0.5.dylib`, `libimobiledevice-1.0.6.dylib`,
`libplist-2.0.4.dylib`, OpenSSL 3, curl, libzip.

> Full restore flows were **not** exercised (no IPSW / no attached device).
> Attach a device and use non-destructive flags first (`-n`, `--ipsw-info`, etc.).

## Option A — Local MacPorts overlay (recommended for a port-managed install)

This repo includes an overlay that bumps the stable port to **revision 3** and adds
`patch-remove-irecv_init.diff`.

### 1. Overlay layout

```text
macports-overlay/
  devel/idevicerestore/
    Portfile
    files/
      patch-postrelease-fixes.diff
      patch-remove-irecv_init.diff
```

Absolute path on this machine:

```text
/Users/madmax/ProfileCreator/mac-admin-tools/appledb/limd-build/macports-overlay
```

### 2. Register the overlay (file:// must be **above** the rsync tree)

Edit `/opt/local/etc/macports/sources.conf` and insert **before** the
`rsync://rsync.macports.org/...` line:

```text
file:///Users/madmax/ProfileCreator/mac-admin-tools/appledb/limd-build/macports-overlay
```

Example order:

```text
file:///Users/madmax/ProfileCreator/mac-admin-tools/appledb/limd-build/macports-overlay
rsync://rsync.macports.org/macports/release/tarballs/ports.tar [default]
```

### 3. Index the overlay

```bash
cd /Users/madmax/ProfileCreator/mac-admin-tools/appledb/limd-build/macports-overlay
portindex
```

### 4. Confirm MacPorts sees revision 3 + patch

```bash
port info idevicerestore
port file idevicerestore
# Should point at .../limd-build/macports-overlay/devel/idevicerestore/Portfile
```

### 5. Build and install

```bash
sudo port clean idevicerestore
sudo port -v install idevicerestore
```

### 6. Verify the installed binary

```bash
which idevicerestore
idevicerestore -v
idevicerestore -h
otool -L "$(which idevicerestore)" | grep irecovery
nm -u "$(which idevicerestore)" | grep irecv_init || echo "OK: no irecv_init"
```

### 7. Optional: deactivate overlay later

Remove or comment the `file://...macports-overlay` line from `sources.conf`, then:

```bash
sudo port selfupdate   # or portindex on default tree as needed
```

## Option B — One-off source install

If you only need the tool and do not care about MacPorts ownership:

```bash
cd /Users/madmax/ProfileCreator/mac-admin-tools/appledb/limd-build
# Obtain 1.0.0 sources (example: MacPorts distfile or GitHub archive), then:
# tar xzf idevicerestore-1.0.0.tar.gz && cd idevicerestore-1.0.0
patch -p0 < ../patch-remove-irecv_init.diff   # adjust path to the patch as needed
export PATH="/opt/local/bin:$PATH"
export PKG_CONFIG_PATH="/opt/local/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
./autogen.sh --prefix=/opt/local CPPFLAGS="-I/opt/local/include" LDFLAGS="-L/opt/local/lib"
make -j"$(sysctl -n hw.ncpu)"
sudo make install
```

Note: `port uninstall idevicerestore` will **not** remove files installed this way.

## Option C — Upstream devel port (no local patch)

If you prefer current git snapshots instead of 1.0.0:

```bash
sudo port install idevicerestore-devel
```

This conflicts with `idevicerestore` and pulls `libirecovery-devel` and related `-devel` ports.

## Patch contents (stable 1.0.0)

`patch-remove-irecv_init.diff` deletes three obsolete calls:

- `src/dfu.c` — `dfu_check_mode`, `dfu_get_irecv_device`
- `src/recovery.c` — `recovery_check_mode`

After patching, those paths only call `irecv_open_with_ecid(...)`.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Still builds old revision 2 | Overlay not first in `sources.conf`, or `portindex` not run |
| Patch fails to apply | Ensure `patch-postrelease-fixes.diff` applies first; our patch is `-p0` style like the stock port |
| Wrong binary at runtime | `which -a idevicerestore`; check `otool -L` points at `/opt/local/lib` |
| No device found | Expected with no hardware; DFU/recovery need a USB-attached device |

## Files in this directory

| Path | Purpose |
| --- | --- |
| `patch-remove-irecv_init.diff` | Standalone API fix patch |
| `macports-overlay/` | Local ports tree for Option A |
| `limd-build-macos.sh` | Upstream-style full stack macOS build script |
| `INSTALL-MACPORTS.md` | This document |

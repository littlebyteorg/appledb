const path = require('node:path');

// Validate with appReleaseFiles.json first. Catalog validation must reject key collisions.
module.exports = function appReleaseApiRecord(filename, version, appRecord) {
    const basename = path.basename(filename);
    const app = path.basename(path.dirname(filename));
    if (!/^[a-zA-Z0-9][a-zA-Z0-9. ()_-]*\.json$/.test(basename) ||
        basename !== `${version.version}.json`) throw new Error('Filename must match version');
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(app) || app === 'main') throw new Error('Invalid app folder');
    if (Object.hasOwn(version, 'key')) throw new Error('Source must not contain key');
    if (!appRecord || version.app !== appRecord.name) throw new Error('App display name mismatch');
    const identity = value => JSON.stringify([value.platform, value.edition ?? null]);
    const variants = appRecord.variants.map(identity);
    if (new Set(variants).size !== variants.length) throw new Error('Duplicate app platform/edition');
    const seen = new Set();
    for (const release of version.releases) {
        if (!variants.includes(identity(release))) throw new Error('Unknown platform/edition');
        const id = JSON.stringify([identity(release), release.build ?? null, release.beta ?? false, release.released ?? null, release.rc ?? false, release.internal ?? false, release.legacyId ?? null, release.osMap ?? null]);
        if (seen.has(id)) throw new Error('Duplicate release; combine its download sources');
        seen.add(id);
    }
    const key = basename.slice(0, -5).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-$/, '');
    if (key === 'main') throw new Error('Reserved version key');
    return { app: version.app, key, version: version.version,
        releases: version.releases.map(release => ({ ...release, beta: release.beta ?? false })) };
};

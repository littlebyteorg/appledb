const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Ajv = require('ajv');
const root = path.resolve(__dirname, '..');
const read = name => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'));
const ajv = new Ajv({allErrors: true, strict: true});
require('ajv-formats')(ajv);
const validators = Object.fromEntries(['appFiles', 'appReleaseFiles'].map(name => [name, ajv.compile(read(`schemas/${name}.json`))]));
const valid = (name, value) => assert(validators[name](value), JSON.stringify(validators[name].errors));
const exportApp = require('./app_api_record');
const exportVersion = require('./app_release_api_record');
// Exercise contracts without shipping a sample catalog or migration map.
const app = {name: 'Contract test', variants: [{platform: 'macOS'}, {platform: 'Windows'}]};
const version = {app: app.name, version: '1.0', releases: [{platform: 'macOS', released: '2026-01-01'}, {platform: 'Windows', released: '2026-01-02', beta: true}]};
valid('appFiles', app);
valid('appFiles', exportApp('appFiles/contract-test.json', app));
valid('appReleaseFiles', version);
const api = exportVersion('appReleaseFiles/contract-test/1.0.json', version, app);
const {key, ...apiSource} = api;
valid('appReleaseFiles', apiSource);
assert.equal(api.key, '1-0');
assert.equal(api.releases[0].beta, false);
assert.equal(api.releases[1].beta, true);
assert(!Object.hasOwn(version.releases[0], 'beta'));
function reject(name, value, mutate) {
    const copy = structuredClone(value); mutate(copy); assert.equal(validators[name](copy), false);
}
reject('appFiles', app, value => value.key = 'forbidden');
reject('appFiles', app, value => value.variants[0].edition = '');
for (const mutate of [value => value.releases = [], value => value.releases[0].beta = 'true', value => value.releases[0].released = '2026-02-30', value => delete value.releases[0].platform]) reject('appReleaseFiles', version, mutate);
assert(api.releases.every(release => typeof release.beta === 'boolean'));
for (const mutate of [value => value.app = 'Mismatch', value => value.releases[0].edition = 'unknown', value => value.releases.push({...value.releases[0]})]) {
    const copy = structuredClone(version); mutate(copy);
    assert.throws(() => exportVersion('appReleaseFiles/contract-test/1.0.json', copy, app));
}
assert.throws(() => exportVersion('appReleaseFiles/contract-test/2.0.json', version, app));
assert.throws(() => exportApp('appFiles/main.json', app));
const sourceSchema = read('schemas/appReleaseFiles.json').properties.releases.items.properties.sources.items;
assert.deepEqual(sourceSchema.properties.hashes, read('schemas/osFiles.json').definitions.os.properties.sources.items.properties.hashes);
// Validate real app records when present; an empty category is supported.
const appsDir = path.join(root, 'appFiles'), releasesDir = path.join(root, 'appReleaseFiles');
let appCount = 0, versionCount = 0;
if (fs.existsSync(appsDir)) for (const file of fs.readdirSync(appsDir).filter(file => file.endsWith('.json'))) {
    const id = file.slice(0, -5), record = read(`appFiles/${file}`);
    valid('appFiles', record); valid('appFiles', exportApp(`appFiles/${file}`, record));
    const dir = path.join(releasesDir, id), keys = new Set();
    if (fs.existsSync(dir)) for (const file of fs.readdirSync(dir).filter(file => file.endsWith('.json'))) {
        const value = read(`appReleaseFiles/${id}/${file}`); valid('appReleaseFiles', value);
        const exported = exportVersion(`appReleaseFiles/${id}/${file}`, value, record); const {key, ...source} = exported; valid('appReleaseFiles', source);
        assert(exported.releases.every(release => typeof release.beta === 'boolean'));
        assert(!keys.has(exported.key), `Version key collision: ${id}/${exported.key}`); keys.add(exported.key); versionCount++;
    }
    appCount++;
}
if (fs.existsSync(releasesDir)) for (const id of fs.readdirSync(releasesDir)) assert(fs.existsSync(path.join(appsDir, `${id}.json`)), `Missing app record: ${id}`);
console.log(`Two source schemas compiled; contract checks passed; validated ${appCount} apps and ${versionCount} version files.`);

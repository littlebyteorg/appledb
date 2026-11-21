const path = require('node:path');

// Input must pass the relevant source schema before production export.
// The app filename identifies the API path; it is not repeated in the payload.
module.exports = function appApiRecord(filename, app) {
    const basename = path.basename(filename);
    if (!basename.endsWith('.json')) throw new Error('Source record must be a JSON file');
    const key = basename.slice(0, -5);
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(key) || key === 'main') {
        throw new Error(`Invalid source filename: ${basename}`);
    }
    if (Object.hasOwn(app, 'key')) throw new Error('Source record must not contain key');
    return { ...app };
};

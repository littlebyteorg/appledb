const Ajv = require("ajv");
const addFormats = require("ajv-formats");
const glob = require("glob");

process.chdir(__dirname);

const ajv = new Ajv({ allErrors: true});
addFormats(ajv);

const schema = require("../schemas/osFiles.json");
const validator = ajv.compile(schema);

const filesToValidate = [
    "../osFiles/**/*.json"
]

var total = 0, failed = 0;

for (const pattern of filesToValidate) {
    const files = glob.sync(pattern);
    for (const file of files) {
        total++;
    
        const data = require(file);
        const valid = validator(data);
        if (!valid) {
            failed++;
            console.error(`${file} failed validation`);
            console.error(validator.errors);
        }
    }
}

if (failed) {
    console.error(`${failed}/${total} files failed`);
    process.exit(1);
} else {
    console.log(`${total} files passed`);
    process.exit(0);
}
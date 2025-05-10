import Ajv from "ajv";
import addFormats from "ajv-formats";
import glob from "glob";
import { readFileSync } from "fs";

process.chdir(__dirname);

const ajv = new Ajv({ allErrors: true});
addFormats(ajv);

var total = 0, failed = 0;

function validate(schemaPath, filesToValidate) {
    const schema = JSON.parse(readFileSync(schemaPath))
    const validator = ajv.compile(schema);

    for (const pattern of filesToValidate) {
        const files = glob.sync(pattern);
        for (const file of files) {
            total++;

            const data = JSON.parse(readFileSync(file));
            const valid = validator(data);
            if (!valid) {
                failed++;
                console.error(`${file} failed validation`);
                console.error(validator.errors);
            }
        }
    }

}

validate("../schemas/osFiles.json", ["../osFiles/**/*.json"]);
validate("../schemas/deviceFiles.json", ["../deviceFiles/**/*.json"]);
validate("../schemas/deviceGroupFiles.json", ["../deviceGroupFiles/**/*.json"]);
validate("../schemas/jailbreakFiles.json", ["../jailbreakFiles/**/*.json"]);

if (failed) {
    console.error(`${failed}/${total} files failed`);
    process.exit(1);
} else {
    console.log(`${total} files passed`);
    process.exit(0);
}
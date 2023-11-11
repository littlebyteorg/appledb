import * as path from "path";
import { glob } from 'glob';
import { promisify } from 'util';
import * as util from "util";
import * as fs from 'graceful-fs';


test('all JSON files are valid', async () => {
    const root_dir = path.resolve(__dirname, '../')
    const files: Array<string> = await promisify(glob)("**/*.json", { cwd: root_dir, ignore: ["node_modules/**", "out/**"] })

    await Promise.all(files.map(async file => {
        // console.log(`reading file: ${file}`)
        try {
            const content = await util.promisify(fs.readFile)(file, "utf-8")
            expect(() => JSON.parse(content)).not.toThrow()
        } catch (err) {
            err.message = `Error parsing JSON file: ${file}\n${err.message}`
            throw err
        }
    }))
})
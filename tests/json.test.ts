import * as path from "path";
import { glob } from 'glob';
import { promisify } from 'util';
import * as util from "util";
import * as fs from 'graceful-fs';

test('all JSON files are valid', async () => {
    const root_dir = path.resolve(__dirname, '../')
    const search = path.resolve(root_dir, "**/*.json")
    console.log(`searchPath: ${search}`)

    const files = await promisify(glob)(search)

    await Promise.all(files.map(async file => {
        const content = await util.promisify(fs.readFile)(file, "utf-8")
        expect(content).toBeTruthy()
    }))
})
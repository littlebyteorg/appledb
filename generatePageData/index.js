const fs = require('fs')

if (!fs.existsSync('./out/appledb-web')) fs.mkdirSync('./out/appledb-web')
if (!fs.existsSync('./out/appledb-web/pageData')) fs.mkdirSync('./out/appledb-web/pageData')

fs.rmSync('./out/appledb-web/pageData', { recursive: true });
fs.mkdirSync('./out/appledb-web/pageData')

require('./generateFirmware')
//require('./generateDevicePage')
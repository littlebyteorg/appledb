const fs = require('fs')
const devArr = require('../grabData/device')
const groupArr = require('../grabData/deviceGroup')

fs.mkdirSync('./out/appledb-web/pageData/device')
fs.mkdirSync('./out/appledb-web/pageData/device/identifier')

function formatUrl(x) {
    const removeCharacters = [
        ' ',
        '/'
    ]

    for (const r of removeCharacters) x = x.replace(new RegExp(r,'g'),'-')

    return encodeURI(x)
}

const pageKeys = groupArr.map(x => { return {
    name: x.name,
    key: x.groupKey,
    url: `/device/${formatUrl(x.groupKey)}`,
    devices: x.devices
}}).concat(devArr.map(x => { return {
    name: x.name,
    key: x.key,
    url: `/device/identifier/${formatUrl(x.key)}`,
    devices: [x.key]
}}))

for (const p of pageKeys) require('./generatePage')(p)

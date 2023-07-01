const { getData } = require('apple-data')
const fs = require('fs')
const path = require('path')

function update_cores()
{
    this.async()
    const root_folder = path.resolve(__dirname, '../')
    const cores_data = getData('cores')
        .then(data => data.chip_ids)
        .then(data => {
            for (const core in data) {
                let revisionArr = []
                for (const r in data[core].revisions) {
                    let obj = data[core].revisions[r]
                    obj.type = `Revision ${r}`
                    revisionArr.push(obj)
                }

                let boardArr = Object.keys(data[core].boards).map(x => data[core].boards[x])
                let boardObj = {}
                for (const board of boardArr) boardObj[board.product_id] = board.board_name

                let capabilities
                if (data[core].capabilities) capabilities = data[core].capabilities

                let os
                if (data[core].os) os = {os: data[core].os}

                let infoObj = {}
                if (os || capabilities) {
                    infoObj = {
                        type: "Info",
                        ...os,
                        ...capabilities
                    }
                }

                let securerom
                if (data[core].securerom) securerom = {
                    type: "SecureRom",
                    ...data[core].securerom.nonce,
                    demotion_reg: data[core].securerom.demotion_reg,
                    ...data[core].securerom.memory_layout
                }

                let objData = [
                    infoObj,
                    ...revisionArr,
                    securerom,
                    {
                        type: "Boards",
                        ...boardObj
                    }
                ].filter(x => x && Object.keys(x).length)

                let arch
                if (data[core].architecture) arch = {arch: data[core].architecture}

                let name
                if (data[core].name && data[core.description]) name = data[core].name + ' (' + data[core].description + ')'
                if (data[core].name) name = data[core].name
                if (data[core].description) name = data[core].description
                if (!name) name = core

                let retObj = {
                    name: name,
                    key: core,
                    type: "Chip",
                    ...arch,
                    info: objData
                }

                fs.writeFile(path.join(root_folder, `./deviceFiles/Chip/${core}.json`), JSON.stringify(retObj, null, 2), (err) => {
                    if (err) console.log(err)
                })
            }
        })
}

module.exports = function register(grunt) {
    grunt.registerTask('generate:chips', 'Generate chip data', update_cores)
}
const fs = require('fs')
const path = require('path')
const hash = require('object-hash')
const p = './deviceGroupFiles'

function getAllFiles(dirPath, arrayOfFiles) {
    files = fs.readdirSync(dirPath)
  
    arrayOfFiles = arrayOfFiles || []
  
    files.forEach(function(file) {
      if (fs.statSync(dirPath + "/" + file).isDirectory()) {
        arrayOfFiles = getAllFiles(dirPath + "/" + file, arrayOfFiles)
      } else {
        arrayOfFiles.push(path.join(dirPath, "/", file))
      }
    })
  
    return arrayOfFiles
}

var deviceGroupFiles = []
deviceGroupFiles = getAllFiles(p, deviceGroupFiles)
deviceGroupFiles = deviceGroupFiles.filter(file => file.endsWith('.json'));
deviceGroupFiles = deviceGroupFiles.map(function(x) {
    const filePathStr = x.split(path.sep)
    const pathStrLength = p.split('/').length - 2
    
    return filePathStr.splice(pathStrLength, filePathStr.length).join(path.sep)
})

var devGroupArr = []
for (const file in deviceGroupFiles) {
  const group = require('../../' + deviceGroupFiles[file])
  if (group.key) group.groupKey = group.key
  devGroupArr.push(group)
}

const devArr = require('./device')

const devicesInDeviceGroups = devGroupArr.map(x => x.devices).flat()
const ungroupedDevices = devArr.filter(x => !devicesInDeviceGroups.includes(x.key) && x.group !== false)
const nowPutThemInGroups = ungroupedDevices.map(x => {
  return {
    name: x.name,
    type: x.type,
    devices: [x.key]
  }
})

devGroupArr = devGroupArr
.concat(nowPutThemInGroups)
.map(function(x) {
  if (x.devices) {
    const devMap = x.devices.map(y => {
      const dev = devArr.filter(x => x.key === y)
      if (dev.length < 1) console.log(`ERROR: Device '${y}' not found`)
      return dev[0]
    }).filter(x => x)
    x.soc = Array.from(new Set(devMap.map(y => y.soc)))
    x.arch = Array.from(new Set(devMap.map(y => y.arch)))
    x.released = Array.from(new Set(devMap.map(y => y.released))).flat()
    .map(x => new Date(x).valueOf()).sort()[0]
  }

  return x
})
.filter(x => x)

deviceGroupsWithoutReleaseDate = devGroupArr
.filter(x => !x.released)
.sort((a,b) => {
  if (a.subtype) a.type = [a.type,a.subtype].join('')
  if (b.subtype) b.type = [b.type,b.subtype].join('')

  if (a.type < b.type) return -1
  if (a.type > b.type) return 1

  if (a.name > b.name) return -1
  if (a.name < b.name) return 1

  return 0
})

deviceGroupsWithReleaseDate = devGroupArr
.filter(x => x.released)
.sort((a,b) => {
  if (a.subtype) a.type = [a.type,a.subtype].join('')
  if (b.subtype) b.type = [b.type,b.subtype].join('')

  if (a.type < b.type) return -1
  if (a.type > b.type) return 1

  if (a.released < b.released) return 1
  if (a.released > b.released) return -1

  if (a.name > b.name) return -1
  if (a.name < b.name) return 1

  return 0
})

module.exports = [
  ...deviceGroupsWithReleaseDate,
  ...deviceGroupsWithoutReleaseDate
].map(x => {
  if (!x.groupKey) {
    if (x.devices.length == 1) x.groupKey = x.devices[0]
    else x.groupKey = x.name
  }
  x.hash = hash(x)
  return x
})
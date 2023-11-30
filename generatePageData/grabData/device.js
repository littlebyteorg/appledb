const fs = require('fs')
const path = require('path')
const hash = require('object-hash')
const request = require('sync-request')
const p = './deviceFiles'

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

var deviceFiles = []
deviceFiles = getAllFiles(p, deviceFiles)
deviceFiles = deviceFiles.filter(file => file.endsWith('.json'));
deviceFiles = deviceFiles.map(function(x) {
    const filePathStr = x.split(path.sep)
    const pathStrLength = p.split('/').length - 2
    
    return filePathStr.splice(pathStrLength, filePathStr.length).join(path.sep)
})

let imgJson = []
try {
  const req = request(
    'GET',
    'https://img.appledb.dev/main.json'
  ).getBody('utf8')
  if (!fs.existsSync('./cache')) fs.mkdirSync('./cache')
  fs.writeFileSync('./cache/imgArr.json', req)

  imgJson = JSON.parse(req)
} catch {
  if (fs.existsSync('./cache/imgArr.json'))
    imgJson = require('../../../cache/imgArr.json')
}

let imgArr = imgJson.map(x => {
  return {
    key: x.key,
    imgCount: x.count,
    dark: x.dark
  }
})

var devArr = []

for (const file in deviceFiles) {
  const obj = require('../../' + deviceFiles[file])

  for (const p of ['model','board','identifier']) {
    if (!obj[p]) obj[p] = []
    if (!Array.isArray(obj[p])) obj[p] = [obj[p]]
  }

  obj.name = obj.name || obj.identifier[0] || obj.key
  obj.key = obj.key || obj.identifier[0] || obj.name

  let imgObj = {
    count: 0,
    dark: true,
    key: 'logo'
  }

  let devImgObj = imgArr.find(x => x.key == obj.key)
  if (devImgObj) {
    imgObj.count = devImgObj.imgCount
    imgObj.dark = devImgObj.dark
    imgObj.key = obj.key
  }
  
  obj.img = imgObj

  if (obj.info) obj.info = obj.info.map(o => {
    if (o.type != 'Display') return o
    if (o.Resolution && o.Screen_Size) {
      const diagRes = Math.sqrt(Math.pow(o.Resolution.x, 2) + Math.pow(o.Resolution.y, 2))
      const size = parseInt(o.Screen_Size.replace('"',''))
      const ppi = Math.round(diagRes / size)

      let newObj = {}
      newObj.type = o.type
      newObj.Resolution = o.Resolution
      newObj.Screen_Size = o.Screen_Size
      newObj.Pixels_per_Inch = ppi
      for (const i of Object.keys(o).filter(x => x != 'Resolution' || x != 'Screen_Size'))
        newObj[i] = o[i]

      return newObj
    }
  })
  
  devArr.push(obj)
}

module.exports = devArr.map(x => {
  x.hash = hash(x)
  return x
})
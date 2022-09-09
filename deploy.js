const cname = 'api.appledb.dev'
const { create } = require('domain')
const fs = require('fs')
const path = require('path')
const hash = require('object-hash')

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

function requireAll(p, fileType) {
  return getAllFiles(p)
  .filter(f => f.endsWith(fileType))
  .map(f => require('.' + path.sep + f))
}

function mkdir(p) {
  if (!fs.existsSync(p)) {
    fs.mkdirSync(p)
    return true
  }
  else return false
}

function write(p, f) {
  fs.writeFileSync(p, f)
  filesWritten++
}

function writeJson(dirName, arr, property) {
  mkdir(path.join(p, dirName))
  write(path.join(p, dirName, 'index.json'), JSON.stringify(arr.map(x => x[property]), null, 2))
  write(path.join(p, dirName, 'main.json'), JSON.stringify(arr, null, 2))
  arr.map(function(x) { write(path.join(p, dirName, x[property].replace('/','%2F') + '.json'), JSON.stringify(x, null, 2))})

  main[dirName] = arr
}

var iosFiles          = requireAll('iosFiles', '.json'),
    jailbreakFiles    = requireAll('jailbreakFiles', '.js'),
    deviceGroupFiles  = requireAll('deviceGroupFiles', '.json'),
    deviceFiles       = requireAll('deviceFiles', '.json'),
    bypassTweaks      = requireAll('bypassTweaks', '.json'),
    bypassApps        = requireAll('bypassApps', '.json')

deviceFiles = deviceFiles.map(function(dev) {
  for (const p of ['model','board','identifier']) {
    if (!dev[p]) dev[p] = []
    if (!Array.isArray(dev[p])) dev[p] = [dev[p]]
  }

  if (!dev.key) dev.key = dev.identifier[0] || dev.name

  if (dev.info) dev.info = dev.info.map(o => {
    if (o.type != 'Display') return o
    if (o.Resolution && o.Screen_Size) {
      const diagRes = Math.sqrt(Math.pow(o.Resolution.x, 2) + Math.pow(o.Resolution.y, 2))
      const size = parseInt(o.Screen_Size.replace('"',''))
      const ppi = Math.round(diagRes / size)
      o.Pixels_per_Inch = ppi
      return o
    }
  })

  return dev
})

deviceGroupFiles = deviceGroupFiles.map(g => {
  if (!g.hideChildren) g.hideChildren = false
  if (!g.key) g.key = g.name

  return g
}).sort((a,b) => {
  function getReleased(dev) {
    let ret = deviceFiles.filter(x => x.key == dev)[0].released
    if (!Array.isArray(ret)) ret = [ret]
    return new Date(ret[0]).valueOf()
  }
  const released = [a,b].map(x => getReleased(x.devices[0]))
  const type = [a,b].map(x => x.type)
  if (type[0] < type[1]) return -1
  if (type[0] > type[1]) return 1
  if (released[0] < released[1]) return -1
  if (released[0] > released[1]) return 1
  return 0
})

const deviceGroupKeyArr = deviceGroupFiles.map(x => x.devices).flat()
const devicesWithNoGroup = deviceFiles.filter(x => !deviceGroupKeyArr.includes(x.key) && x.group !== false)
const nowPutThemInGroups = devicesWithNoGroup.map(x => {
  return {
    name: x.name,
    type: x.type,
    devices: [x.key]
  }
})

deviceGroupFiles = deviceGroupFiles.concat(nowPutThemInGroups)

let counter = 0
let lastDevType = ''
for (const group of deviceGroupFiles) {
  if (group.type == lastDevType) {
    counter++
    group.order = counter
  } else {
    counter = 0
    group.order = counter
    lastDevType = group.type
  }
}

let createDuplicateEntriesArray = []

for (let i of iosFiles) {
  if (!i.hasOwnProperty('createDuplicateEntries')) continue
  for (const entry of i.createDuplicateEntries) {
    let ver = { ...i }
    delete ver.createDuplicateEntries
    for (const property in entry) {
      ver[property] = entry[property]
    }
    createDuplicateEntriesArray.push(ver)
  }
  delete i.createDuplicateEntries
}

iosFiles = iosFiles
.concat(createDuplicateEntriesArray)
.map(function(ver) {
  if (!ver.uniqueBuild) ver.uniqueBuild = ver.build
  if (!ver.key) ver.key = ver.osStr + ';' + ver.uniqueBuild
  if (!ver.beta) ver.beta = false
  /*if (!ver.sortVersion) {
    if (ver.iosVersion) ver.sortVersion = ver.iosVersion
    else ver.sortVersion = ver.version
  }*/
  if (!ver.deviceMap) ver.deviceMap = []
  if (!ver.released) ver.released = ''
  
  ver.osType = ver.osStr
  if (ver.osType == 'iPhoneOS' || ver.osType == 'iPadOS') ver.osType = 'iOS'
  if (ver.osType == 'Apple TV Software') ver.osType = 'tvOS'

  function getLegacyDevicesObjectArray() {
    let obj = {}
    ver.deviceMap.map(x => obj[x] = {})
    if (!ver.sources) return obj

    ver.deviceMap.map(x => {
      const source = ver.sources.filter(y => y.deviceMap.includes(x))[0]
      if (!source) return
      const type = source.type
      const linksArr = source.links
      const link = linksArr.filter(x => {
        if (linksArr.some(x => x.preferred)) return x.preferred
        else return true
      })[0].url
      obj[x][type] = link
    })
    return obj
  }

  ver.devices = getLegacyDevicesObjectArray()

  ver.appledburl = encodeURI(`https://appledb.dev/firmware/${ver.osStr.replace(/ /g,'-')}/${ver.uniqueBuild}`)

  return ver
})

jailbreakFiles = jailbreakFiles.map(function(jb) {
  if (jb.info.guide) {
    jb.info.guide = jb.info.guide.map(function(g) {
      if ((g.name || g.text) && g.url) {
        if (!g.name) g.name = g.text
        else if (!g.text) g.text = g.name
        g.validGuide = true
      }
      else g.validGuide = false
      g.text = (g.text) ? g.text : 'none'
      g.name = (g.name) ? g.name : 'none'
      g.url = (g.url) ? g.url : ''
      g.pkgman = (g.pkgman) ? g.pkgman : 'none'
      return g
    })
  }
  return jb
})

bypassApps = bypassApps.map(function(app) {
  if (!app.bypasses) return JSON.stringify(app)

  app.bypasses = app.bypasses.map(function(b) {
    if (!b.name) return b
    
    var bypassObj = bypassTweaks.filter(t => t.name == b.name)[0]
    if (b.notes) bypassObj.appNotes = b.notes

    return bypassObj
  })

  return JSON.stringify(app)
})

bypassApps = bypassApps.map(x => JSON.parse(x)) // This is extremely dumb but necessary for some reason

const p = 'out'
mkdir(p)
fs.writeFileSync(`${p}/CNAME`, cname)

var main = {}
var filesWritten = 0

writeJson('ios', iosFiles, 'key')
writeJson('jailbreak', jailbreakFiles, 'name')
writeJson('group', deviceGroupFiles, 'name')
writeJson('device', deviceFiles, 'key')
writeJson('bypass', bypassApps, 'bundleId')

write(path.join(p, 'main.json'), JSON.stringify(main))
write(path.join(p, 'hash'), hash(main))

var dirName = path.join(p, 'compat')
mkdir(dirName)
iosFiles.map(function(fw) {
  if (fw.deviceMap) fw.deviceMap.map(function(dev) {
    mkdir(path.join(dirName, dev))
    var jb = jailbreakFiles.filter(function(x) {
      if (x.hasOwnProperty('compatibility')) return x.compatibility.filter(function(y) {
        return y.devices.includes(dev) && y.firmwares.includes(fw.uniqueBuild)
      }).length > 0
    }).sort((a,b) => a.priority - b.priority)
    write(path.join(dirName, dev, fw.uniqueBuild + '.json'), JSON.stringify(jb, null, 2))
  })
})

console.log('Files Written:', filesWritten)

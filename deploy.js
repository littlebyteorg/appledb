const cname = 'api.appledb.dev'
const fs = require('fs')
const path = require('path')

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
  if (!fs.existsSync(p)) fs.mkdirSync(p)
}

function write(p, f) {
  fs.writeFileSync(p, f)
  filesWritten++
}

function writeJson(dirName, arr, property) {
  var obj = {}
  arr.map(function(x) { obj[x[property]] = x })

  mkdir(path.join(p, dirName))
  write(path.join(p, dirName, 'index.json'), JSON.stringify(arr.map(x => x[property]), null, 2))
  write(path.join(p, dirName, 'main.json'), JSON.stringify(obj, null, 2))
  arr.map(function(x) { write(path.join(p, dirName, x[property] + '.json'), JSON.stringify(x, null, 2))})

  main[dirName] = obj
}

var iosFiles          = requireAll('iosFiles', '.json'),
    jailbreakFiles    = requireAll('jailbreakFiles', '.js'),
    deviceGroupFiles  = requireAll('deviceGroupFiles', '.json'),
    deviceFiles       = requireAll('deviceFiles', '.json'),
    bypassTweaks      = requireAll('bypassTweaks', '.json'),
    bypassApps        = requireAll('bypassApps', '.json')

iosFiles = iosFiles.map(function(ver) {
  if (!ver.uniqueBuild) ver.uniqueBuild = ver.build
  if (!ver.beta) ver.beta = false
  if (!ver.sortVersion) {
    if (ver.iosVersion) ver.sortVersion = ver.iosVersion
    else ver.sortVersion = ver.version
  }
  if (!ver.devices) ver.devices = {}
  return ver
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

writeJson('ios', iosFiles, 'uniqueBuild')
writeJson('jailbreak', jailbreakFiles, 'name')
writeJson('group', deviceGroupFiles, 'name')
writeJson('device', deviceFiles, 'identifier')
writeJson('bypass', bypassApps, 'bundleId')

write(path.join(p, 'main.json'), JSON.stringify(main))

var dirName = path.join(p, 'compat')
mkdir(dirName)
iosFiles.map(function(fw) {
  if (fw.devices) Object.keys(fw.devices).map(function(dev) {
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
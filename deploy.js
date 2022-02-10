const fs = require('fs')
const path = require('path')
const cname = 'api.appledb.dev'

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

var iosFiles          = requireAll('iosFiles', '.json'),
    jailbreakFiles    = requireAll('jailbreakFiles', '.js'),
    deviceGroupFiles  = requireAll('deviceGroupFiles', '.json'),
    deviceFiles       = requireAll('deviceFiles', '.json'),
    bypassTweaks      = requireAll('bypassTweaks', '.json'),
    bypassApps        = requireAll('bypassApps', '.json')

bypassApps = bypassApps.map(function(f) {
  if (f.bypasses == null) return f
  
  f.bypasses = f.bypasses.map(function(b) {
    var bpName
    var notes
    var bypass

    if (b.name) bpName = b.name
    if (b.notes) notes = b.notes
    if (bpName) bypass = bypassTweaks.filter(x => x.name == bpName)[0]
    if (notes && bpName) bypass.notes = notes

    return bypass
  })
  return f
})

const p = 'out'
mkdir(p)
fs.writeFileSync(`${p}/CNAME`, cname)

var main = {}
var filesWritten = 0

function writeJson(dirName, arr, property) {
  var obj = {}
  arr.map(function(x) { obj[x[property]] = x })

  mkdir(path.join(p, dirName))
  fs.writeFileSync(path.join(p, dirName, 'index.json'), JSON.stringify(arr.map(x => x[property]), null, 2))
  filesWritten++
  fs.writeFileSync(path.join(p, dirName, 'main.json'), JSON.stringify(obj, null, 2))
  filesWritten++
  arr.map(function(x) {
    fs.writeFileSync(path.join(p, dirName, x[property] + '.json'), JSON.stringify(x, null, 2))
    filesWritten++
  })

  main[dirName] = obj
}

writeJson('ios', iosFiles, 'uniqueBuild')
writeJson('jailbreak', jailbreakFiles, 'name')
writeJson('group', deviceGroupFiles, 'name')
writeJson('device', deviceFiles, 'identifier')
writeJson('bypass', bypassApps, 'bundleId')

fs.writeFileSync(path.join(p, 'main.json'), JSON.stringify(main))
filesWritten++

var dirName = path.join(p, 'compat')
mkdir(dirName)
iosFiles.map(function(fw) {
  Object.keys(fw.devices).map(function(dev) {
    mkdir(path.join(dirName, dev))
    var jb = jailbreakFiles.filter(function(x) {
      if (x.hasOwnProperty('compatibility')) return x.compatibility.filter(function(y) {
        return y.devices.includes(dev) && y.firmwares.includes(fw.uniqueBuild)
      }).length > 0
    }).sort((a,b) => a.priority - b.priority)
    fs.writeFileSync(path.join(dirName, dev, fw.uniqueBuild + '.json'), JSON.stringify(jb, null, 2))
    filesWritten++
  })
})

console.log('Files Written:', filesWritten)
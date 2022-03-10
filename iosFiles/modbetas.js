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

var inBeta = requireAll('./in','.json')
inBeta.map(function(x) {
  var uniqueBuild = [x.build,x.version.split(' ')[1]].join('-')
  var o = {
    osStr: x.osStr,
    version: x.version,
    build: x.build,
    uniqueBuild: uniqueBuild,
    released: x.released
  }
  fs.writeFile(`out/${uniqueBuild}.json`, JSON.stringify(o,null,2), (err) => {
    if (err) console.log(err)
  })
})
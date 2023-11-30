const fs = require('fs')
const path = require('path')
const p = './jailbreakFiles'

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

var jbFiles = []
jbFiles = getAllFiles(p, jbFiles)
jbFiles = jbFiles.filter(file => file.endsWith('.js'));
jbFiles = jbFiles.map(function(x) {
    const filePathStr = x.split(path.sep)
    const pathStrLength = p.split('/').length - 2
    
    return filePathStr.splice(pathStrLength, filePathStr.length).join(path.sep)
})

var jbArr = []
for (const file in jbFiles) jbArr.push(require('../../' + jbFiles[file]))

module.exports = jbArr
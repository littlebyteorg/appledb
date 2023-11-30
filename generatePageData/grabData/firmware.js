const fs = require('fs')
const path = require('path')
const osFilesPath = './osFiles'

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

function handleSDKs(baseItem) {
  var sdkEntries = []
  if (!baseItem.hasOwnProperty('sdks')) return sdkEntries

  baseItem['sdks'].forEach(function(sdk) {
    sdk['version'] = sdk['version'] + ' SDK'
    sdk['uniqueBuild'] = sdk['build'] + '-SDK'
    sdk['released'] = baseItem['released']
    sdk['deviceMap'] = [(sdk['osStr'].indexOf('OS X') >= 0 ? 'macOS' : sdk['osStr']) + ' SDK']
    sdk['sdk'] = true
    sdkEntries.push(sdk)
  })

  return sdkEntries
}

var osFiles = getAllFiles(osFilesPath)
osFiles = osFiles.filter(file => file.endsWith('.json'));
osFiles = osFiles.map(function(x) {
    const filePathStr = x.split(path.sep)
    const pathStrLength = osFilesPath.split('/').length - 2
    
    return filePathStr.splice(pathStrLength, filePathStr.length).join(path.sep)
})

var osArr = []
for (const file of osFiles) {
  let os = require('../../' + file)
  if (os.sources) os.sources = os.sources.filter(x => x.type != 'ota')
  osArr.push(os)
}

let createDuplicateEntriesArray = []

for (let i of osArr) {
    if (!i.hasOwnProperty('createDuplicateEntries') && !i.hasOwnProperty('sdks')) continue
    for (const entry of (i.createDuplicateEntries || [])) {
      let ver = { ...i }
      delete ver.createDuplicateEntries
      for (const property in entry) {
        ver[property] = entry[property]
      }
      createDuplicateEntriesArray.push(ver)
      createDuplicateEntriesArray = createDuplicateEntriesArray.concat(handleSDKs(entry))
    }
    delete i.createDuplicateEntries
    createDuplicateEntriesArray = createDuplicateEntriesArray.concat(handleSDKs(i))
}

let ret = osArr
.concat(createDuplicateEntriesArray)
.map(function(x) {
    if (!x.deviceMap) x.deviceMap = []
    if (!x.uniqueBuild) x.uniqueBuild = x.build || x.version
    if (!x.beta) x.beta = false
    if (!x.rc) x.rc = false

    x.path = '/firmware/' + [x.osStr.replace(/ /g,'-'), x.uniqueBuild].join('/') + '.html'
    
    return x
})

if (process.env.npm_config_argv) {
  let args = JSON.parse(process.env.npm_config_argv).original
  if (process.env.npm_lifecycle_script && !args.filter(x => x.includes('limitfw=')).length) args = process.env.npm_lifecycle_script.split(' ')
  if (args.filter(x => x.includes('limitfw=')).length) {
    let limitfwArg = args.find(x => x.includes('limitfw='))
    let fwCount = parseInt(limitfwArg.split('=').slice(1))
    if (fwCount > 0) {
      console.log(`Limited to ${fwCount} firmware${fwCount.length == 1 ? 's' : ''}`)
      ret = ret.slice(0,fwCount)
    } else {
      console.log('limitfw integer not valid')
    }
  }
}

module.exports = ret
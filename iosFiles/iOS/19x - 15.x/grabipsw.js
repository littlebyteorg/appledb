var request = require('request')
var fs = require('fs')
var path = require('path')
var { parse } = require('node-html-parser')

const devTypeLookup = {
  TV: "Apple_TV",
  Watch: "Apple_Watch",
  Home: "HomePod",
  Mac: "Mac",
  iPad: "iPad",
  Air: "iPad_Air",
  Pro: "iPad_Pro",
  mini: "iPad_mini",
  iPhone: "iPhone",
  iPod: "iPod_touch"
}

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

const version = require(process.argv[2])
const build = version.build
const devices = requireAll('../../deviceFiles', '.json')

Object.keys(version.devices).map(function(x) {
  var url
  if (version.beta) url = `https://api.m1sta.xyz/betas/${x}`
  else url = `https://api.ipsw.me/v4/ipsw/${x}/${build}`

  request(url, function (error, response, body) {
    if (version.beta) response = JSON.parse(body).filter(x => x.buildid == build)[0]
    else response = JSON.parse(body)

    if (response) response = response.url
    else response = "none"

    if (response == "none" && version.beta) {
      const deviceType = devTypeLookup[devices.filter(d => d.identifier == x)[0].type]
      const versionForUrl = version.version.split('.')[0] + '.x'
      url = `https://www.theiphonewiki.com/wiki/Beta_Firmware/${deviceType}/${versionForUrl}`

      request(url, function (error, response, body) {
        var verArr = parse(body.toString())
        .querySelectorAll('table').map(a => a
          .querySelectorAll('tr').map(b => b
            .querySelectorAll('td').map(c => c
              .innerHTML.replace('\n', '')
            )
            .filter(c => !(/\d\.\d\d\.\d\d/g.test(c) || c == '?'))
            .filter((c, index) => !(index == 0 && c.includes('.')))
            .slice(0, -1)
            .filter(c => !c.includes('class="date"'))
            .map(function(c) {
              if (c.includes('https://')) return parse(c).querySelector('a').attributes.href
              else if (c.includes('/w/index.php?')) return parse(c).structuredText.split('\n')
              else return c
            })
          )
          .filter(b => JSON.stringify(b) != JSON.stringify([]))
          .filter(b => b[0] == version.build)
          .filter(b => b[1].includes(x))
        ).filter(a => JSON.stringify(a) != JSON.stringify([]))[0]

        response = "none"

        if (verArr) {
          verArr = verArr[0]
          if (verArr.length > 2 && verArr[2].includes('https://') && verArr[2].includes('.ipsw'))
            response = verArr[2]
        }

        console.log(`"${x}": {\n  "ipsw": "${response}"\n},`)
      })

    } else console.log(`"${x}": {\n  "ipsw": "${response}"\n},`)
  })
})
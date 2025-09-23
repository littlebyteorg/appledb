const cname = "api.appledb.dev";
import fs from "fs";
import path from "path";
import hash from "object-hash";
import zlib from "zlib";
import lzma from "lzma-native";
import { createRequire } from "module";
const require = createRequire(import.meta.url);

function getAllFiles(dirPath, arrayOfFiles) {
  var files = fs.readdirSync(dirPath);
  arrayOfFiles = arrayOfFiles || [];
  files.forEach(function (file) {
    if (fs.statSync(dirPath + "/" + file).isDirectory()) {
      arrayOfFiles = getAllFiles(dirPath + "/" + file, arrayOfFiles);
    } else {
      arrayOfFiles.push(path.join(dirPath, "/", file));
    }
  });
  return arrayOfFiles;
}

function requireAll(p, fileType) {
  return getAllFiles(p)
    .filter((f) => f.endsWith(fileType))
    .map((f) => require("." + path.sep + f));
}

function mkdir(p) {
  if (!fs.existsSync(p)) {
    fs.mkdirSync(p);
    return true;
  } else return false;
}

function write(p, f) {
  fs.writeFileSync(p, f);
  filesWritten++;
}

async function writeCompressed(p, f) {
  console.time(`compressing ${p}, gz`);
  write(p + ".gz", zlib.gzipSync(f));
  console.timeEnd(`compressing ${p}, gz`);
  console.time(`compressing ${p}, xz2`);
  write(p + ".xz", await lzma.compress(f, { threads: 0 }));
  console.timeEnd(`compressing ${p}, xz2`);
}

async function writeJson(dirName, arr, property, makeSmaller = (data) => data, individual = true) {
  mkdir(path.join(p, dirName));
  console.time(`writing ${dirName} index.json`);
  write(
    path.join(p, dirName, "index.json"),
    JSON.stringify(arr.map((x) => x[property])),
  );
  console.timeEnd(`writing ${dirName} index.json`);
  console.time(`writing ${dirName} main.json`);
  write(path.join(p, dirName, "main.json"), JSON.stringify(makeSmaller(arr)));
  console.timeEnd(`writing ${dirName} main.json`);
  console.time(`writing ${dirName} main.json compressed`);
  await writeCompressed(path.join(p, dirName, "main.json"), JSON.stringify(arr));
  console.timeEnd(`writing ${dirName} main.json compressed`);
  if (individual) {
    console.time(`writing ${dirName} individual json files`);
    arr.map(function (x) {
      write(
        path.join(p, dirName, x[property].replace("/", "%2F") + ".json"),
        JSON.stringify(x),
      );
    });
    console.timeEnd(`writing ${dirName} individual json files`);
  }
}

function handleSDKs(baseItem) {
  var sdkEntries = [];
  if (!baseItem.hasOwnProperty("sdks")) return sdkEntries;

  for (var sdk of baseItem["sdks"]) {
    sdk["version"] = sdk["version"] + " SDK";
    sdk["uniqueBuild"] = (sdk["build"] || sdk["version"]) + "-" + (baseItem["uniqueBuild"] || baseItem["build"] || baseItem["version"]) + "-SDK";
    sdk["released"] = baseItem["released"];
    sdk["deviceMap"] = [
      (sdk["osStr"].indexOf("OS X") >= 0 ? "macOS" : sdk["osStr"]) + " SDK",
    ];
    sdk["sdk"] = true;
    sdkEntries.push(sdk);
  }

  return sdkEntries;
}

console.time("loading files");
var osFiles = requireAll("osFiles", ".json"),
  jailbreakFiles = requireAll("jailbreakFiles", ".json"),
  deviceGroupFiles = requireAll("deviceGroupFiles", ".json"),
  deviceFiles = requireAll("deviceFiles", ".json"),
  bypassTweaks = requireAll("bypassTweaks", ".json"),
  bypassApps = requireAll("bypassApps", ".json");
console.timeEnd("loading files");

deviceFiles = deviceFiles.map(function (dev) {
  for (const p of ["model", "board", "identifier"]) {
    if (!dev[p]) dev[p] = [];
    if (!Array.isArray(dev[p])) dev[p] = [dev[p]];
  }

  if (!dev.key) dev.key = dev.identifier[0] || dev.name;
  if (!dev.imageKey) dev.imageKey = dev.key

  if (dev.info)
    dev.info = dev.info.map((o) => {
      if (o.type != "Display") return o;
      if (o.Resolution && o.Screen_Size) {
        const diagRes = Math.sqrt(
          Math.pow(o.Resolution.x, 2) + Math.pow(o.Resolution.y, 2),
        );
        const size = parseInt(o.Screen_Size.replace('"', ""));
        const ppi = Math.round(diagRes / size);
        o.Pixels_per_Inch = ppi;
        return o;
      }
    });
  
    if (dev.colors)
      dev.colors = dev.colors.map((c) => {
        if (!c.key) c.key = c.name
        return c
      })

  return dev;
});

const deviceGroupKeyArr = deviceGroupFiles.map((x) => x.devices).flat();
const devicesWithNoGroup = deviceFiles.filter(
  (x) => !deviceGroupKeyArr.includes(x.key) && x.group !== false,
);
const nowPutThemInGroups = devicesWithNoGroup.map((x) => {
  return {
    name: x.name,
    type: x.type,
    devices: [x.key],
  };
});

deviceGroupFiles = deviceGroupFiles
  .concat(nowPutThemInGroups)
  .map((g) => {
    if (!g.hideChildren) g.hideChildren = false;
    if (!g.key) g.key = g.name;

    return g;
  })
  .sort((a, b) => {
    function getReleased(dev) {
      let ret = deviceFiles.filter((x) => x.key == dev)[0].released;
      if (!Array.isArray(ret)) ret = [ret];
      return new Date(ret[0]).valueOf();
    }
    const released = [a, b].map((x) => getReleased(x.devices[0]));
    const type = [a, b].map((x) => x.type);
    if (type[0] < type[1]) return -1;
    if (type[0] > type[1]) return 1;
    if (released[0] < released[1]) return -1;
    if (released[0] > released[1]) return 1;
    return 0;
  });

let counter = 0;
let lastDevType = "";
for (const group of deviceGroupFiles) {
  if (group.type == lastDevType) {
    counter++;
    group.order = counter;
  } else {
    counter = 0;
    group.order = counter;
    lastDevType = group.type;
  }
}

let createDuplicateEntriesArray = [];

for (let i of osFiles) {
  if (!i.hasOwnProperty("createDuplicateEntries") && !i.hasOwnProperty("sdks"))
    continue;
  for (const entry of i.createDuplicateEntries || []) {
    let ver = { ...i };
    delete ver.createDuplicateEntries;
    for (const property in entry) {
      ver[property] = entry[property];
    }
    createDuplicateEntriesArray.push(ver);

    createDuplicateEntriesArray = createDuplicateEntriesArray.concat(
      handleSDKs(entry),
    );
  }
  delete i.createDuplicateEntries;
  createDuplicateEntriesArray = createDuplicateEntriesArray.concat(
    handleSDKs(i),
  );
}
let filterOTAsArray = ["audioOS", "tvOS", "watchOS", "iOS", "HomePod Software"];
osFiles = osFiles.concat(createDuplicateEntriesArray).map(function (ver) {
  if (!ver.uniqueBuild) ver.uniqueBuild = ver.build || ver.version;
  if (!ver.key) ver.key = ver.osStr + ";" + ver.uniqueBuild;
  if (!ver.beta) ver.beta = false;
  if (!ver.rc) ver.rc = false;
  if (!ver.deviceMap) ver.deviceMap = [];
  if (!ver.released) ver.released = "";

  if (ver.preinstalled === true) ver.preinstalled = ver.deviceMap;
  else if (!ver.preinstalled) ver.preinstalled = [];
  if (ver.signed === true) ver.signed = ver.deviceMap;
  else if (!ver.signed) ver.signed = [];

  ver.osType = ver.osStr;
  if (ver.osType == "iPhone Software" || ver.osType == "iPhone OS" || ver.osType == "iPadOS") ver.osType = "iOS";
  else if (ver.osType == "Apple TV Software") ver.osType = "tvOS";
  else if (ver.osType == "audioOS") ver.osType = "HomePod Software";
  else if (ver.osType == "Mac OS X" || ver.osType == "OS X") ver.osType = "macOS";

  function getLegacyDevicesObjectArray() {
    let obj = {};
    ver.deviceMap.map((x) => (obj[x] = {}));
    if (!ver.sources) return obj;

    ver.deviceMap.map((x) => {
      const source = ver.sources.filter((y) => y.deviceMap.includes(x))[0];
      if (!source) return;
      const type = source.type;
      const linksArr = source.links;
      const link = linksArr.filter((x) => {
        if (linksArr.some((x) => x.preferred)) return x.preferred;
        else return true;
      })[0].url;
      obj[x][type] = link;
    });
    return obj;
  }

  ver.devices = getLegacyDevicesObjectArray();

  ver.appledburl = encodeURI(
    `https://appledb.dev/firmware/${ver.osStr.replace(/ /g, "-")}/${ver.uniqueBuild}`,
  );

  return ver;
});

jailbreakFiles = jailbreakFiles.map(function (jb) {
  if (jb.info.guide) {
    jb.info.guide = jb.info.guide.map(function (g) {
      if ((g.name || g.text) && g.url) {
        if (!g.name) g.name = g.text;
        else if (!g.text) g.text = g.name;
        g.validGuide = true;
      } else g.validGuide = false;
      g.text = g.text ? g.text : "none";
      g.name = g.name ? g.name : "none";
      g.url = g.url ? g.url : "";
      g.pkgman = g.pkgman ? g.pkgman : "none";
      return g;
    });
  }
  return jb;
});

bypassApps = bypassApps.map(function (app) {
  if (!app.bypasses) return app;

  app.bypasses = app.bypasses.map(function (b) {
    if (!b.name) return b;

    var bypassObj = bypassTweaks.filter((t) => t.name == b.name)[0];
    if (b.notes) bypassObj.appNotes = b.notes;

    return bypassObj;
  });

  return app;
});

const p = "out";
mkdir(p);
console.time("writing CNAME, .nojekyll, index.html");
fs.writeFileSync(`${p}/CNAME`, cname);
fs.writeFileSync(`${p}/.nojekyll`, "");
fs.writeFileSync(
  `${p}/index.html`,
  `
<!DOCTYPE HTML>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="0;url=https://github.com/littlebyteorg/appledb/blob/main/API.md" />
        <link rel="canonical" href="https://github.com/littlebyteorg/appledb/blob/main/API.md" />
    </head>
    <body>
        <h1>
            Redirecting to <a href="https://github.com/littlebyteorg/appledb/blob/main/API.md">https://github.com/littlebyteorg/appledb/blob/main/API.md</a>
        </h1>
    </body>
</html>
`,
);
console.timeEnd("writing CNAME, .nojekyll, index.html");

var filesWritten = 0;

function filterOTAs(ver) {
  ver = { ...ver };
  if (filterOTAsArray.indexOf(ver.osType) >= 0 && ver.sources)
    ver.sources = ver.sources.filter((source) => source.type != "ota");
  return ver;
}

await writeJson("ios", osFiles, "key", (data) => data.map(filterOTAs));

console.time("writing osFiles inner");
// Write index.json and main.json filtered by each osType
for (const [osType, fws] of Object.entries(Object.groupBy(osFiles, (x) => x.osType))) {
  await writeJson(`ios/${osType}`, fws, "key", (data) => data.map(filterOTAs), false);
}
console.timeEnd("writing osFiles inner");

console.time("writing jailbreakFiles");
await writeJson("jailbreak", jailbreakFiles, "name");
console.timeEnd("writing jailbreakFiles");
console.time("writing deviceGroupFiles");
await writeJson("group", deviceGroupFiles, "name");
console.timeEnd("writing deviceGroupFiles");
console.time("writing deviceFiles");
await writeJson("device", deviceFiles, "key");
console.timeEnd("writing deviceFiles");
console.time("writing bypassTweaks");
await writeJson("bypass", bypassApps, "bundleId");
console.timeEnd("writing bypassTweaks");

var main = {
  "ios": osFiles,
  "jailbreak": jailbreakFiles,
  "group": deviceGroupFiles,
  "device": deviceFiles,
  "bypass": bypassApps
};

console.time("writing main");
write(path.join(p, "main.json"), JSON.stringify({...main, "ios": osFiles.map(filterOTAs)}));
console.timeEnd("writing main");
console.time("writing main compressed");
await writeCompressed(path.join(p, "main.json"), JSON.stringify(main));
console.timeEnd("writing main compressed");
console.time("writing main hash");
write(path.join(p, "hash"), hash(JSON.stringify(main)));
console.timeEnd("writing main hash");

console.time("writing compatibility files");
var dirName = path.join(p, "compat");
mkdir(dirName);
osFiles.map(function (fw) {
  if (fw.deviceMap)
    fw.deviceMap.map(function (dev) {
      mkdir(path.join(dirName, dev));
      var jb = jailbreakFiles
        .filter(function (x) {
          if (x.hasOwnProperty("compatibility"))
            return (
              x.compatibility.filter(function (y) {
                return (
                  y.devices.includes(dev) &&
                  y.firmwares.includes(fw.uniqueBuild)
                );
              }).length > 0
            );
        })
        .sort((a, b) => a.priority - b.priority);
      write(
        path.join(dirName, dev, fw.uniqueBuild + ".json"),
        JSON.stringify(jb),
      );
    });
});
console.timeEnd("writing compatibility files");

// home page json

let homePage = require("./appledb-web/homePage.json");
homePage.softwareCount = osFiles.length;
homePage.deviceCount = deviceFiles.length;

let latestVersionArr = homePage['osVersionArray']

const latestVersions = latestVersionArr
.map(x => osFiles
  .filter(y => {
    if (y.version.includes('Simulator') || y.sdk || y.hideFromLatestVersions ) return false
    const osStrCheck = y.osStr == x.osStr
    const betaRcCheck = (y.beta || y.rc) == x.beta
    
    const check = osStrCheck && betaRcCheck && y.released

    let startsWith = x.version
    if (startsWith && y.version) {
      startsWith = y.version.startsWith(startsWith)
      if (check && startsWith && y.osStr == 'Bluetooth Headset Firmware') {
        return y.deviceMap.filter(z => z.startsWith("AirPods")).length
      }
      return check && startsWith
    }

    return check
  })
  .sort((a,b) => {
    const date = [a,b].map(x => new Date(x.released))
    if (date[0] < date[1]) return 1
    if (date[0] > date[1]) return -1
    if (a.deviceMap.length < b.deviceMap.length) return 1
    if (a.deviceMap.length > b.deviceMap.length) return -1
    if (a.build < b.build) return 1
    if (a.build > b.build) return -1
    return 0
  })[0])
.filter(x => x)
.map(x => {
  if (!x.released) return x
  if (x.released.includes(' ')) return x

  const dateOffset = (new Date().getTimezoneOffset() * 60 * 1000) + (60 * 60000)
  const currentDate = new Date(x.released).valueOf()
  const adjustedDate = new Date(currentDate + dateOffset)

  const releasedArr = x.released.split('-')
  const dateStyleArr = [{ year: 'numeric' }, { year: 'numeric', month: 'short' }, { dateStyle: 'medium' }]
  x.released =  new Intl.DateTimeFormat('en-US', dateStyleArr[releasedArr.length-1]).format(adjustedDate)
  x.releasedVal = adjustedDate.valueOf()

  return x
})
.sort((a,b) => {
  const dateRel = [a,b].map(x => new Date(x.released))
  if (dateRel[0] < dateRel[1]) return 1
  if (dateRel[0] > dateRel[1]) return -1

  if (a.osStr.toLowerCase() < b.osStr.toLowerCase()) return -1
  if (a.osStr.toLowerCase() > b.osStr.toLowerCase()) return 1

  if (a.version < b.version) return 1
  if (a.version > b.version) return -1
  return 0
}).reduce(((a, x) => {
  if (!a.hasOwnProperty(x.osStr)) a[x.osStr] = []
  const i = a[x.osStr].length
  const replaced = (i > 0 && a[x.osStr][0].version.split(" ")[0] >= x.version.split(" ")[0] && (x.beta || x.rc))
  a[x.osStr].push({'osStr': x.osStr, 'build': x.build, 'uniqueBuild': x.uniqueBuild, 'version': x.version, 'beta': x.beta, 'rc': x.rc, 'released': x.released, 'replaced': replaced})
  return a
}), {})

homePage['latestVersions'] = latestVersions

console.time("writing appledb-web files");
mkdir(`${p}/appledb-web`);
write(`${p}/appledb-web/homePage.json`, JSON.stringify(homePage));
console.timeEnd("writing appledb-web files");

// finish

console.log("Files Written:", filesWritten);

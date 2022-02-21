module.exports = {
  name: "EtasonATV",
  priority: 0,
  info: {
    website: {
      name: "etasonatv.tihmstar.net",
      url: "https://etasonatv.tihmstar.net/",
      external: true
    },
    wiki: {
      name: "theiphonewiki.com/wiki/EtasonATV",
      url: "https://www.theiphonewiki.com/wiki/EtasonATV",
      external: true
    },
    type: "Untethered",
    latestVer: "RC1",
    color: "#FFFF00",
    firmwares: ["7.4","7.5"]
  },
  compatibility: [
    {
      firmwares: [
        "12H876", // 7.4, AppleTV
      ],
      devices: [
        "AppleTV3,1", // Apple TV 3rd Gen (3,1), A5
        "AppleTV3,2", // Apple TV 3rd Gen (3,2), A5
      ]
    },
    {
      firmwares: [
        "12H885", // 7.5, AppleTV
      ],
      devices: [
        "AppleTV3,2", // Apple TV 3rd Gen (3,2), A5
      ]
    }
  ]
}
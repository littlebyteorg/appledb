module.exports = {
  name: "Blackb0x",
  alias: "blackbox",
  priority: 3,
  info: {
    website: {
      name: "github.com/NSSpiral/Blackb0x",
      url: "https://github.com/NSSpiral/Blackb0x",
      external: true
    },
    wiki: {
      name: "theiphonewiki.com/wiki/Blackb0x",
      url: "https://www.theiphonewiki.com/wiki/Blackb0x",
      external: true
    },
    type: "Mixed",
    latestVer: "0.6.2",
    color: "#800080",
    firmwares: ["5.3","7.9"]
  },
  compatibility: [
    {
      firmwares: [
        "11A470e", // 6.0, AppleTV
        "11A502", // 6.0, AppleTV
        "11B511d", // 6.0.1, AppleTV
        "11B554a-TV", // 6.0.2, AppleTV
        "11B651-TV", // 6.0.2, AppleTV
        "11D169b", // 6.1, AppleTV
        "11D201c", // 6.1.1, AppleTV
        "11D257c", // 6.2, AppleTV
        "12H523", // 7.2.1, AppleTV
        "12H606", // 7.2.2, AppleTV
        "12H847", // 7.3, AppleTV
        "12H864", // 7.3.1, AppleTV
        "12H876", // 7.4, AppleTV
        "12H885", // 7.5, AppleTV
        "12H903", // 7.6, AppleTV
        "12H911", // 7.6.1, AppleTV
        "12H914", // 7.6.2, AppleTV
        "12H923", // 7.7, AppleTV
        "12H937", // 7.8, AppleTV
        "12H1006", // 7.9, AppleTV
      ],
      devices: [
        "AppleTV3,1", // Apple TV 3rd Gen (3,1), A5
        "AppleTV3,2", // Apple TV 3rd Gen (3,2), A5
      ]
    },
    {
      firmwares: [
        "10B809", // 5.3, AppleTV
        "11D258", // 6.2.1, AppleTV
      ],
      devices: [
        "AppleTV2,1", // Apple TV 2nd Gen, A4
      ]
    }
  ]
} 

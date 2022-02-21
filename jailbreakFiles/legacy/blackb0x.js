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
    type: "Tethered",
    latestVer: "0.6.2",
    color: "#800080",
    firmwares: ["5.3","7.8"]
  },
  compatibility: [
    {
      firmwares: [
        "10A406e", // 6.0, AppleTV
        "10A831", // 6.0.1, AppleTV
        "11B554A", // 6.0.2, AppleTV
        "10B144b", // 6.1, AppleTV
        "11D201c", // 6.1.1, AppleTV
        "10B329a", // 6.1.3, AppleTV
        "10B809", // 6.1.4, AppleTV
        "11D257c", // 6.2, AppleTV
        "12H523", // 7.2.1, AppleTV
        "12H606", // 7.2.2, AppleTV
        "12H847", // 7.3, AppleTV
        "12H847", // 7.3.1, AppleTV
        "12H876", // 7.4, AppleTV
        "12H885", // 7.5, AppleTV
        "12H903", // 7.6, AppleTV
        "12H911", // 7.6.1, AppleTV
        "12H914", // 7.6.2, AppleTV
        "12H923", // 7.7, AppleTV
        "12H937", // 7.8, AppleTV
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

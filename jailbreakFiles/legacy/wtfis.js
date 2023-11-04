module.exports = {
  name: "wtfis",
  priority: 0,
  info: {
    website: {
      name: "github.com/TheRealClarity/wtfis",
      url: "https://github.com/TheRealClarity/wtfis",
      external: true
    },
    wiki: {
      name: "theapplewiki.com/wiki/wtfis",
      url: "https://www.theapplewiki.com/wiki/wtfis",
      external: true
    },
    guide: [
      {
        name: "Installing wtfis",
        url: "/installing-wtfis/",
        pkgman: "cydia",
      }
    ],
    type: "Untethered",
    latestVer: "1.0b1",
    firmwares: ["8.0","8.4.1"],
  },
  compatibility: [
    {
      firmwares: [
        "12A365", // 8.0
        "12A366", // 8.0, iPhone 6 Plus only
        "12A402", // 8.0.1
        "12A405", // 8.0.2
        "12B410", // 8.1, iPad only
        "12B411", // 8.1, iPhone and iPod only
        "12B435", // 8.1.1
        "12B436", // 8.1.1, iPhone 6, iPad mini 3, and iPad Air 2 only
        "12B440", // 8.1.2
        "12B466", // 8.1.3
        "12D508", // 8.2
        "12F69", // 8.3, iPad and iPod only
        "12F70", // 8.3, iPhone only
        "12H143", // 8.4
        "12H321", // 8.4.1
      ],
      devices: [
        "iPhone6,1", // iPhone 5s (GSM), A7
        "iPhone6,2", // iPhone 5s (CDMA), A7
        "iPhone7,1", // iPhone 6 Plus, A8
        "iPhone7,2", // iPhone 6, A8
        "iPad4,1", // iPad Air Wi-Fi, A7
        "iPad4,2", // iPad Air Wi-Fi + Cellular, A7
        "iPad4,3", // iPad Air Wi-Fi + Cellular (TD-LTE), A7
        "iPad4,4", // iPad mini 2 Wi-Fi, A7
        "iPad4,5", // iPad mini 2 Wi-Fi + Cellular, A7
        "iPad4,6", // iPad mini 2 Wi-Fi + Cellular (TD-LTE), A7
        "iPad4,7", // iPad mini 3 Wi-Fi, A8
        "iPad4,8", // iPad mini 3 Wi-Fi + Cellular, A8
        "iPad4,9", // iPad mini 3 Wi-Fi + Cellular (TD-LTE), A8
        "iPad5,3", // iPad Air 2 Wi-Fi, A8X
        "iPad5,4", // iPad Air 2 Wi-Fi + Cellular, A8X
        "iPod7,1", // iPod touch (6th generation), A8
      ]
    },
  ]
}
module.exports = {
  name: "opensn0w",
  info: {
    wiki: {
      name: "theiphonewiki.com/wiki/Opensn0w",
      url: "https://www.theiphonewiki.com/wiki/Opensn0w",
      external: true
    },
    type: "Tethered",
    firmwares: ["6.0","7.1"],
  },
  compatibility: [
    {
      firmwares: [
        "11A465", // 7.0
        "11A470a", // 7.0.1
        "11A501", // 7.0.2
        "11B511", // 7.0.3
        "11B554a", // 7.0.4
        "11D167", // 7.1
        "11D169", // 7.1, iPhone 4 (GSM) and iPhone 4 (GSM, 2012) only
        "11D201", // 7.1.1
        "11D257", // 7.1.2
        "11A470e", // 6.0, Apple TV 2nd Gen
        "11A502", // 6.0, Apple TV 2nd Gen
        "11B511d", // 6.0.1, Apple TV 2nd Gen
        "11B554a", // 6.0.2, Apple TV 2nd Gen
        "11B651", // 6.0.2, Apple TV 2nd Gen
        "11D169b", // 6.1, Apple TV 2nd Gen
        "11D201c", // 6.1.1, Apple TV 2nd Gen
        "11D257c", // 6.2, Apple TV 2nd Gen
        "11D258" // 6.2.1, Apple TV 2nd Gen
        
      ],
      devices: [
        "iPhone3,1", // iPhone 4 (GSM), A4
        "iPhone3,2", // iPhone 4 (GSM, 2012), A4
        "iPhone3,3", // iPhone 4 (CDMA), A4
        "AppleTV2,1" // Apple TV 2nd Gen, A4
        
      ]
    },
  ]
}
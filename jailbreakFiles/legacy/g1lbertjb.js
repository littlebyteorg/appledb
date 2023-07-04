module.exports = {
  name: "g1lbertJB",
  info: {
    website: {
      name: "github.com/eatingurtoes/g1lbertCFW",
      url: "https://github.com/eatingurtoes/g1lbertCFW",
      external: true
    },
    type: "Untethered",
    firmwares: ["5.0", "5.1.1"],
  },
  compatibility: [
    {
      firmwares: [
        "9A334", // 5.0
        "9A405", // 5.0.1
        "9A406", // 5.0.1 (4s only)
        "9B176", // 5.1 (everything but 4s)
        "9B179", // 5.1 (4s only)
        "9B206", // 5.1.1
      ],
      devices: [
        "iPhone4,1", // iPhone 4s
        "iPad2,1", // iPad 2 WiFi
        "iPad2,2", // iPad 2 GSM
        "iPad2,3", // iPad 2 CDMA
        "iPad2,4", // iPad 2 Mid 2012
        "iPad3,1", // iPad 3 WiFi
        "iPad3,2", // iPad 3 GSM
        "iPad3,3", // iPad 3 CDMA
      ]
    },
  ]
}

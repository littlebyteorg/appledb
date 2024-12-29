module.exports = {
  name: "EverPwnage",
  priority: 0,
  info: {
    website: {
      name: "github.com/LukeZGD/EverPwnage",
      url: "https://github.com/LukeZGD/EverPwnage",
      external: true
    },
    guide: [
      {
        name: "Installing EverPwnage",
        url: "/installing-everpwnage/",
        pkgman: "cydia",
      }
    ],
    type: "Untethered",
    firmwares: ["8.0", "9.0.2"],
    notes: "Only supports 32-bit devices.",
    latestVer: "1.1",
    color: "#ba8eb6",
  },
  compatibility: [
    {
      firmwares: [
        "12A365", // 8.0
        "12A402", // 8.0.1
        "12A405", // 8.0.2
        "12B410", // 8.1, iPad only
        "12B411", // 8.1, iPhone and iPod only
        "12B435", // 8.1.1
        "12B440", // 8.1.2
        "12B466", // 8.1.3
        "12D508", // 8.2
        "12F69", // 8.3, iPad and iPod only
        "12F70", // 8.3, iPhone only
        "12H143", // 8.4
        "12H321", // 8.4.1
        "13A344", // 9.0
        "13A404", // 9.0.1
        "13A452", // 9.0.2
      ],
      devices: [
        "iPhone4,1", // iPhone 4S, A5
        "iPad2,1", // iPad 2 Wi-Fi, A5
        "iPad2,2", // iPad 2 Wi-Fi + 3G (GSM), A5
        "iPad2,3", // iPad 2 Wi-Fi + 3G (CDMA), A5
        "iPad2,4", // iPad 2 Wi-Fi (Mid 2012), A5
        "iPad2,5", // iPad mini Wi-Fi, A5
        "iPad2,6", // iPad mini Wi-Fi + Cellular, A5
        "iPad2,7", // iPad mini Wi-Fi + Cellular (MM), A5
        "iPad3,1", // iPad (3rd generation) Wi-Fi, A5X
        "iPad3,2", // iPad (3rd generation) Wi-Fi + Cellular (VZ), A5X
        "iPad3,3", // iPad (3rd generation) Wi-Fi + Cellular, A5X
        "iPod5,1", // iPod touch (5th generation), A5
        "iPhone5,1", // iPhone 5 (GSM), A6
        "iPhone5,2", // iPhone 5 (CDMA), A6
        "iPhone5,3", // iPhone 5c (GSM), A6
        "iPhone5,4", // iPhone 5c (CDMA), A6
        "iPad3,4", // iPad (4th generation) Wi-Fi, A6X
        "iPad3,5", // iPad (4th generation) Wi-Fi + Cellular, A6X
        "iPad3,6", // iPad (4th generation) Wi-Fi + Cellular (MM), A6X
      ]
    }
  ]
}

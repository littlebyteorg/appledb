module.exports = {
  name: "Home Depot",
  alias: ["HomeDepot", "Home-Depot", "Home_Depot"],
  priority: 2,
  info: {
    website: {
      name: "wall.supplies",
      url: "http://wall.supplies/",
      external: true
    },
    wiki: {
      name: "theapplewiki.com/wiki/Home_Depot",
      url: "https://www.theapplewiki.com/wiki/Home_Depot",
      external: true
    },
    guide: [
      {
        name: "Installing HomeDepot",
        url: "/installing-homedepot/",
        pkgman: "cydia",
      }
    ],
    type: "Semi-untethered",
    firmwares: ["8.0", "9.3.4"],
    notes: "Untethered through add-on package, also compatible with A5(X) devices on iOS 8.4.1, also compatible with A5(X) devices on iOS 8.0 to 8.4 with the use of a patching script",
    latestVer: "1.1 beta 1",
    color: "#ba8eb6",
    icon: "/assets/images/jb-icons/homedepot.png",
  },
  compatibility: [
    {
      firmwares: [
        "13B143", // 9.1
        "13C75", // 9.2
        "13D15", // 9.2.1
        "13E233", // 9.3
        "13E236", // 9.3, iPad 2 (Cellular) only
        "13E237", // 9.3
        "13E238", // 9.3.1
        "13F69", // 9.3.2
        "13G34", // 9.3.3
        "13G35", // 9.3.4
      ],
      devices: [
        "iPhone4,1", // iPhone 4S, A5
        "iPhone5,1", // iPhone 5 (GSM), A6
        "iPhone5,2", // iPhone 5 (CDMA), A6
        "iPhone5,3", // iPhone 5c (GSM), A6
        "iPhone5,4", // iPhone 5c (CDMA), A6
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
        "iPad3,4", // iPad (4th generation) Wi-Fi, A6X
        "iPad3,5", // iPad (4th generation) Wi-Fi + Cellular, A6X
        "iPad3,6", // iPad (4th generation) Wi-Fi + Cellular (MM), A6X
        "iPod5,1", // iPod touch (5th generation), A5
      ]
    },
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
      ]
    },
  ]
}

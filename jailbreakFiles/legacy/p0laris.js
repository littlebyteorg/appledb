module.exports = {
  name: "p0laris",
  alias: "polaris",
  priority: 3,
  info: {
    website: {
      name: "p0laris.dev",
      url: "https://p0laris.dev/",
      external: true
    },
    wiki: {
      name: "theiphonewiki.com/wiki/p0laris",
      url: "https://www.theiphonewiki.com/wiki/p0laris",
      external: true
    },
    guide: [
      {
        name: "Installing p0laris",
        url: "/installing-p0laris/",
        pkgman: "cydia",
      }
    ],
    latestVer: "1.0",
    color: "#202020",
    icon: "/assets/images/jb-icons/p0laris.png",
    type: "Semi-untethered",
    firmwares: ["9.3","9.3.6"]
  },
  compatibility: [
    {
      firmwares: [
        "13E236", // 9.3 (iPad 2 Wi-Fi + 3G)
        "13E237", // 9.3 (other)
        "13E238", // 9.3.1
        "13F69", // 9.3.2
        "13G34", // 9.3.3
        "13G35", // 9.3.4
        "13G36", // 9.3.5
        "13G37", // 9.3.6
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

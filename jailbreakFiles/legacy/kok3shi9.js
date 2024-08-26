module.exports = {
  name: "kok3shi9",
  alias: ["kok3shi", "kokeshi", "kok3shiJB", "kokeshiJB"],
  priority: 1,
  info: {
    website: {
      name: "kok3shidoll.web.app/kok3shi9.html",
      url: "https://kok3shidoll.web.app/kok3shi9.html",
      external: true
    },
    wiki: {
      name: "theapplewiki.com/wiki/kok3shi",
      url: "https://www.theapplewiki.com/wiki/kok3shi",
      external: true
    },
    guide: [
      {
        name: "Installing kok3shi9",
        url: "/installing-kok3shi9/",
        pkgman: "cydia",
        updateLink: [
          {
            text: 'Updating to 9.3.5',
            link: '/updating-to-9-3-5/'
          },
          {
            text: 'Updating to 9.3.5 (IPSW)',
            link: '/updating-to-9-3-5-ipsw/'
          },
          {
            text: 'Updating to 9.3.6',
            link: '/updating-to-9-3-6/'
          },
          {
            text: 'Updating to 9.3.6 (IPSW)',
            link: '/updating-to-9-3-6-ipsw/'
          },
        ],
      }
    ],
    type: "Semi-untethered",
    firmwares: ["9.3","9.3.6"],
    notes: "32-bit support only for 9.3.2 to 9.3.6",
    latestVer: "5.0.1",
    color: "#c279a0",
    icon: "/assets/images/jb-icons/kok3shi.png",
  },
  compatibility: [
    {
      firmwares: [
        "13C75", // 9.2
        "13D15", // 9.2.1
        "13D20", // 9.2.1
        "13E233", // 9.3
        "13E237", // 9.3
        "13E238", // 9.3.1
        "13F69", // 9.3.2
        "13G34", // 9.3.3
        "13G35", // 9.3.4
        "13G36", // 9.3.5
      ],
      devices: [
        "iPhone6,1", // iPhone 5s (GSM), A7
        "iPhone6,2", // iPhone 5s (CDMA), A7
        "iPhone7,1", // iPhone 6 Plus, A8
        "iPhone7,2", // iPhone 6, A8
        "iPhone8,1", // iPhone 6s, A9
        "iPhone8,2", // iPhone 6s Plus, A9
        "iPhone8,4", // iPhone SE, A9
        "iPad4,1", // iPad Air Wi-Fi, A7
        "iPad4,2", // iPad Air Wi-Fi + Cellular, A7
        "iPad4,3", // iPad Air Wi-Fi + Cellular (TD-LTE), A7
        "iPad4,4", // iPad mini 2 Wi-Fi, A7
        "iPad4,5", // iPad mini 2 Wi-Fi + Cellular, A7
        "iPad4,6", // iPad mini 2 Wi-Fi + Cellular (TD-LTE), A7
        "iPad4,7", // iPad mini 3 Wi-Fi, A8
        "iPad4,8", // iPad mini 3 Wi-Fi + Cellular, A8
        "iPad4,9", // iPad mini 3 Wi-Fi + Cellular (TD-LTE), A8
        "iPad5,1", // iPad mini 4 Wi-Fi, A8
        "iPad5,2", // iPad mini 4 Wi-Fi + Cellular, A8
        "iPad5,3", // iPad Air 2 Wi-Fi, A8X
        "iPad5,4", // iPad Air 2 Wi-Fi + Cellular, A8X
        "iPod7,1", // iPod touch (6th generation), A8
        "iPad6,3", // iPad Pro (9.7-inch) Wi-Fi, A9X
        "iPad6,4", // iPad Pro (9.7-inch) Wi-Fi + Cellular, A9X
        "iPad6,7", // iPad Pro (12.9-inch) Wi-Fi, A9X
        "iPad6,8", // iPad Pro (12.9-inch) Wi-Fi + Cellular, A9X
      ]
    },
    {
      firmwares: [
        "13F69", // 9.3.2
        "13G34", // 9.3.3
        "13G35", // 9.3.4
        "13G36", // 9.3.5
        "13G37", // 9.3.6
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
  ]
}
module.exports = {
  name: "Lyncis",
  priority: 0,
  info: {
    guide: [
      {
        name: "Using Lyncis",
        url: "/using-lyncis/",
        pkgman: "cydia",
        updateLink: [
          {
            text: 'Updating to 7.1.2 (IPSW)',
            link: '/updating-to-7-1-2-ipsw/'
          },
        ],
      }
    ],
    type: "Untethered",
    firmwares: ["7.1","7.1.2"],
    notes: "Only supports 32-bit devices.",
    latestVer: "1.0",
    color: "#ffffff",
  },
  compatibility: [
    {
      firmwares: [
        "11D167", // 7.1
        "11D169", // 7.1, iPhone 4 (GSM) and iPhone 4 (GSM, 2012) only
        "11D201", // 7.1.1
        "11D257", // 7.1.2
      ],
      devices: [
        "iPhone3,1", // iPhone 4 (GSM), A4
        "iPhone3,2", // iPhone 4 (GSM, 2012), A4
        "iPhone3,3", // iPhone 4 (CDMA), A4
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
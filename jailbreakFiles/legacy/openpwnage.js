module.exports = {
  name: "openpwnage",
  priority: 6,
  info: {
    website: {
      name: "github.com/zachary7829/openpwnage/",
      url: "https://github.com/zachary7829/openpwnage/",
      external: true
    },
    wiki: {
      name: "theiphonewiki.com/wiki/openpwnage",
      url: "https://www.theiphonewiki.com/wiki/openpwnage",
      external: true
    },
    guide: [
      {
        name: "Installing openpwnage",
        url: "/installing-openpwnage/",
        pkgman: "cydia",
      }
    ],
    latestVer: "Beta Build 9",
    color: "#faf4f7",
    icon: "/assets/images/jb-icons/openpwnage.png",
    notes: "iOS 8.4.1 can be optionally untethered via etason untether package",
    jailbreaksmeapp: true,
    type: "Semi-untethered",
    firmwares: ["8.4b4","9.3.6"]
  },
  compatibility: [
    {
      firmwares: [
        "12H4125a", // 8.4 Beta 4
        "12H143", // 8.4
        "12H304", // 8.4.1 Beta
        "12H318", // 8.4.1 Beta 2
        "12H321", // 8.4.1
        "13A4254v", // 9.0 Beta
        "13A4280e", // 9.0 Beta 2
        "13A4293g", // 9.0 Beta 3
        "13A4305g", // 9.0 Beta 4
        "13A4325c", // 9.0 Beta 5
        "13A340", // 9.0 GM
        "13A344", // 9.0
        "13A404", // 9.0.1
        "13A452", // 9.0.2
        "13B5110e", // 9.1 Beta
        "13B5119e", // 9.1 Beta 2
        "13B5130b", // 9.1 Beta 3
        "13B136", // 9.1 Beta 4
        "13B137", // 9.1 Beta 5
        "13B143", // 9.1
        "13C5055d", // 9.2 Beta
        "13C5060d", // 9.2 Beta 2
        "13C71", // 9.2 Beta 3
        "13C75", // 9.2 / 9.2 Beta 4
        "13D11", // 9.2.1 Beta
        "13D14", // 9.2.1 Beta 2
        "13D15", // 9.2.1
        "13E5181d", // 9.3 Beta 1
        "13E5181f", // 9.3 Beta 1.1
        "13E5191d", // 9.3 Beta 2
        "13E5200d", // 9.3 Beta 3
        "13E5214d", // 9.3 Beta 4
        "13E5225a", // 9.3 Beta 5
        "13E5231a", // 9.3 Beta 6
        "13E5233a", // 9.3 Beta 7
        "13E233", // 9.3
        "13E236", // 9.3 (iPad 2 Wi-Fi + 3G)
        "13E237", // 9.3 (other)
        "13E238", // 9.3.1
        "13F51a", // 9.3.2 Beta 1
        "13F61", // 9.3.2 Beta 2
        "13F65", // 9.3.2 Beta 3
        "13F68", // 9.3.2 Beta 4
        "13F69", // 9.3.2
        "13G12", // 9.3.3 Beta 1
        "13G21", // 9.3.3 Beta 2
        "13G29", // 9.3.3 Beta 3
        "13G33", // 9.3.3 Beta 4
        "13G34", // 9.3.3 / 9.3.3 Beta 5
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
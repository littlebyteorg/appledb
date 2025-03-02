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
    latestVer: "1.1.1",
    color: "#ba8eb6",
  },
  compatibility: [
    {
      firmwares: [
        "12A4265u", // 8.0 beta
        "12A4297e", // 8.0 beta 2
        "12A4318c", // 8.0 beta 3
        "12A4331d", // 8.0 beta 4
        "12A4345d", // 8.0 beta 5
        "12A365", // 8.0
        "12A402", // 8.0.1
        "12A405", // 8.0.2
        "12B401", // 8.1 beta
        "12B407", // 8.1 beta 2
        "12B410", // 8.1, iPad only
        "12B411", // 8.1, iPhone and iPod only
        "12B432", // 8.1.1 beta
        "12B435", // 8.1.1
        "12B440", // 8.1.2
        "12B466", // 8.1.3
        "12D436", // 8.2 beta
        "12D445d", // 8.2 beta 2
        "12D5452a", // 8.2 beta 3
        "12D5461b", // 8.2 beta 4
        "12D5480a", // 8.2 beta 5
        "12D508", // 8.2
        "12F5027d", // 8.3 beta
        "12F5037c", // 8.3 beta 2
        "12F5047f", // 8.3 beta 3
        "12F61", // 8.3 beta 4
        "12F69", // 8.3, iPad and iPod only
        "12F70", // 8.3, iPhone only
        "12H4074d", // 8.4 beta
        "12H4086d", // 8.4 beta 2
        "12H4098c", // 8.4 beta 3
        "12H4125a", // 8.4 beta 4
        "12H143", // 8.4
        "12H304", // 8.4.1 beta
        "12H318", // 8.4.1 beta 2
        "12H321", // 8.4.1
        "13A4254v", // 9.0 beta
        "13A4280e", // 9.0 beta 2
        "13A4293f", // 9.0 beta 3
        "13A4293g", // 9.0 beta 3
        "13A4305g", // 9.0 beta 4
        "13A4325c", // 9.0 beta 5
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

module.exports = {
  name: "daibutsu",
  priority: 0,
  info: {
    website: {
      name: "dora2ios.web.app/daibutsu.html",
      url: "https://dora2ios.web.app/daibutsu.html",
      external: true
    },
    guide: [
      {
        name: "Installing daibutsu",
        url: "/installing-daibutsu/",
        pkgman: "cydia",
      }
    ],
    type: "Untethered",
    firmwares: ["8.4.1","8.4.1"],
    notes: "iPad 2 support limited to the 2012 WiFi-Only 16GB revision",
    latestVer: "1.2.1",
    color: "#f6b0f6",
    icon: "/assets/images/jb-icons/daibutsu.png",
  },
  compatibility: [
    {
      firmwares: [
        "12H321", // 8.4.1
      ],
      devices: [
        "iPhone4,1", // iPhone 4S, A5
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
};

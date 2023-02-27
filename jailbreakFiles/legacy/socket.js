module.exports = {
  name: "Socket",
  alias: "Socket",
  priority: 0,
  info: {
    website: {
      name: "socket-jb.app",
      url: "https://socket-jb.app/",
      external: true
    },
    guide: [
      {
        name: "Installing Socket",
        url: "/installing-socket/",
        pkgman: "zebra",
      }
    ],
    latestVer: "1.0 beta 2",
    color: "#ffffff",
    type: "Semi-untethered",
    firmwares: ["10.3","10.3.4"]
  },
  compatibility: [
    {
      firmwares: [
        "14E277", // 10.3
        "14E304", // 10.3.1
        "14F89", // 10.3.2
        "14G60", // 10.3.3
        "14G61", // 10.3.4
      ],
      devices: [
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

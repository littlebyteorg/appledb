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
    latestVer: "1.1",
    color: "#ffffff",
    type: "Semi-untethered",
    firmwares: ["10.0.1","10.3.4"]
  },
  compatibility: [
    {
      firmwares: [
       // Disabled 10.0 until testing is done
       // "14A5261v", // 10.0 beta
       // "14A5297c", // 10.0 beta 2
       // "14A5309d", // 10.0 beta 3
       // "14A5322e", // 10.0 beta 4
       // "14A5335b", // 10.0 beta 5
       // "14A5341a", // 10.0 beta 6
       // "14A5345a", // 10.0 beta 7
       // "14A5346a", // 10.0 beta 8
       // "14A346", // 10.0
        "14A403-GM", // iOS 10.0.1 GM
        "14A403", // 10.0.1
        "14A456", // 10.0.2
        "14B67", // 10.1 beta 2
        "14B71", // 10.1 beta 3
        "14B72b", // 10.1 beta 4
        "14B72", // 10.1 beta 4
        "14B72c", // 10.1 beta 5
        "14B72",  // 10.1
        "14B100", // 10.1.1
        "14B150", // 10.1.1
        "14C5062e", // 10.2 beta
        "14C5069c", // 10.2 beta 2
        "14C5077b", // 10.2 beta 3
        "14C82", // 10.2 beta 4
        "14C89", // 10.2 beta 5
        "14C91", // 10.2 beta 6
        "14C90", // 10.2 beta 6
        "14C92", // 10.2 beta 7
        "14C92",  // 10.2
        "14D10", // 10.2.1 beta
        "14D15", // 10.2.1 beta 2
        "14D23", // 10.2.1 beta 3
        "14D27", // 10.2.1 beta 4
        "14D27",  // 10.2.1
        "14E5230e", // 10.3 beta
        "14E5239e", // 10.3 beta 2
        "14E5249d", // 10.3 beta 3
        "14E5260b", // 10.3 beta 4
        "14E5269a", // 10.3 beta 5
        "14E5273a", // 10.3 beta 6
        "14E5277a", // 10.3 beta 7
        "14E277", // 10.3
        "14E304", // 10.3.1
        "14F5065b", // 10.3.2 beta
        "14F5075a", // 10.3.2 beta 2
        "14F5080a", // 10.3.2 beta 3
        "14F5086a", // 10.3.2 beta 4
        "14F5089a", // 10.3.2 beta 5
        "14F89",  // 10.3.2
        "14G5028a", // 10.3.3 beta
        "14G5037b", // 10.3.3 beta 2
        "14G5047a", // 10.3.3 beta 3
        "14G5053a", // 10.3.3 beta 4
        "14G5057a", // 10.3.3 beta 5
        "14G58", // 10.3.3 beta 6
        "14G57", // 10.3.3 beta 6
        "14G60",  // 10.3.3
        "14G61",  // 10.3.4
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

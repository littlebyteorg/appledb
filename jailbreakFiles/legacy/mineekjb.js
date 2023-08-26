module.exports = {
  name: "mineekJB",
  priority: 9,
  info: {
    website: {
      name: "mineek.github.io/mineekJB/",
      url: "https://mineek.github.io/mineekJB/",
      external: true
    },
    latestVer: "1.0",
    color: "#faf4f7",
    icon: "/assets/images/jb-icons/mineekjb.png",
    jailbreaksmeapp: false,
    type: "Semi-untethered",
    firmwares: ["10.3.3","10.3.3"]
  },
  compatibility: [
    {
      firmwares: [
        "14G60" // 10.3.3
      ],
      devices: [
        "iPhone6,1", // iPhone 5s (GSM), A7
        "iPhone6,2", // iPhone 5s (CDMA), A7
        "iPad4,1", // iPad Air Wi-Fi, A7
        "iPad4,2", // iPad Air Cellular, A7
        "iPad4,3", // iPad Air Wi-Fi + Cellular (TD-LTE), A7
        "iPad4,4", // iPad mini 2 Wi-Fi, A7
        "iPad4,5", // iPad mini 2 Wi-Fi + Cellular, A7
        "iPad4,6", // iPad mini 2 Wi-Fi + Cellular (TD-LTE), A7
      ]
    },
  ]
}

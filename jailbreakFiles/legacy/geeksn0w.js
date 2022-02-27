module.exports = {
  name: "Geeksn0w",
  alias: "Geeksnow",
  info: {
    wiki: {
      name: "theiphonewiki.com/wiki/Geeksn0w",
      url: "https://www.theiphonewiki.com/wiki/Geeksn0w",
      external: true
    },
    type: "Semi-Tethered",
    firmwares: ["7.1","7.1.2"],
    latestVer: "2.9.1",
    color: "#ffffff",
    icon: "/assets/images/jb-icons/geeksn0w.png",
  },
  compatibility: [
    {
      firmwares: [
        "11D167", // 7.1
        "11D169", // 7.1, iPhone 4 (GSM) and iPhone 4 (GSM, 2012) only
        "11D201", // 7.1.1
        "11D257" // 7.1.2
      ],
      devices: [
        "iPhone3,1", // iPhone 4 (GSM), A4
        "iPhone3,2", // iPhone 4 (GSM, 2012), A4
        "iPhone3,3" // iPhone 4 (CDMA), A4
      ]
    }
  ]
}
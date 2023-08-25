module.exports = {
  name: "backr00m",
  alias: ["backroom", "backr0om", "backro0m"],
  info: {
    website: {
      name: "nito.tv/downloads",
      url: "https://nito.tv/downloads",
      external: true
    },
    wiki: {
      name: "theapplewiki.com/wiki/Backr00m",
      url: "https://www.theapplewiki.com/wiki/Backr00m",
      external: true
    },
    guide: [
      {
        name: "Installing backr00m",
        url: "/installing-backr00m/",
        pkgman: "nito.tv",
      }
    ],
    type: "Semi-untethered",
    latestVer: "1.1",
    firmwares: ["10.2.2","11.1"]
  },
  compatibility: [
    {
      firmwares: [
        "14W756", // 10.2.2, AppleTV
        "15J381", // 11.0, AppleTV
        "15J582", // 11.1, AppleTV
      ],
      devices: [
        "AppleTV5,3", // Apple TV HD (4th generation), A8
        "AppleTV6,2", // Apple TV 4K (1st generation), A10X
      ]
    }
  ]
}
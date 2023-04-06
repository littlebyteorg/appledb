module.exports = {
  name: "ChimeraTV",
  priority: 0,
  info: {
    website: {
      name: "chimera.coolstar.org",
      url: "https://chimera.coolstar.org/",
      external: true
    },
    wiki: {
      name: "theapplewiki.com/wiki/Chimera",
      url: "https://www.theapplewiki.com/wiki/Chimera#tvOS",
      external: true
    },
    guide: [
      {
        name: "Installing ChimeraTV",
        url: "/installing-chimeratv/",
        pkgman: "nito.tv",
      }
    ],
    latestVer: "1.3.9",
    color: "#deeded",
    icon: "/assets/images/jb-icons/chimera.png",
    firmwares: ["12.0","12.2 and 12.4"]
  },
  compatibility: [
    {
      firmwares: [
        "16J364", // 12.0, AppleTV
        "16J380", // 12.0.1, AppleTV
        "16J602", // 12.1, AppleTV
        "16K45", // 12.1.1, AppleTV
        "16K534", // 12.1.2, AppleTV
        "16L226", // 12.2, AppleTV
        "16M568", // 12.4, AppleTV
      ],
      devices: [
        "AppleTV5,3", // Apple TV HD (4th generation), A8
        "AppleTV6,2", // Apple TV 4K (1st generation), A10X
      ]
    }
  ]
}
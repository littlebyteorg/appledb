module.exports = {
  name: "Seas0nPass",
  alias: "SeasonPass",
  priority: 3,
  info: {
    website: {
      name: "support.firecore.com/hc/en-us/articles/215090347-Jailbreaking-101-Seas0nPass",
      url: "https://support.firecore.com/hc/en-us/articles/215090347-Jailbreaking-101-Seas0nPass",
      external: true
    },
    wiki: {
      name: "theiphonewiki.com/wiki/Seas0nPass",
      url: "https://www.theiphonewiki.com/wiki/Seas0nPass",
      external: true
    },
    type: "Tethered",
    latestVer: "0.9.8",
    color: "#32CD32",
    firmwares: ["4.0","6.2.1"]
  },
  compatibility: [
    {
      firmwares: [
        "8M89", // 4.0, AppleTV
        "8C150", // 4.1, AppleTV
        "8C154", // 4.1.1, AppleTV
        "8C152", // 4.1.1, AppleTV
        "8F191m", // 4.2, AppleTV
        "8F202", // 4.2.1, AppleTV
        "8F305", // 4.2.2, AppleTV
        "8F455", // 4.3, AppleTV
        "9A334v", // 4.4, AppleTV
        "9A335a", // 4.4.1, AppleTV
        "9A336a", // 4.4.2, AppleTV
        "9A405l", // 4.4.3, AppleTV
        "9A406a", // 4.4.4, AppleTV
        "9B179b", // 5.0, AppleTV
        "9B206f", // 5.0.1, AppleTV
        "9B830", // 5.0.2, AppleTV
        "10A406e", // 5.1, AppleTV
        "10A831", // 5.1.1, AppleTV
        "10B144b", // 5.2, AppleTV
        "10B329a", // 5.2.1, AppleTV
        "10B809", // 5.3, AppleTV
        "11D258" // 6.2.1, AppleTV
      ],
      devices: [
        "AppleTV2,1" // Apple TV 2nd Gen, A4
      ]
    }
  ]
}
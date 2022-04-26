module.exports = {
  name: "ZiPhone",
  info: {
    website: {
      name: "The Legacy Archives",
      url: "https://mega.nz/folder/k4FAXCIB#Fk7pxs6ikYzL3YBvAGX5ig/folder/I8lRwKAS",
      external: true
    },
    wiki: {
      name: "theiphonewiki.com/wiki/ZiPhone",
      url: "https://www.theiphonewiki.com/wiki/ZiPhone",
      external: true
    },
    type: "Untethered",
    firmwares: ["1.0","1.1.5"],
    latestVer: "3.6",
    color: "#ed9121",
    icon: "/assets/images/jb-icons/ziphone.png",
  },
  compatibility: [
    {
      firmwares: [
        "1A543a", // 1.0
        "1C25", // 1.0.1
        "1C28", // 1.0.2
        "3A101a", // 1.1, iPod touch only
        "3A109a", // 1.1.1, iPhone 2G only
        "3A110a", // 1.1.1, iPod touch only
        "3B48b", // 1.1.2
        "4A93", // 1.1.3
        "4A102", // 1.1.4
        "4B1", // 1.1.5, iPod touch only
      ],
      devices: [
        "iPhone1,1", // iPhone
        "iPod1,1", // iPod touch
      ]
    },
  ]
}
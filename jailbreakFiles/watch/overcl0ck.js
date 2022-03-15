module.exports = {
  name: "OverCl0ck",
  info: {
    website: {
      name: "github.com/PsychoTea/OverCl0ck",
      url: "https://github.com/PsychoTea/OverCl0ck",
      external: true
    },
    wiki: {
      name: "theiphonewiki.com/wiki/Overcl0ck",
      url: "https://www.theiphonewiki.com/wiki/Overcl0ck",
      external: true
    },
    firmwares: ["3.0","3.2.3"]
  },
  compatibility: [
    {
      firmwares: [
        "14S326", // 3.0, Watch
        "14S471", // 3.1, Watch
        "14S883", // 3.1.1, Watch
        "14S960", // 3.1.3, Watch
        "14V249", // 3.2, Watch
        "14V485", // 3.2.2, Watch
        "14V753", // 3.2.3, Watch
      ],
      devices: [
        "Watch1,1", // Apple Watch (1st generation) (38mm), S1
        "Watch1,2", // Apple Watch (1st generation) (38mm), S1
        "Watch2,6", // Apple Watch Series 1 (38mm), S1P
        "Watch2,7", // Apple Watch Series 1 (38mm), S1P
        "Watch2,3", // Apple Watch Series 2 (38mm), S2
        "Watch2,4", // Apple Watch Series 2 (42mm), S2
      ]
    }
  ]
}

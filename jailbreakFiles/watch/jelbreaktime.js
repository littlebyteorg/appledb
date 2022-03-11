module.exports = {
  name: "jelbrekTime",
  info: {
    website: {
      name: "github.com/tihmstar/jelbrekTime",
      url: "https://github.com/tihmstar/jelbrekTime",
      external: true
    },
    firmwares: ["4.1","4.1"]
  },
  compatibility: [
    {
      firmwares: [
        "15R846", // 4.1, Watch
      ],
      devices: [
        "Watch3,1", // Apple Watch Series 3 (GPS + Cellular, 38mm), S3
        "Watch3,2", // Apple Watch Series 3 (GPS + Cellular, 42mm), 
        "Watch3,3", // Apple Watch Series 3 (GPS, 38mm), S3
        "Watch3,4", // Apple Watch Series 3 (GPS, 42mm), S3
      ]
    }
  ]
}
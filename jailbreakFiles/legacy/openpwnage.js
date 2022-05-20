module.exports = {
  name: "openpwnage",
  priority: 3,
  info: {
    website: {
      name: "github.com/zachary7829/openpwnage/",
      url: "https://github.com/zachary7829/openpwnage/",
      external: true
    },
    latestVer: "Pre-Alpha Build 2",
    color: "#faf4f7",
    notes: "Currently only intended for developers/testers. Does not install bootstrap and Substrate currently doesn't work.",
    type: "Semi-untethered",
    firmwares: ["9.0","9.3.6"]
  },
  compatibility: [
    {
      firmwares: [
        "13A344", // 9.0
        "13A404", // 9.0.1
        "13A452", // 9.0.2
        "13B136", // 9.1 Beta 4
        "13B137", // 9.1 Beta 5
        "13B143", // 9.1
        "13C75", // 9.2 / 9.2 Beta 4
        "13D11", // 9.2.1 Beta
        "13D14", // 9.2.1 Beta 2
        "13D15", // 9.2.1
        "13E5233a", // 9.3 Beta 7
        "13E233", // 9.3
        "13E236", // 9.3 (iPad 2 Wi-Fi + 3G)
        "13E237", // 9.3 (other)
        "13E238", // 9.3.1
        "13F65", // 9.3.2 Beta 3
        "13F68", // 9.3.2 Beta 4
        "13F69", // 9.3.2
        "13G33", // 9.3.3 Beta 4
        "13G34", // 9.3.3 / 9.3.3 Beta 5
        "13G35", // 9.3.4
        "13G36", // 9.3.5
        "13G37", // 9.3.6
      ],
      devices: [
        "iPhone4,1", // iPhone 4S, A5
        "iPhone5,1", // iPhone 5 (GSM), A6
        "iPhone5,2", // iPhone 5 (CDMA), A6
        "iPhone5,3", // iPhone 5c (GSM), A6
        "iPhone5,4", // iPhone 5c (CDMA), A6
        "iPad2,1", // iPad 2 Wi-Fi, A5
        "iPad2,2", // iPad 2 Wi-Fi + 3G (GSM), A5
        "iPad2,3", // iPad 2 Wi-Fi + 3G (CDMA), A5
        "iPad2,4", // iPad 2 Wi-Fi (Mid 2012), A5
        "iPad2,5", // iPad mini Wi-Fi, A5
        "iPad2,6", // iPad mini Wi-Fi + Cellular, A5
        "iPad2,7", // iPad mini Wi-Fi + Cellular (MM), A5
        "iPad3,1", // iPad (3rd generation) Wi-Fi, A5X
        "iPad3,2", // iPad (3rd generation) Wi-Fi + Cellular (VZ), A5X
        "iPad3,3", // iPad (3rd generation) Wi-Fi + Cellular, A5X
        "iPad3,4", // iPad (4th generation) Wi-Fi, A6X
        "iPad3,5", // iPad (4th generation) Wi-Fi + Cellular, A6X
        "iPad3,6", // iPad (4th generation) Wi-Fi + Cellular (MM), A6X
        "iPod5,1", // iPod touch (5th generation), A5
      ]
    },
  ]
}
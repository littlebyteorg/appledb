const substitutes = require('./deviceNameSubstitutes.json')

module.exports = function formatDeviceName(n) {
    let arr = n.split('')
    for (let c in arr) for (var i = 0; i < substitutes.length / 2; i++)
        if (arr[c] == substitutes[i*2]) arr[c] = substitutes[i*2+1]
    return arr.join('')
}
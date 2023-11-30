const fs = require('fs')
const devArr = require('../grabData/device')

function getInfoObj(devKeyArr) {
    const devices = devArr.filter(x => devKeyArr.includes(x.key))

    let retArr = []

    function grabInfo(property) { return Array.from(new Set(devices.filter(x => x[property]).map(x => x[property]).flat())) }
    function addInfo(name, property, pluralise = true) {
        const infoArr = grabInfo(property)
        if (infoArr.length) {
            let str = `${name}${pluralise && infoArr.length > 1 ? 's' : ''}: `
            retArr.push({
                text: str,
                data: infoArr.sort(),
                link: null
            })
        }
    }

    addInfo('Identifier', 'identifier')

    const releasedArr = grabInfo('released')
    if (releasedArr.length) {
        const sortedDates = releasedArr.sort((a,b) => {
            const date = [a,b].map(x => new Date(x).valueOf())
            if (date[0] > date[1]) return 1
            if (date[0] < date[1]) return -1
            return 0
        })
        
		function adjustDate(date) {
			const dateOffset = new Date().getTimezoneOffset() * 60 * 1000
			const currentDate = new Date(date).valueOf()
			return new Date(currentDate + dateOffset)
		}

		function formatDate(date) {
			const releasedArr = date.split('-')
			const dateStyleArr = [{ year: 'numeric' }, { year: 'numeric', month: 'short' }, { dateStyle: 'medium' }]
			return new Intl.DateTimeFormat('en-US', dateStyleArr[releasedArr.length-1]).format(adjustDate(date))
		}

        const formattedDates = sortedDates.map(x => formatDate(x))
        if (formattedDates.length > 1) formattedDates.map(x => x.replace(',',''))
        retArr.push({
            text: 'Released: ',
            data: formattedDates,
            link: null
        })
    }
    
    [
        {
            name: 'SoC',
            property: 'soc'
        },
        {
            name: 'Arch',
            property: 'arch',
            pluralise: false
        },
        {
            name: 'Model',
            property: 'model'
        },
        {
            name: 'Board',
            property: 'board'
        }
    ].map(x => addInfo(x.name, x.property, x.pluralise || true))

    return retArr
}

module.exports = function(pageKey) {
    const obj = {
        title: pageKey.name,
        sections: [
            {
                type: 'list',
                class: 'noPadding noListDisc',
                content: getInfoObj(pageKey.devices)
            },
            {
                title: 'Grouped Devices',
                type: 'list',
                content: pageKey.devices.length > 1 ? pageKey.devices.map(x => { return {
                    text: devArr.find(y => y.key === x).name,
                    link: `/device/identifier/${x}`
                }}) : []
            }
        ].filter(x => x.content.length)
    }

    fs.writeFile(
        `./out/appledb-web/pageData${pageKey.url}.json`,
        JSON.stringify(obj),
        function (err) { if (err) throw err
    })
}
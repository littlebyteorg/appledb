
const THREAD_COUNT = 16

const rewrite_map_v2 = {
    "https://updates.cdn-apple.com/": ["http://updates-http.cdn-apple.com/"],
    "https://mesu.apple.com/": ["http://mesu.apple.com/"],
    "https://secure-appldnld.apple.com/": ["http://appldnld.apple.com/", "http://appldnld.apple.com.edgesuite.net/content.info.apple.com/"],
    "https://download.developer.apple.com/": ["http://adcdownload.apple.com/"],
}

const needs_auth = ["adcdownload.apple.com", "download.developer.apple.com", "developer.apple.com"]



function updateLinks() {

}

module.exports = function register(grunt) {
    grunt.registerTask('update', 'update links', updateLinks)
}
const path = require('path')

module.exports = function(grunt) {

    grunt.initConfig({
        run: {
            options: {
                // Task-specific options go here.
            },
            jest: {
                cmd: 'npm',
                args: [
                    'run',
                    'test'
                ]
            }
        }
    });

    grunt.loadNpmTasks("grunt-ts");
    grunt.loadNpmTasks('grunt-run');

    grunt.loadTasks('tasks')

    grunt.registerTask('default', ['run:jest']);

};
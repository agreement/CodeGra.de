const fs = require('fs');
const ini = require('ini');
const execFileSync = require('child_process').execFileSync;

let userConfig = {};

try {
    userConfig = ini.parse(fs.readFileSync('./config.ini', 'utf-8'));
} catch (err) {
    process.stderr.write('Config file not found, using default values!\n');
}

if (userConfig['Front-end'] === undefined) userConfig['Front-end'] = {};
if (userConfig.Features === undefined) userConfig.Features = {};

const config = Object.assign({}, {
    email: 'info@CodeGra.de',
}, userConfig['Front-end']);

config.version = execFileSync('git', ['describe', '--abbrev=0', '--tags']).toString();
if (config.version.slice(-1) === '\n') {
    config.version = config.version.slice(0, -1);
}

config.features = Object.assign({}, {
    blackboard_zip_upload: true,
    rubrics: true,
    automatic_lti_role: true,
    LTI: true,
}, userConfig.Features);

module.exports = config;

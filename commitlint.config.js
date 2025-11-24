const allowedTypes = [
    'feat',
    'fix',
    'docs',
    'style',
    'refactor',
    'test',
    'chore',
    'build',
    'revert',
    'merge'
];

const allowedScopes = [
    'data',
    'ui',
    'theme',
    'dark-theme',
    'modal',
    'layout',
    'filters',
    'config',
    'build',
    'lint',
    'tests',
    'docs',
    'logging',
    'maintenance',
    'scripts',
    'assets',
    'deps'
];

module.exports = {
    allowedTypes,
    allowedScopes,
    extends: ['@commitlint/config-conventional'],
    rules: {
        'type-enum': [2, 'always', allowedTypes],
        'scope-enum': [2, 'always', allowedScopes],
        'scope-empty': [2, 'never'],
        'subject-case': [2, 'always', ['lower-case']]
    }
};

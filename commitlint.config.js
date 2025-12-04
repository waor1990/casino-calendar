const allowedTypes = [
    'feat',
    'fix',
    'docs',
    'style',
    'refactor',
    'perf',
    'test',
    'build',
    'ci',
    'chore',
    'merge',
    'revert'
];

const allowedScopes = [
    'app',
    'dash',
    'components',
    'layout',
    'styles',
    'theme',
    'data',
    'services',
    'logging',
    'config',
    'assets',
    'scripts',
    'deps',
    'branch',
    'tests',
    'docs',
    'ci',
    'infra'
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

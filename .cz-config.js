// cz-config.js
const { allowedTypes, allowedScopes } = require('./commitlint.config');

const typeDescriptions = {
    feat: 'feat:     A new feature',
    fix: 'fix:      A bug fix',
    docs: 'docs:     Documentation only',
    style: 'style:    Formatting, missing semi colons, etc',
    refactor: 'refactor: Code change that neither fixes a bug nor adds a feature',
    test: 'test:     Adding or updating tests',
    chore: 'chore:    Updating build tasks, deps, etc',
    build: 'build:    Build system or external dependencies',
    revert: 'revert:   Revert a previous commit',
    merge: 'merge:    Merge branches'
};

module.exports = {
    types: allowedTypes.map((type) => ({
        value: type,
        name: typeDescriptions[type] || `${type}:`
    })),
    scopes: allowedScopes.map((scope) => ({ name: scope })),
    messages: {
        type: "Select the type of change you're committing:",
        scope: 'Select the scope (component or file area):',
        subject: 'Write a short, imperative summary:\n'
    },
    skipQuestions: ['body', 'breaking', 'issues', 'footer'],
    allowCustomScopes: true
};

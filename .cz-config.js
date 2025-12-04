// cz-config.js
const { allowedTypes, allowedScopes } = require('./commitlint.config');

const typeDescriptions = {
    feat: 'feat:     A new feature',
    fix: 'fix:      A bug fix',
    docs: 'docs:     Documentation only',
    style: 'style:    Formatting, missing semicolons, etc',
    refactor: 'refactor: Code change that neither fixes a bug nor adds a feature',
    perf: 'perf:     Performance improvement without functional change',
    test: 'test:     Adding or updating tests',
    build: 'build:    Build system or external dependencies',
    ci: 'ci:       Continuous integration or automation changes',
    chore: 'chore:    Maintenance tasks and dependency updates',
    merge: 'merge:    Merge branches',
    revert: 'revert:   Revert a previous commit'
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

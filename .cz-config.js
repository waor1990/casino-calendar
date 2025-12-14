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

const scopeDescriptions = {
    app: 'app:      Entrypoints and server wiring',
    dash: 'dash:     Dash factory, callbacks, and layout glue',
    components: 'components: Reusable UI pieces and modal helpers',
    layout: 'layout:   High-level page structure',
    styles: 'styles:   Sass and CSS tokens',
    theme: 'theme:    Theme toggles and palettes',
    data: 'data:     Datasets, lookups, and transforms',
    services: 'services: Shared Python services and utilities',
    logging: 'logging:  Logging configuration and pipelines',
    config: 'config:   Settings, environment handling, and tooling config',
    assets: 'assets:   Static assets and client-side scripts',
    scripts: 'scripts:  Automation scripts (shell, Python, or Node)',
    deps: 'deps:     Dependency upgrades or pinning',
    branch: 'branch:   Release branches or branch hygiene changes',
    tests: 'tests:    Tests and fixtures',
    docs: 'docs:     Documentation changes',
    ci: 'ci:       CI/CD definitions and git hooks',
    infra: 'infra:    Deployment, hosting, and infrastructure changes'
};

module.exports = {
    types: allowedTypes.map((type) => ({
        value: type,
        name: typeDescriptions[type] || `${type}:`
    })),
    scopes: allowedScopes.map((scope) => ({
        value: scope,
        name: scopeDescriptions[scope] || `${scope}:`
    })),
    messages: {
        type: "Select the type of change you're committing:",
        scope: 'Select the scope (component or file area):',
        subject: 'Write a short, imperative summary:\n'
    },
    skipQuestions: ['body', 'breaking', 'issues', 'footer'],
    allowCustomScopes: true
};

# Commit conventions

Commit messages use Conventional Commits with a required scope and an imperative, lowercase subject. The commit hook rejects messages that do not follow the lists below.

## Allowed types

- `feat`: new feature work
- `fix`: bug fixes
- `docs`: documentation only
- `style`: formatting or lint-only changes
- `refactor`: internal restructuring without behaviour change
- `perf`: performance improvements
- `test`: adding or updating tests
- `build`: build tooling and external dependencies
- `ci`: pipelines, automation, and hooks
- `chore`: maintenance and dependency upkeep
- `merge`: merge branches
- `revert`: revert a previous commit

## Allowed scopes

- `app`: entrypoints and server wiring
- `dash`: Dash factory, callbacks, and layout glue
- `components`: reusable UI pieces and modal helpers
- `layout`: high-level page structure
- `styles`: Sass and CSS tokens
- `theme`: theme toggles and palettes
- `data`: datasets, lookups, and transforms
- `services`: shared Python services and utilities
- `logging`: logging configuration and pipelines
- `config`: settings, environment handling, and tooling config
- `assets`: static assets and client-side scripts
- `scripts`: automation scripts (shell, Python, or Node)
- `deps`: dependency upgrades or pinning
- `branch`: release branches or branch hygiene changes
- `tests`: tests and fixtures
- `docs`: documentation changes
- `ci`: CI/CD definitions and git hooks
- `infra`: deployment, hosting, and infrastructure changes

## How to use the prompt

Run `npm run commit` (or `npx git-cz`) to open the Commitizen prompt powered by `.cz-config.js`. It presents the allowed types and scopes above with short descriptions and formats the commit message to satisfy commitlint and the Husky `commit-msg` hook.

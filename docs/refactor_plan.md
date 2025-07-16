# 🗂️ Casino Calendar Refactor Plan

This document captures an audit of the current codebase and proposes a roadmap of improvements. Each item should be tracked as a GitHub issue.

## Architecture and Modular Design

- **#97 Split callback modules** – break up the oversized `app_components/callbacks.py` file.  Create focused modules such as `callbacks/events.py` and `callbacks/filters.py` and expose a `register_callbacks(app)` helper in each.
- **#98 Extract utilities** – move data parsing and color functions from `plotting.py` into `utils/data_parsing.py` and `utils/colors.py`.  Update imports throughout the codebase.
- **#99 Retire `legacy.py`** – migrate any still useful helpers into the new utils modules and add documentation for the remaining deprecated code.

## Callback and State Management

- **#100 Simplify chains** – extract duplicated logic from chained callbacks into reusable helpers to reduce complexity.
- **#101 Audit `Input`/`State` usage** – verify each callback only listens to values it truly depends on to prevent unnecessary renders.
- **#102 Document helpers** – add type hints and concise docstrings to every callback helper for easier maintenance.

## Grid and Modal Rendering

- **#103 Fix block overlap** – normalize event spans in `week_grid_layout.py` so mini blocks never cover full-day blocks and event blocks do not spand outside the week grid.
- **#104 Correct modal selection** – resolve click-through issues where a day modal opens instead of the event modal or no modal opens at all.
- **#105 Test breakpoints** – verify layout responsiveness at typical mobile and tablet widths.

## Styling and Responsiveness

- **#106 Consolidate variables** – move all repeated color and spacing variables into `_variables.scss` and remove unused styles.
- **#107 Standardize fonts** – apply `var(--font-*)` tokens to `.event-block-day_text`, `.week-label` and modal containers.
- **#108 Test text overflow** – create tests to ensure truncation and overflow behave on narrow screens.

## Data Handling and Time Normalization

- **#109 Validate DST logic** – check `data.py` when events cross daylight saving time boundaries and ensure offsets are correct.
- **#110 Normalize times** – store all times as naive UTC and convert to PDT only when displaying dates.
- **#111 Expand boundary tests** – add unit tests for multi-day events and DST changeovers.

## Testing Strategy

- **#112 Cover modals** – write tests for modal behaviour and scenarios with duplicated Sunday events.
- **#113 Parametrize suites** – extend tests to run across more casinos and offer types using pytest parametrize.
- **#114 Optional linters** – update `scripts/test.sh` to run `mypy`, `bandit` and `pydocstyle` when those tools are installed.

## Tooling and CI

- **#115 Update flake8** – ensure `.flake8` excludes the `.venv` directory (already completed).
- **#116 GitHub Actions** – create workflows to run `scripts/test.sh` and CSS linting on each pull request.
- **#117 Stylelint script** – add an npm script `lint:css` to invoke `stylelint` against SCSS files.

## GitHub Project Setup

1. Create a **Casino Calendar Refactor Plan** project board with columns: *To Do*, *In Progress*, *Review* and *Done*.
2. File issues under the categories below and assign a priority label (`critical`, `high`, `medium`, `low`).
3. Suggested milestones:
   - **v1.1 Bug Fixes** – immediate rendering and data issues.
   - **v1.2 Modal Rewrite** – improved callback and modal logic.
   - **v2.0 Architecture Cleanup** – module restructuring and new tooling.

### Issue Categories

- **UI/UX** – styling, grid layout and modal behaviour.
- **Logic & Architecture** – callback refactors and module separation.
- **Time & Data** – parsing, DST handling and week normalization.
- **Testing** – new test cases and coverage goals.
- **Tooling** – CI improvements and additional linters.

> **Note:** Creating GitHub issues and project boards requires authentication. Run the following once a valid token is available:
>
> ```bash
> gh auth login
> ./scripts/create_issues.sh  # to iterate through the roadmap and open issues
> ```

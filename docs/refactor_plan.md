# 🗂️ Casino Calendar Refactor Plan

This document captures an audit of the current codebase and proposes a roadmap of improvements. Each item should be tracked as a GitHub issue.

## Architecture and Modular Design

- Split large callback functions in `app_components/callbacks.py` into smaller modules.
- Move data parsing and color utilities from `plotting.py` into a dedicated `utils/colors.py` and `utils/data_parsing.py`.
- Deprecate `legacy.py` by migrating useful helpers into clearer modules and documenting the remainder.

## Callback and State Management

- Simplify chained callbacks by extracting shared logic into reusable functions.
- Review all `Input`/`State` pairs to ensure values are read only when necessary to avoid extra renders.
- Add type hints and docstrings for callback helper functions.

## Grid and Modal Rendering

- Ensure mini blocks never overlap full blocks in `week_grid_layout.py` by normalizing spans before rendering.
- Address click-through mismatches where day modal opens instead of event modal.
- Verify responsiveness on mobile and tablet breakpoints.

## Styling and Responsiveness

- Consolidate SCSS variables in `_variables.scss` and audit unused rules in `assets/styles`.
- Standardize font sizing for `.event-block-day_text`, `.week-label` and modal containers using `var(--font-*)` tokens.
- Add tests for text truncation and overflow on small screens.

## Data Handling and Time Normalization

- Validate DST logic in `data.py` when events span multiple days.
- Normalize times to naive UTC internally and convert to PDT only for display.
- Expand unit tests for multi-day events and DST boundary cases.

## Testing Strategy

- Increase coverage for modal behaviour and duplicated Sunday events.
- Parametrize existing tests to cover additional casinos and offer types.
- Integrate `mypy`, `bandit` and `pydocstyle` into `scripts/test.sh` when available.

## Tooling and CI

- Update `.flake8` to ignore the `.venv` directory (already done).
- Add GitHub Actions workflows for linting and testing on pull requests.
- Provide an npm script to run `stylelint` for SCSS files.

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

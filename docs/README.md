# Casino Calendar Documentation

This directory collects the living documentation for the project.

## Structure

- `architecture/`
  - [project_structure.md](architecture/project_structure.md) — Repository layout and code organisation.
  - [logging_system.md](architecture/logging_system.md) — Logging pipeline, rotation, and environment controls.
- `guides/`
  - [commit_conventions.md](guides/commit_conventions.md) — Allowed commit types/scopes and formatting rules enforced by commitlint/cz.
  - [TODO.md](guides/TODO.md) — Backlog of enhancements and stretch goals.
  - [vscode_terminal_troubleshooting.md](guides/vscode_terminal_troubleshooting.md) — Terminal configuration tips for Windows users.
- `operations/`
  - [log_management.md](operations/log_management.md) – Log retention, scheduled cleanup, and maintenance automation.
- `legacy/`
  - Archived documentation retained for historical context. Consult only when researching previous implementations.

Key entry points for the current app state are:

- [README.md](../README.md) — product overview, setup, and runtime behaviour.
- [QUICKSTART.md](../QUICKSTART.md) — shortest setup and run path.
- [architecture/project_structure.md](architecture/project_structure.md) — source tree map.

All documentation assumes the repository is checked out at the project root. When updating features, update the relevant guide in this folder in addition to the README.

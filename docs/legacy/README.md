# Archive Directory

This directory contains files that are no longer actively used but are preserved for historical reference.

## Archive Structure

### `deprecated_scripts/`

Contains scripts that are no longer functional or have been replaced by the maintained helpers under `scripts/windows/` and `scripts/shell/`:

- `run.bat` - Empty script file from the old scripts directory
- `setup.bat` - Empty script file from the old scripts directory
- `create_issues-v1.py` - Legacy script that referenced non-existent files (`docs/refactor_plan.md`)

### `legacy_docs/`

Contains documentation about deprecated features:

- `legacy_plotly.md` - Documentation about removed Plotly-based calendar rendering (replaced with CSS grid)

### `_archived/`

Historical utilities that used to live in the root-level `legacy/` folder. These are preserved for reference only and should not be executed:

- `deprecated_scripts/import_sanity.py` - Deprecated import validator for the removed `app_components` package

### `old_batch_files/`

Contains deprecated batch scripts that were replaced by the current Windows helpers under `scripts/windows/` (callable via the root `setup.bat` and `run.bat` launchers). Each file includes a README detailing why it was archived.

## Archiving Guidelines

When archiving files:

1. **Create appropriate subdirectories** based on file type and reason for archiving
2. **Document the reason** for archiving in this README
3. **Update any references** in active documentation to point to replacements
4. **Preserve historical context** - don't just delete, archive for future reference

## Current Active Alternatives

- **Scripts**: Use the maintained files in `scripts/windows/` (or the root proxy batch files) and `scripts/shell/` instead of archived scripts.
- **Calendar Rendering**: Uses CSS grid layout instead of the legacy Plotly approach.
- **Documentation**: Current docs are in the `docs/` directory root; architecture and operations guides live there.

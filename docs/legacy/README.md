# Archive Directory

This directory contains files that are no longer actively used but are preserved for historical reference.

## Archive Structure

### `deprecated_scripts/`

Contains scripts that are no longer functional or have been replaced:

- `run.bat` - Empty script file from scripts/ directory
- `setup.bat` - Empty script file from scripts/ directory  
- `create_issues-v1.py` - Legacy script that referenced non-existent files (`docs/refactor_plan.md`)

### `legacy_docs/`

Contains documentation about deprecated features:

- `legacy_plotly.md` - Documentation about removed Plotly-based calendar rendering (replaced with CSS grid)

### `old_batch_files/`

Contains deprecated batch scripts that were replaced by the current tools/ directory structure:

- Various old batch files with their own README.md explaining the deprecation

## Archiving Guidelines

When archiving files:

1. **Create appropriate subdirectories** based on file type and reason for archiving
2. **Document the reason** for archiving in this README
3. **Update any references** in active documentation to point to replacements
4. **Preserve historical context** - don't just delete, archive for future reference

## Current Active Alternatives

- **Scripts**: Use files in `tools/` directory instead of archived scripts
- **Calendar Rendering**: Uses CSS grid layout instead of legacy Plotly approach
- **Documentation**: Current docs are in `docs/` directory root

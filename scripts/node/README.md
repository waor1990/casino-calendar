# Node Scripts

This directory contains JavaScript utilities that support the Casino Calendar workflow. Some of the scripts are designed for the iOS Scriptable app while others provide local development tooling.

## Scripts

### `append-casino-event.mjs`

- **Purpose**: Adds new casino events to the CSV file
- **Platform**: iOS Scriptable app
- **Input**: JavaScript array of 6-item arrays (EventName, Casino, Location, Offer, StartDate, EndDate)
- **Features**: Duplicate detection, data validation, iCloud sync
- **Usage**: Run via iOS Shortcuts with casino event data
- **Data Format**: Requires properly formatted data (no escaped characters like `\[` or `\$`)

### `trim-old-casino-events.mjs`

- **Purpose**: Removes events older than 2 months to prevent CSV file growth
- **Platform**: iOS Scriptable app
- **Input**: None (automatically processes existing CSV file)
- **Features**: Casino-specific removal counts, robust CSV parsing, alert summary
- **Usage**: Run periodically in Scriptable app (manually or via automation)
- **Safety**: Preserves events with invalid dates, shows detailed removal summary

### `cleanup-node-modules.mjs`

- **Purpose**: Removes stale npm staging directories that trigger `npm warn cleanup` messages on Windows
- **Platform**: Local development (Node.js 18+)
- **Usage**: `npm run clean:node-modules` or `node scripts/node/cleanup-node-modules.mjs`
- **Notes**: Automatically runs as part of `scripts\windows\setup.bat` and the `npm run setup` workflow to ensure clean dependency installs.

## Integration

The iOS automation scripts integrate with the main Casino Calendar application by:

- **Data Source**: Both iOS scripts work with `iCloud/CasinoEvents/casino_events.csv`
- **Compatibility**: CSV format matches what the Dash app expects in `data/casino_events.csv`
- **Workflow**: Complete data lifecycle from addition (`append-casino-event.mjs`) to cleanup (`trim-old-casino-events.mjs`)

The `cleanup-node-modules.mjs` utility keeps the local `node_modules` tree tidy so that Windows developers can run `npm install` without cleanup warnings.

## Setup

1. Install the Scriptable app on iOS
2. Copy the script content into new Scriptable scripts
3. Ensure iCloud Drive is enabled for file access
4. Run via Scriptable app or integrate with iOS Shortcuts

## File Structure

The scripts expect this iCloud file structure:

```text
iCloud Drive/
└── Scriptable/
    └── CasinoEvents/
        ├── casino_events.csv (main data file)
        └── backups/ (created by cleanup script if needed)
```

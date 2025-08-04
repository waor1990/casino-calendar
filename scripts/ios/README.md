# iOS Scriptable Scripts

This directory contains JavaScript scripts designed for the iOS Scriptable app that manage casino event data as part of the Casino Calendar workflow.

## Scripts

### `AppendCasinoEventToCSV.js`

- **Purpose**: Adds new casino events to the CSV file
- **Platform**: iOS Scriptable app
- **Input**: JavaScript array of 6-item arrays (EventName, Casino, Location, Offer, StartDate, EndDate)
- **Features**: Duplicate detection, data validation, iCloud sync
- **Usage**: Run via iOS Shortcuts with casino event data
- **Data Format**: Requires properly formatted data (no escaped characters like `\[` or `\$`)

### `trimOldCasinoEvents.js`

- **Purpose**: Removes events older than 2 months to prevent CSV file growth
- **Platform**: iOS Scriptable app
- **Input**: None (automatically processes existing CSV file)
- **Features**: Casino-specific removal counts, robust CSV parsing, alert summary
- **Usage**: Run periodically in Scriptable app (manually or via automation)
- **Safety**: Preserves events with invalid dates, shows detailed removal summary

## Integration

These scripts integrate with the main Casino Calendar application by:

- **Data Source**: Both scripts work with `iCloud/CasinoEvents/casino_events.csv`
- **Compatibility**: CSV format matches what the Dash app expects in `data/casino_events.csv`
- **Workflow**: Complete data lifecycle from addition (`AppendCasinoEventToCSV.js`) to cleanup (`trimOldCasinoEvents.js`)

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

# Node Scripts

This directory contains JavaScript utilities that support the Casino Calendar workflow. Some of the scripts are designed for the iOS Scriptable app while others provide local development tooling.

## Scripts

### `append-casino-event.mjs`

- **Purpose**: Posts new casino events directly to the REST API (`POST /events`)
- **Platform**: iOS Scriptable app
- **Input**: Single event object or array of `[EventName, Casino, Location, Offer, StartDate, EndDate, (OfferType?)]`
- **Features**: Converts dates to ISO 8601 UTC, categorises offer types client-side using the same keyword lists as the Dash app, and sends JSON payloads (no CSV writes)
- **Usage**: Run via iOS Shortcuts with casino event data; set `apiUrl` to your API host

### `trim-old-casino-events.mjs`

- **Purpose**: Legacy CSV cleaner retained for archival workflows
- **Platform**: iOS Scriptable app
- **Notes**: The primary workflow now posts to the REST API; CSV cleanup is no longer required for the Dash app

### `cleanup-node-modules.mjs`

- **Purpose**: Removes stale npm staging directories that trigger `npm warn cleanup` messages on Windows
- **Platform**: Local development (Node.js 18+)
- **Usage**: `npm run clean:node-modules` or `node scripts/node/cleanup-node-modules.mjs`
- **Notes**: Retries deletions that fail with `EPERM/EACCES` by resetting permissions, and runs automatically via npm's `preinstall` hook (including during `npm ci`), the Windows setup script, and the `npm run setup` workflow.

### `verify-package-json.mjs`

- **Purpose**: Ensures `package.json` remains valid JSON and free of Git merge conflict markers before installations.
- **Platform**: Local development (Node.js 18+)
- **Usage**: `npm run lint:package-json` or `node scripts/node/verify-package-json.mjs`
- **Notes**: The Windows setup script runs this validator automatically and exits early with guidance if a merge conflict is detected.

## Integration

The iOS automation scripts integrate with the main Casino Calendar application by:

- **Data Source**: `append-casino-event.mjs` posts to the REST API backed by `data/events.json`
- **Compatibility**: Dash fetches events from the API via `APIEventRepository`
- **Workflow**: CSV utilities are retained only for legacy pipelines

The `cleanup-node-modules.mjs` utility keeps the local `node_modules` tree tidy so that Windows developers can run `npm install` without cleanup warnings.

## Setup

1. Install the Scriptable app on iOS
2. Copy the script content into new Scriptable scripts
3. Update `apiUrl` in `append-casino-event.mjs` to point at your API host/IP (port 5001 by default)
4. Run via Scriptable app or integrate with iOS Shortcuts

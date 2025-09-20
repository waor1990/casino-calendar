# Casino Calendar - Next Steps

This document outlines the upcoming improvements and high‑priority tasks for the project.

## Data Processing

- Extract data manipulation from UI components into dedicated utility modules.
- Introduce a validation layer (e.g., Pydantic) for event and configuration data.
- Cache JSON configuration files at application start instead of on each call.

## Performance

- Refactor `assign_event_rows()` to reduce complexity and improve runtime.
- Minimize repeated DataFrame copies during filtering and transformation.

## Testing

- Expand tests for timezone edge cases and malformed input data.
- Add integration tests covering the flow from CSV inputs to rendered views.

## Features

- Provide data export functionality for filtered event sets.
- Implement a caching layer for processed event data to speed up rendering.


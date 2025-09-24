# Logging System Documentation

## Overview

The Casino Calendar application implements a comprehensive logging system to facilitate debugging, monitoring, and tracing of application behavior. The logging system is built on Python's standard `logging` library with custom formatters and structured output.

## Features

### 🎯 Centralized Configuration

- Single configuration module (`casino_calendar/logging/config.py`)
- Environment variable-based log level control
- Consistent formatting across all modules

### 📊 Structured Output

- Timestamp, log level, module name, and message
- Color-coded console output for better readability
- Optional file output with rotation

### ⚡ Performance Monitoring

- Automatic performance logging for key operations
- Data loading and processing time tracking
- Callback execution timing

### 🐛 Error Tracking

- Comprehensive exception logging with stack traces
- Context-aware error messages in callbacks
- Graceful error handling with fallback behaviors

## Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LOG_LEVEL` | Sets the minimum log level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_FILE` | Optional file output path | None | `logs/casino_calendar.log` |

### Usage Examples

```bash
# Development mode with debug logging
LOG_LEVEL=DEBUG python app.py

# Production mode with file logging
LOG_LEVEL=INFO LOG_FILE=logs/app.log gunicorn app:server

# Debug with file output
LOG_LEVEL=DEBUG LOG_FILE=debug.log python app.py
```

### Environment File (.env)

Create a `.env` file in the project root:

```env
# Development settings
LOG_LEVEL=DEBUG
LOG_FILE=logs/casino_calendar_dev.log

# Production settings
# LOG_LEVEL=INFO
# LOG_FILE=logs/casino_calendar_prod.log
```

## Log Levels

### DEBUG

- Function calls with parameters
- DataFrame shapes and column information
- Detailed callback execution flow
- Performance timing details

### INFO

- Application startup and shutdown
- Data loading completion
- Modal open/close events
- Theme changes
- Major operation summaries

### WARNING

- Invalid data encountered
- Missing configuration files
- Non-critical errors with fallbacks

### ERROR

- File not found errors
- JSON parsing failures
- Callback execution errors
- Database connection issues

### CRITICAL

- Application startup failures
- Unrecoverable errors
- System-level failures

## Log Output Format

### Console Output (with colors)

```log
2025-07-29 10:15:30 | INFO     | app                  | Casino Calendar application starting up
2025-07-29 10:15:30 | DEBUG    | casino_calendar.dash_app.data.loader  | Loading event data from data/casino_events.csv
2025-07-29 10:15:31 | INFO     | casino_calendar.dash_app.data.loader  | Event data loaded successfully in 0.234s
```

### File Output (no colors)

```log
2025-07-29 10:15:30 | INFO     | app                  | Casino Calendar application starting up
2025-07-29 10:15:30 | DEBUG    | casino_calendar.dash_app.data.loader  | Loading event data from data/casino_events.csv
2025-07-29 10:15:31 | INFO     | casino_calendar.dash_app.data.loader  | Event data loaded successfully in 0.234s
```

## JavaScript Logging

The client-side JavaScript includes console logging for theme operations:

```javascript
console.info('[CasinoCalendar] Applied dark theme');
console.debug('[CasinoCalendar] Theme button updated: ☀️');
console.warn('[CasinoCalendar] Theme toggle button not found');
```

View these logs in the browser's Developer Tools (F12) → Console tab.

## Integration Points

### Application Modules

- `app.py`: Application lifecycle events
- `dash_app/data/loader.py`: Data loading and processing
- `dash_app/layout/root.py`: UI component creation
- `dash_app/callbacks/`: User interaction events
- `casino_calendar/services/`: Shared service utilities

### Key Operations Logged

1. **Application Startup**
   - Configuration loading
   - Data file reading
   - Layout creation
   - Callback registration

2. **Data Processing**
   - CSV file loading
   - Date/time conversions
   - Offer categorization
   - Event filtering

3. **User Interactions**
   - Modal open/close events
   - Theme toggles
   - Week navigation
   - Event clicks

4. **Performance Metrics**
   - Data loading times
   - Callback execution duration
   - Modal generation performance

## Best Practices

### For Developers

1. Use appropriate log levels
2. Include relevant context in messages
3. Log both successful operations and errors
4. Use structured logging for complex data

### For Production

1. Set `LOG_LEVEL=INFO` or `LOG_LEVEL=WARNING`
2. Enable file logging with rotation
3. Monitor log files for errors
4. Use log aggregation tools for multiple instances

### For Debugging

1. Set `LOG_LEVEL=DEBUG` temporarily
2. Check both console and file outputs
3. Look for performance bottlenecks in timing logs
4. Use browser console for client-side issues

## File Rotation

File logging includes automatic rotation:

- Maximum file size: 10MB
- Backup count: 5 files
- Old files are automatically compressed and renamed

## Security Considerations

- Log files may contain sensitive data
- Ensure proper file permissions
- Consider log retention policies
- Avoid logging passwords or tokens

## Troubleshooting

### Common Issues

1. **No log output**: Check `LOG_LEVEL` environment variable
2. **File not created**: Verify directory permissions
3. **Console colors missing**: Check if terminal supports ANSI colors
4. **Performance slow**: Reduce log level in production

### Debug Commands

```bash
# Check current log level
python -c "import os; print(f'LOG_LEVEL={os.getenv(\"LOG_LEVEL\", \"INFO\")}')"

# Test logging configuration
python -c "from casino_calendar.logging.config import app_logger; app_logger.info('Test message')"

# Verify file logging
LOG_FILE=test.log python -c "from casino_calendar.logging.config import setup_logger; setup_logger('test', 'test.log').info('Test file logging')"
```

## Extending the Logging System

### Adding New Modules

```python
from casino_calendar.logging.config import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

def my_function():
    logger.info("Function started")
    try:
        # Your code here
        logger.debug("Processing data")
    except Exception as e:
        logger.error(f"Error in my_function: {e}")
        raise
```

### Custom Log Levels

```python
import logging

# Add custom levels if needed
logging.addLevelName(35, 'BUSINESS')
logger.business = lambda msg: logger.log(35, msg)
```

### Performance Logging

```python
import time
from casino_calendar.logging.config import log_performance

start_time = time.time()
# ... your operation ...
end_time = time.time()
log_performance(logger, "my_operation", start_time, end_time)
```

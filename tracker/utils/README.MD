# `tor_manager.py` - Tor Process Management Module

## Overview

`tor_manager.py` is a utility module that manages the Tor process for the ransomware tracker system. It handles all aspects of Tor lifecycle including starting, monitoring, and stopping the service, ensuring the browser module has a working Tor connection available.

## Key Features

- **Automatic Tor management**: Starts and stops Tor as needed
- **Configuration-based setup**: Uses external JSON for all Tor settings
- **Dynamic configuration**: Creates temporary torrc files on-the-fly
- **Process monitoring**: Verifies Tor is running on the expected port
- **Cleanup handling**: Properly terminates processes and removes temporary files
- **GitHub Actions compatibility**: Special handling for CI/CD environments

## Main Functions

### `load_proxy_config()`

Loads proxy and Tor configuration from a JSON file.

- **Returns**: Dictionary containing proxy and Tor configuration
- **Features**: Falls back to sensible defaults if configuration is missing

### `create_temp_torrc()`

Creates a temporary torrc configuration file for Tor.

- **Returns**: Path to the created temporary file or None on error
- **Features**: Registers cleanup functions for automatic removal

### `start_tor()`

Starts the Tor process with the generated configuration.

- **Returns**: Boolean - True if Tor started successfully
- **Features**:
  - Checks if auto-start is enabled in configuration
  - Verifies Tor is installed in the system
  - Starts Tor with appropriate settings
  - Registers cleanup handlers

### `stop_tor()`

Gracefully stops the Tor process.

- **Features**:
  - Attempts graceful termination first
  - Falls back to force kill if termination times out
  - Nullifies process references for garbage collection

### `is_tor_running()`

Checks if Tor is already running on the configured port.

- **Returns**: Boolean - True if Tor is running
- **Implementation**: Uses `lsof` to check if the configured port is in use

### `ensure_tor_running()`

Main entry point that ensures Tor is running, starting it if necessary.

- **Returns**: Boolean - True if Tor is running (existing or newly started)
- **Usage**: Called by main.py before starting browser operations

## Usage Example

```python
from tracker.utils.tor_manager import ensure_tor_running

# Make sure Tor is available before starting browser
if ensure_tor_running():
    # Continue with browser setup and scraping
    setup_browser_and_scrape()
else:
    logger.error("Cannot ensure Tor is running. Exiting.")
    exit(1)
```

## Integration

This module works closely with tor_browser.py to ensure the Selenium browser instance has a working Tor proxy to connect through. It's typically called early in the application lifecycle to ensure Tor is available for subsequent operations.

# `file_utils.py` - JSON File Handling Utilities

## Overview

`file_utils.py` provides robust functions for loading and saving JSON data with comprehensive error handling. It's a core utility module used throughout the ransomware tracker system for all file operations.

## Key Features

- **Error-resilient operations**: Handles common file errors gracefully
- **Comprehensive logging**: Detailed error and debug messages
- **Directory creation**: Automatically creates missing directories
- **Safe defaults**: Returns empty dictionaries rather than failing
- **Status reporting**: Returns success/failure for all operations

## Main Functions

### `load_json(filename, output_dir)`

Loads JSON data from a file with thorough error handling.

- **Parameters**:
  - `filename`: Name of the JSON file to load
  - `output_dir`: Directory containing the file
- **Returns**: Loaded JSON data as a Python dictionary (or empty dict on error)
- **Error Handling**:
  - Handles missing files by returning an empty dictionary
  - Handles malformed JSON by returning an empty dictionary
  - Logs appropriate messages for different error types

### `save_json(data, filename, output_dir)`

Saves data to a JSON file with directory creation and error handling.

- **Parameters**:
  - `data`: Python dictionary to save as JSON
  - `filename`: Name of the file to save
  - `output_dir`: Directory to save the file in
- **Returns**: Boolean - True on success, False on failure
- **Features**:
  - Automatically creates parent directories if they don't exist
  - Pretty-prints JSON with 4-space indentation
  - Provides debug logging on success

## Usage Example

```python
from tracker.utils.file_utils import load_json, save_json

# Save data to a file
entity_data = {
    "entities": [
        {"id": "entity1", "domain": "example.com"},
        {"id": "entity2", "domain": "sample.org"}
    ],
    "total_count": 2
}
success = save_json(entity_data, "entities.json", "data/output")

# Load data from a file
loaded_data = load_json("entities.json", "data/output")
entity_count = loaded_data.get("total_count", 0)
```

## Integration

This module is used extensively throughout the ransomware tracker system for loading configuration files, saving entity data, and maintaining state between runs.

# `logging_utils.py` - Logging Configuration Module

## Overview

`logging_utils.py` is a simple but essential module that provides standardized logging configuration for the entire ransomware tracker system, ensuring consistent log format and behavior across all components.

## Key Features

- **Standardized format**: Consistent timestamp, level, and message format
- **Console output**: Configured for immediate feedback during execution
- **Appropriate log levels**: Uses INFO level by default
- **Reusable logger**: Provides a pre-configured logger instance

## Main Functions

### `setup_logging()`

Configures and returns a logger with standardized format and handlers.

- **Returns**: Configured logging.Logger instance
- **Configuration**:
  - Sets logging level to INFO
  - Uses format: '%(asctime)s - %(levelname)s - %(message)s'
  - Configures StreamHandler for console output

## Module-Level Variables

### `logger`

A pre-configured logger instance that can be imported and used directly.

```python
from tracker.utils.logging_utils import logger

logger.info("Operation succeeded")
logger.error("An error occurred")
```

## Usage Example

```python
from tracker.utils.logging_utils import logger

def process_site(site_config):
    site_name = site_config.get('site_name', 'Unknown')
    logger.info(f"Processing site: {site_name}")
    
    try:
        # Process the site
        result = do_something_complex()
        logger.info(f"Successfully processed {site_name}")
        return result
    except Exception as e:
        logger.error(f"Error processing {site_name}: {e}")
        return None
```

## Integration

This module is typically imported at the top of other modules to provide logging capabilities. The consistent logger configuration ensures that all log messages throughout the system have the same format and appear in the same location, making debugging and monitoring much easier.
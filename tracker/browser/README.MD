# `tor_browser.py` - Tor Browser Integration Module

## Overview

`tor_browser.py` is a critical component of the ransomware tracker system that handles all Tor browser interactions. It provides a secure and configurable interface to access .onion sites through the Tor network using Selenium with Firefox.

## Key Features

- **Configuration-based setup**: Loads browser, proxy, and scraping settings from external JSON files
- **Automated Tor connection**: Configures Firefox to route traffic through the Tor network
- **Anti-bot measures**: Implements configurable wait times to bypass anti-scraping protections
- **Mirror management**: Tests multiple site mirrors until finding one that works
- **HTML snapshot capabilities**: Optionally saves HTML content for analysis with automatic cleanup
- **Robust error handling**: Comprehensive logging and error recovery

## Main Functions

### `setup_tor_browser(headless=False)`

Creates and configures a Firefox WebDriver instance to use Tor as a proxy.

- **Parameters**:
  - `headless`: Boolean (default: False) - Whether to run Firefox in headless mode
- **Returns**: Configured Selenium WebDriver instance
- **Features**:
  - Sets proxy settings based on configuration
  - Configures user agent and other browser preferences
  - Handles Firefox binary path for compatibility with GitHub Actions
  - Sets page load timeouts

### `test_tor_connection(driver)`

Verifies that the browser is correctly connected to the Tor network.

- **Parameters**:
  - `driver`: WebDriver instance
- **Returns**: Boolean - True if successfully connected to Tor
- **Implementation**: Visits check.torproject.org and looks for "Congratulations" text

### `browse_with_selenium(driver, url, site_config, wait_time=None)`

Navigates to a URL and handles anti-bot measures.

- **Parameters**:
  - `driver`: WebDriver instance
  - `url`: URL to visit
  - `site_config`: Dictionary with site configuration
  - `wait_time`: Optional delay after page load (uses configured random time if None)
- **Returns**: Page source HTML if successful, None otherwise
- **Verification**: Checks for expected content based on site_verification config

### `get_working_mirror(driver, site_config)`

Tries multiple mirrors for a site until finding one that works.

- **Parameters**:
  - `driver`: WebDriver instance
  - `site_config`: Dictionary with site configuration including mirrors list
- **Returns**: Tuple of (working_mirror, html_content) or (None, None) if all failed

### `save_html_snapshot(html_content, site_key, html_snapshots_dir)`

Saves HTML content to a timestamped file.

- **Parameters**:
  - `html_content`: HTML content to save
  - `site_key`: Site identifier (used in directory/filename)
  - `html_snapshots_dir`: Directory to save snapshots
- **Returns**: Path to saved file or None if saving is disabled
- **Features**: 
  - Respects configuration settings (save_html toggle)
  - Automatically cleans up old snapshots

## Configuration Management

The module loads three types of configuration:

1. **Browser Configuration** (`browser_config.json`):
   - Timing parameters (wait times, timeouts)
   - Anti-bot settings
   - User agent information

2. **Proxy Configuration** (`proxy_config.json`):
   - Tor proxy settings (host, port)
   - Remote DNS settings

3. **Scraping Configuration** (`scraping_config.json`):
   - HTML snapshot settings
   - Snapshot retention policy

## Usage Example

```python
from tracker.browser.tor_browser import setup_tor_browser, test_tor_connection, get_working_mirror

# Initialize the browser
driver = setup_tor_browser(headless=True)

# Verify Tor connection
if test_tor_connection(driver):
    # Define site configuration
    site_config = {
        'site_name': 'Example Site',
        'mirrors': ['example1.onion', 'example2.onion'],
        'site_verification': {'type': 'text', 'value': 'Example'}
    }
    
    # Try to find a working mirror
    mirror, html = get_working_mirror(driver, site_config)
    
    if html:
        # Process the HTML content
        process_html(html)
```

## Error Handling

The module includes comprehensive error handling with detailed logging, especially for GitHub Actions environments where diagnosing browser issues can be challenging.

## Integration

This module is designed to work within the larger ransomware tracker system, with functionality that supports the scraping of multiple ransomware sites running through the Tor network.
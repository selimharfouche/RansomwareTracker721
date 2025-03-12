TODO : FILTER ALSO ON MPAGE BY CAPITAL, ENTREPRISE SIZE ETC CHECK JSON


TODO: change JSON LIKE AFTER AI PROCESS COPY IT TO WEBSITE DIRECTORY  !
To use this system:

Run python create_configs.py --all to create the initial configuration files
Run python main.py to process all configured sites
Or run python main.py --sites lockbit bashe to process specific sites


tor config :
a12@1 721 % cat  ~/.tor/torrc

SocksPort 9050
ControlPort 9051
CookieAuthentication 1
# Longer circuit timeout for onion services
CircuitBuildTimeout 60
# More aggressive circuit handling
LearnCircuitBuildTimeout 0
# Improve onion service performance
HiddenServiceStatistics 0
OptimisticData 1
a12@1 721 % tor -f ~/.tor/torrc



website: 
using version 4 of tailwind, conf in the globalcss !




# `main.py` - Ransomware Tracker Entry Point

## Overview

`main.py` serves as the primary entry point for the ransomware tracker system. It orchestrates the entire scraping process by coordinating all components: setting up Tor, loading configurations, initializing browsers, managing site scraping, and sending notifications when the operation completes.

## Key Features

- **Configuration-based operation**: Processes multiple ransomware sites based on JSON configurations
- **Selective scraping**: Supports scraping all available sites or specific requested sites
- **Environment detection**: Auto-detects GitHub Actions environment for headless operation
- **Tor integration**: Ensures Tor is running before attempting to scrape sites
- **Comprehensive metrics**: Tracks processed sites, total entities, and new discoveries
- **Notification system**: Sends completion notifications with operation statistics
- **Error resilience**: Handles failures gracefully with proper logging
- **Command-line interface**: Supports arguments for customizing operation

## Main Functions

### `process_site(driver, site_config)`

Processes a single ransomware site using a GenericParser.

- **Parameters**:
  - `driver`: Selenium WebDriver instance with Tor configured
  - `site_config`: Dictionary with site configuration
- **Returns**: Boolean - True if scraping was successful
- **Implementation**: Creates a GenericParser instance and initiates scraping

### `main(target_sites=None)`

The primary function that coordinates the entire scraping process.

- **Parameters**:
  - `target_sites`: Optional list of site keys to process (processes all if None)
- **Features**:
  - Ensures Tor is running
  - Loads site configurations
  - Validates requested sites against available sites
  - Sets up the browser with Tor
  - Processes each site
  - Counts entities and tracks new discoveries
  - Sends completion notification
  - Ensures proper cleanup of resources

## Command-Line Arguments

The script supports two command-line arguments:

1. `--sites`: Space-separated list of site keys to scrape (e.g., `--sites lockbit bashe`)
2. `--headless`: Flag to run the browser in headless mode for server environments

Example usage:
```bash
python -m tracker.main --sites lockbit ransomhub --headless
```

## Environment Detection

The script automatically detects when it's running in GitHub Actions:

- Uses headless browser mode
- Skips Tor startup (assumes Tor is already running from workflow)
- Adapts to CI/CD environment constraints

## Workflow Process

1. **Initialization**:
   - Ensures all necessary directories exist
   - Sets up logging
   - Initializes tracking variables

2. **Environment Setup**:
   - Checks if running in GitHub Actions
   - Ensures Tor is running
   - Loads site configurations

3. **Target Selection**:
   - Processes all available sites if no targets specified
   - Validates requested sites against available configurations

4. **Browser Setup**:
   - Initializes Selenium with Tor configuration
   - Tests Tor connectivity

5. **Site Processing**:
   - Iterates through target sites
   - Creates parser for each site
   - Tracks entity counts and new discoveries

6. **Completion**:
   - Ensures browser is properly closed
   - Sends notification with operation results
   - Reports any errors encountered

## Usage Examples

### Process All Available Sites

```python
python -m tracker.main
```

### Process Specific Sites

```python
python -m tracker.main --sites lockbit bashe
```

### Run in Headless Mode for Server Environments

```python
python -m tracker.main --headless
```

## Integration

This module is the central coordinator that integrates all components of the ransomware tracker system:

- **Utils**: For Tor management, logging, and file operations
- **Browser**: For Tor browser setup and connection
- **Scraper**: For scraping and parsing site content
- **Config**: For loading site configurations
- **Notifications**: For sending Telegram notifications

The centralized design allows for the entire system to be run from a single entry point, making it ideal for scheduled execution in CI/CD environments or as a standalone application.
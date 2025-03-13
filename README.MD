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

# Ransomware Tracker

A comprehensive system for monitoring and analyzing ransomware leak sites through Tor. This project automatically tracks multiple ransomware groups, detects new victims, standardizes data formats, and provides real-time notifications.

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Telegram Notifications](#telegram-notifications)
7. [AI Data Enrichment](#ai-data-enrichment)
8. [Directory Structure](#directory-structure)

## Project Overview

The Ransomware Tracker automatically monitors various ransomware leak sites through Tor, identifying and tracking entities (victims) that have been targeted by ransomware groups. Key features include:

- **Multi-site monitoring**: Tracks multiple ransomware groups (LockBit, Bashe, RansomHub, etc.)
- **Configuration-based architecture**: Add new ransomware sites without code changes
- **Entity tracking**: Identifies new victims and tracks their status over time
- **Real-time notifications**: Sends alerts via Telegram when new victims are discovered
- **Data standardization**: Converts different date formats and fields to a consistent structure
- **AI enrichment**: Enhances victim data with organizational information using AI
- **GitHub Actions integration**: Runs automatically on schedule in the cloud

The system is designed for cybersecurity researchers, threat intelligence analysts, and organizations that need to monitor ransomware activity across the threat landscape.

## System Architecture

The system uses a modular, configuration-based architecture:

1. **Scraper Module**: Connects to ransomware sites via Tor and extracts HTML content
2. **Parser Module**: Uses site-specific configurations to extract entity information
3. **Processing Pipeline**: Standardizes and archives entity data
4. **Notification System**: Sends real-time alerts via Telegram
5. **AI Enrichment**: Enhances entity data with additional organizational information

Data flows through the system as follows:
- Raw HTML → Structured JSON → Standardized formats → AI enrichment → Notifications

The configuration-based approach allows adding new ransomware sites by simply creating a JSON configuration file, without modifying any code.

## Installation

### Prerequisites

- Python 3.9+
- Tor service
- Firefox (for Selenium)
- Geckodriver (for Selenium)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ransomware-tracker.git
   cd ransomware-tracker
   ```

2. Create and activate a virtual environment:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate on Windows
   venv\Scripts\activate
   
   # Activate on macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your Telegram credentials (if using notifications):
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHANNEL_ID=your_channel_id_here
   ```

5. For AI enrichment, add your OpenAI API key to the `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Configuration

The system uses JSON configuration files to control various aspects of operation.

### Site Configurations

Site configurations are stored in `config/sites/` with one file per ransomware group. Example:

```json
{
  "site_key": "lockbit",
  "site_name": "LockBit",
  "json_file": "lockbit_entities.json",
  "mirrors": [
    "lockbit3753ekiocyo5epmpy6klmejchjtzddoekjlnt6mu3qh4de2id.onion",
    "lockbit3g3ohd3katajf6zaehxz4h4cnhmz5t735zpltywhwpc6oy3id.onion"
  ],
  "site_verification": {
    "type": "text",
    "value": "LockBit"
  },
  "parsing": {
    "entity_selector": "a.post-block",
    "fields": [
      {
        "name": "id",
        "type": "attribute",
        "selector": "self",
        "attribute": "href",
        "regex": "^\\/?(.+)$",
        "regex_group": 1
      },
      // Additional field configurations...
    ]
  }
}
```

### Browser Configuration

Browser settings are controlled in `config/code/browser_config.json`:

```json
{
  "timing": {
    "min_wait_time": 10,
    "max_wait_time": 20,
    "tor_check_wait_time": 3,
    "page_load_timeout": 120
  },
  "anti_bot": {
    "enabled": true,
    "randomize_timing": true
  },
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"
}
```

### Proxy Configuration

Tor and proxy settings are configured in `config/code/proxy_config.json`:

```json
{
  "proxy": {
    "type": "socks",
    "host": "127.0.0.1",
    "port": 9050,
    "remote_dns": true
  },
  "tor": {
    "auto_start": true,
    "config": [
      "SocksPort 9050",
      "ControlPort 9051",
      "CookieAuthentication 1",
      "CircuitBuildTimeout 60"
    ]
  }
}
```

### Scraping Configuration

Scraping behavior is controlled in `config/code/scraping_config.json`:

```json
{
  "snapshots": {
    "save_html": false,
    "max_snapshots_per_site": 5,
    "cleanup_old_snapshots": true
  },
  "scheduling": {
    "frequency_hours": 6,
    "randomize_start_time": true
  }
}
```

## Usage

### Basic Usage

Run the main script to scrape all configured sites:

```bash
cd tracker
python main.py
```

### Command Line Options

```bash
# Scrape specific sites
python main.py --sites lockbit bashe

# Run in headless mode (no visible browser)
python main.py --headless

# Skip entity processing after scraping
python main.py --no-process
```

### Creating New Site Configurations

To track a new ransomware group, create a configuration file:

```bash
python create_configs.py --sites new_ransomware_group
```

Then edit the generated file in `config/sites/` to match the site's structure.

### GitHub Actions Integration

The project includes a GitHub Actions workflow (`scrape.yml`) that runs the scraper automatically on a schedule. To use it:

1. Fork the repository
2. Add your Telegram credentials as GitHub secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHANNEL_ID`
3. Enable GitHub Actions in your repository

The workflow runs every 6 hours by default, but you can modify the schedule in the workflow file.

## Telegram Notifications

The system can send real-time notifications about new ransomware victims via Telegram.

### Setting Up Telegram Bot

1. Create a Telegram bot using [@BotFather](https://t.me/botfather)
2. Create a Telegram channel or group
3. Add your bot to the channel/group as an admin
4. Get the channel ID (can be in format `-100xxxxxxxxxx`)
5. Add these credentials to your `.env` file or GitHub secrets

### Types of Notifications

The system sends two types of notifications:

1. **Entity Notifications**: Sent when a new ransomware victim is discovered
2. **Scan Completion Notifications**: Sent at the end of each scan with a summary

Example entity notification:
```
🚨 New Ransomware Victim Discovered!

Domain: example.com
Ransomware Group: LockBit
Status: ⏳ Countdown
Views: 156

Description:
Example Corp data breach including financial records and customer information...

Countdown: 5d 4h 32m 15s
Estimated Publication: 2023-09-15 12:30:00 UTC

First seen: 2023-09-10 08:15:22 UTC
```

### Notification Logs

All notifications are logged to `logs/telegram_notifications.log` for history tracking.

## AI Data Enrichment

The system can enrich entity data with organizational information using the OpenAI API.

### Setup

1. Add your OpenAI API key to the `.env` file
2. Run the extraction script to prepare data:
   ```bash
   cd AI
   python extract_ai_fields.py
   ```
3. Run the enrichment process:
   ```bash
   python domain_enrichment.py
   ```

### Batch Processing

The enrichment process works in batches of 100 domains by default. You can:
- Preview batches before processing (`python domain_enrichment.py`)
- Automatically process all batches (`python domain_enrichment.py --yes`)
- Hide preview details (`python domain_enrichment.py --no-preview`)

### Output Data

The AI enrichment adds the following information to each entity:

```json
{
  "domain": "example.com",
  "geography": {
    "country_code": "USA",
    "region": "California",
    "city": "San Francisco"
  },
  "organization": {
    "name": "Example Corporation",
    "industry": "Technology",
    "sub_industry": "Software Development",
    "size": {
      "employees_range": "100-499",
      "revenue_range": "$10M-$50M"
    },
    "status": "Private"
  }
}
```

The enriched data is saved to `AI/processed_AI.json`.

## Directory Structure

```
project-root/
├── tracker/                    # Python code
│   ├── main.py                 # Main script
│   ├── create_configs.py       # Script to create site configs
│   ├── browser/                # Browser modules
│   │   ├── __init__.py
│   │   └── tor_browser.py      # Tor browser management
│   ├── config/                 # Configuration handling
│   │   ├── __init__.py
│   │   └── config_handler.py   # Configuration loader
│   ├── scraper/                # Scraper modules
│   │   ├── __init__.py
│   │   ├── base_parser.py      # Base parser class
│   │   └── generic_parser.py   # Generic site parser
│   ├── processing/             # Data processing scripts
│   │   ├── __init__.py
│   │   ├── entity_merger.py    # Combines entities from all sites
│   │   ├── process_entities.py # Standardizes and archives entities
│   └── telegram_bot/           # Telegram notification system
│       ├── __init__.py
│       └── notifier.py         # Notification sender
├── config/                     # Configuration files
│   ├── sites/                  # Site configurations
│   │   ├── lockbit.json        # LockBit configuration
│   │   └── bashe.json          # Bashe configuration
│   └── code/                   # Code-related configurations
│       ├── browser_config.json # Browser settings
│       ├── proxy_config.json   # Proxy and Tor settings
│       └── scraping_config.json # Scraping behavior settings
├── data/                       # Data storage
│   ├── output/                 # Raw JSON output
│   │   ├── lockbit_entities.json
│   │   ├── bashe_entities.json
│   │   └── new_entities.json   # Newly discovered entities
│   ├── processed/              # Processed data
│   │   ├── all_entities.json   # All entities merged
│   │   └── final_entities.json # Standardized archive
│   ├── new_entities_snapshot/  # Historical snapshots
│   └── html_snapshots/         # Raw HTML snapshots
├── AI/                         # AI enrichment system
│   ├── extract_ai_fields.py    # Extracts fields for AI processing
│   ├── domain_enrichment.py    # Enriches domains with OpenAI
│   ├── AI.json                 # Extracted basic entity data
│   ├── processed_AI.json       # Enriched entity data
│   ├── raw_responses/          # Raw API responses
│   └── batch_previews/         # Preview of batch requests
├── logs/                       # Log files
│   └── telegram_notifications.log # Notification history
├── .github/                    # GitHub configuration
│   └── workflows/
│       └── scrape.yml          # GitHub Actions workflow
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

This README provides an overview of the project's functionality and usage. For more detailed information about specific components, refer to the documentation in the corresponding directories.
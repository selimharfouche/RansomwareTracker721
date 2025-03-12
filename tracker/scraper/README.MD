# `base_parser.py` - Abstract Base Parser

## Overview

`base_parser.py` defines the foundational `BaseParser` abstract class that serves as the template for all site-specific parsers in the ransomware tracker system. It establishes a common interface and implements shared functionality for site scraping, entity tracking, and notification.

## Key Features

- **Abstract template**: Provides a consistent interface for all site parsers
- **Entity management**: Handles entity database creation and updates
- **New entity detection**: Identifies and tracks newly discovered entities
- **Snapshot creation**: Creates timestamped snapshots of new discoveries
- **Notification integration**: Dynamically imports and calls the Telegram notifier
- **Dual storage approach**: Maintains both site-specific files and central tracking

## Core Methods

### `scrape_site()`

Coordinates the end-to-end site scraping process.

- Connects to a working mirror
- Saves HTML snapshots
- Triggers entity parsing
- Updates the entity database
- **Returns**: HTML content (or `None` if failed)

### `parse_entities(html_content)` [Abstract]

Abstract method that must be implemented by subclasses to extract entities from HTML.

- **Parameters**: HTML content from the site
- **Returns**: List of entity dictionaries

### `update_entities_database(new_entities)`

Updates the site-specific entity database with newly scraped entities:

- Compares with existing entities to identify truly new ones
- Preserves first_seen dates for existing entities
- Triggers Telegram notifications for new entities
- Overwrites the existing database with comprehensive update
- **Returns**: Tuple of (updated_db, new_count, total_count)

### `update_new_entities_file(truly_new_entities)`

Implements a dual-storage approach for tracking new entities:

1. Saves a timestamped snapshot to `data/new_entities_snapshot`
2. Updates the central tracking file `new_entities.json`

## Entity Tracking System

The parser maintains two parallel tracking systems:

1. **Site-specific database**: Complete record of all entities for each site (`lockbit_entities.json`, etc.)
2. **Central tracking database**: Record of all new entities across all sites (`new_entities.json`)

This dual approach enables both comprehensive site monitoring and focused tracking of new discoveries.

## Usage Pattern

The `BaseParser` is not used directly but serves as a parent class. The pattern is:

```python
class CustomParser(BaseParser):
    def parse_entities(self, html_content):
        # Implement site-specific parsing logic
        entities = []
        # Extract entities from HTML
        return entities

# Later usage:
parser = CustomParser(driver, site_config, output_dir, html_snapshots_dir)
html = parser.scrape_site()  # This calls the shared implementation
```

## Integration

`BaseParser` integrates with:
- The browser module for mirror connection
- File utilities for database management
- Telegram notification system (imported dynamically)
- Processing scripts (through the shared database files)

# `generic_parser.py` - Configuration-Driven Parser

## Overview

`generic_parser.py` provides the `GenericParser` class, a concrete implementation of `BaseParser` that uses JSON configuration to parse any ransomware site without requiring custom code. This configuration-driven approach enables adding new sites by simply creating configuration files rather than writing new parsers.

## Key Features

- **Configuration-driven**: Uses JSON configuration to define parsing rules
- **CSS selector based**: Extracts entities using CSS selectors
- **Field type system**: Supports text, attribute, conditional, and complex fields
- **Multiple formats**: Handles different countdown formats across sites
- **Regex extraction**: Extracts partial data from larger text/attributes
- **Special handling**: Custom logic for site-specific formats (RansomHub, LockBit)
- **Standardization**: Normalizes entity data to a consistent format

## Field Extraction System

The parser supports multiple field extraction methods:

### 1. Text Fields
Extracts text content from HTML elements matching a CSS selector.

### 2. Attribute Fields
Extracts attribute values from HTML elements matching a CSS selector.

### 3. Conditional Fields
Sets field values based on the presence/absence of elements.

### 4. Complex Fields
Extracts nested structures with multiple sub-fields.

## Special Format Handling

The parser includes specialized handling for different site formats:

1. **Standard countdown format** (LockBit style):
   - Extracts days, hours, minutes, seconds
   - Calculates estimated publication date

2. **Text-based countdown format** (RansomHub style):
   - Parses formats like "5D 21h 16m 8s" 
   - Extracts numeric values with regular expressions
   - Standardizes to the common countdown structure

3. **Date-based countdown format**:
   - Handles sites that provide exact countdown dates
   - Converts to the standard date format

## Configuration Example

A site configuration defines how to extract entities with selectors:

```json
{
  "site_key": "lockbit",
  "site_name": "LockBit",
  "parsing": {
    "entity_selector": "a.post-block",
    "fields": [
      {
        "name": "id",
        "type": "attribute",
        "selector": "self",
        "attribute": "href"
      },
      {
        "name": "domain",
        "type": "text",
        "selector": ".post-title"
      }
    ]
  }
}
```

## Usage Example

```python
# Load site configuration from JSON
site_config = load_json("lockbit.json", "config/sites")

# Create parser with configuration
parser = GenericParser(driver, site_config, output_dir, html_snapshots_dir)

# Parse the site - all parsing rules come from the configuration
html = parser.scrape_site()
```

## Extending for New Sites

To add support for a new ransomware site:

1. Create a new JSON configuration file
2. Define the entity selector to locate victim entries
3. Configure field extractors for each piece of data
4. Add special handling in GenericParser if the site uses unique formats

This approach allows the system to adapt to new sites without modifying the parser code.
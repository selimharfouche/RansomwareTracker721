#!/usr/bin/env python3
"""
Entity Processing and Archiving Script

This script:
1. Reads newly discovered entities from new_entities.json
2. Standardizes all entity fields with consistent formats
3. Archives them directly into final_entities.json (creating it if needed)
4. Resets the original new_entities.json file

The script uses online time sources for accurate UTC timestamps and 
ensures no duplicate entities are added to the final archive.
"""

import os
import json
import datetime
import re
import requests
import shutil
import traceback
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "output")
PER_GROUP_DIR = os.path.join(OUTPUT_DIR, "per_group")

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PER_GROUP_DIR, exist_ok=True)

# Define file paths - Both files in the main output directory
INPUT_FILE = os.path.join(OUTPUT_DIR, "new_entities.json")
FINAL_ENTITIES_FILE = os.path.join(OUTPUT_DIR, "final_entities.json")

# Define the fields we want to standardize across all entities
STANDARD_FIELDS = [
    "id", "domain", "status", "description_preview", "updated", "views",
    "countdown_remaining", "estimated_publish_date", "first_seen",
    "ransomware_group", "group_key", "country", "data_size", 
    "last_view", "visits", "class"
]

# Define date fields that need standardization
DATE_FIELDS = [
    "updated", "estimated_publish_date", "first_seen", "last_view"
]

# Define fields that should have specific data types
TYPE_MAPPING = {
    "views": int,
    "visits": int
}

# Month name mapping for parsing dates with month names
MONTH_NAMES = {
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
    'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
}

def get_current_utc_time():
    """
    Fetches the current UTC time from an online time API.
    Returns time in format: YYYY-MM-DD HH:MM:SS UTC
    
    Falls back to local system time if online fetch fails.
    """
    # List of time APIs to try (in order of preference)
    time_apis = [
        "http://worldtimeapi.org/api/timezone/Etc/UTC",
        "http://worldclockapi.com/api/json/utc/now"
    ]
    
    for api_url in time_apis:
        try:
            logger.debug(f"Fetching time from: {api_url}")
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle WorldTimeAPI response format
                if "datetime" in data:
                    # WorldTimeAPI format: 2023-03-09T10:00:00.000000+00:00
                    dt_str = data["datetime"]
                    # Convert to datetime object
                    dt = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                
                # Handle WorldClockAPI response format
                elif "currentDateTime" in data:
                    # WorldClockAPI format: 2023-03-09T10:00Z
                    dt_str = data["currentDateTime"]
                    # Convert to datetime object (removing the Z)
                    dt = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            
        except Exception as e:
            logger.warning(f"Failed to fetch time from {api_url}: {e}")
    
    # Fallback to system time if all APIs fail
    logger.warning("Failed to fetch time from online sources. Using system time.")
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

def load_json_file(file_path):
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

def save_json_file(data, file_path):
    """Save data to a JSON file."""
    try:
        # Create a backup of the existing file if it exists
        if os.path.exists(file_path):
            backup_file = f"{file_path}.bak"
            shutil.copy2(file_path, backup_file)
            logger.info(f"Created backup of existing file: {backup_file}")
        
        # Make sure parent directory exists (fix for issue)
        parent_dir = os.path.dirname(file_path)
        os.makedirs(parent_dir, exist_ok=True)
        logger.info(f"Ensuring directory exists: {parent_dir}")
        
        # Write the new data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved data to {file_path}")
        return True
    except Exception as e:
        # Detailed error information to help debug
        logger.error(f"Error saving to {file_path}: {e}")
        logger.error(f"File path: {file_path}")
        logger.error(f"Directory exists? {os.path.exists(os.path.dirname(file_path))}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def load_site_entities(site_key):
    """Load entity data for a specific site from the per_group directory."""
    json_file = f"{site_key}_entities.json"
    per_group_path = os.path.join(PER_GROUP_DIR, json_file)
    
    try:
        if os.path.exists(per_group_path):
            with open(per_group_path, 'r') as f:
                return json.load(f)
        else:
            # For backward compatibility, try looking in the main output directory
            old_path = os.path.join(OUTPUT_DIR, json_file)
            if os.path.exists(old_path):
                with open(old_path, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Found entity file in old location: {old_path}")
                    return data
            logger.warning(f"No entity file found for {site_key}")
    except Exception as e:
        logger.warning(f"Error loading site entities for {site_key}: {e}")
    
    # Return empty data if file not found or error occurred
    return {"entities": [], "last_updated": "", "total_count": 0}

def standardize_date(date_string):
    """
    Standardize date formats to YYYY-MM-DD HH:MM:SS UTC
    
    Handles various input formats:
    - DD MMM, YYYY, HH:MM UTC (LockBit format, e.g., "12 Aug, 2024, 11:05 UTC")
    - YYYY/MM/DD HH:MM:SS (Bashe format)
    - YYYY-MM-DD HH:MM:SS (without UTC)
    - YYYY-MM-DD HH:MM:SS UTC (already standard)
    """
    if not date_string:
        return None
    
    # Check if already in standard format
    if re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC', date_string):
        return date_string
    
    # Handle LockBit format with month names: "12 Aug, 2024, 11:05 UTC"
    lockbit_match = re.match(r'(\d{1,2}) ([A-Za-z]{3}), (\d{4}),\s+(\d{1,2}):(\d{2}) UTC', date_string)
    if lockbit_match:
        day, month, year, hour, minute = lockbit_match.groups()
        month_num = MONTH_NAMES.get(month, '01')  # Default to January if month not found
        # Pad single-digit day and hour with zeros
        day = day.zfill(2)
        hour = hour.zfill(2)
        return f"{year}-{month_num}-{day} {hour}:{minute}:00 UTC"
    
    # Handle Bashe format (YYYY/MM/DD HH:MM:SS)
    bashe_match = re.match(r'(\d{4})/(\d{2})/(\d{2}) (\d{2}:\d{2}:\d{2})', date_string)
    if bashe_match:
        year, month, day, time = bashe_match.groups()
        return f"{year}-{month}-{day} {time} UTC"
    
    # Handle format without UTC (YYYY-MM-DD HH:MM:SS)
    if re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', date_string):
        return f"{date_string} UTC"
    
    # For any other format, try to parse with datetime
    try:
        # Try common formats
        for fmt in [
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y/%m/%d %H:%M',
            '%d %b %Y %H:%M',
            '%d %B %Y %H:%M'
        ]:
            try:
                dt = datetime.datetime.strptime(date_string, fmt)
                return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except ValueError:
                continue
        
        # If we got here, none of the formats matched
        logger.warning(f"Could not standardize date format: {date_string}")
        return date_string
    except Exception as e:
        logger.warning(f"Error standardizing date: {date_string}, {str(e)}")
        return date_string

def standardize_entity(entity):
    """
    Standardize an entity by ensuring all required fields exist and 
    date fields are in consistent format.
    """
    standardized = {}
    
    # Copy all standard fields, setting missing ones to null
    for field in STANDARD_FIELDS:
        if field in entity:
            standardized[field] = entity[field]
        else:
            standardized[field] = None
    
    # Standardize date fields
    for date_field in DATE_FIELDS:
        if standardized[date_field]:
            standardized[date_field] = standardize_date(standardized[date_field])
    
    # For countdown_remaining, ensure it's a dictionary with standard fields if present
    if standardized["countdown_remaining"] is not None:
        if not isinstance(standardized["countdown_remaining"], dict):
            standardized["countdown_remaining"] = {"countdown_text": str(standardized["countdown_remaining"])}
        
        # Ensure standard countdown fields exist
        for subfield in ["countdown_text", "days", "hours", "minutes", "seconds"]:
            if subfield not in standardized["countdown_remaining"]:
                standardized["countdown_remaining"][subfield] = None
    
    # Convert fields to their expected types if possible
    for field, expected_type in TYPE_MAPPING.items():
        if standardized[field] is not None:
            try:
                standardized[field] = expected_type(standardized[field])
            except (ValueError, TypeError):
                # If conversion fails, keep the original value
                pass
    
    return standardized

def reset_input_file():
    """Reset the input file by emptying its entities array."""
    # Get current UTC time from online source
    current_time = get_current_utc_time()
    
    empty_db = {
        'entities': [],
        'last_updated': current_time,
        'total_count': 0
    }
    
    success = save_json_file(empty_db, INPUT_FILE)
    if success:
        logger.info(f"Successfully reset input file: {INPUT_FILE}")
    else:
        logger.error(f"Failed to reset input file: {INPUT_FILE}")
    
    return success

def process_and_archive_entities():
    """
    Process entities from new_entities.json, standardize them,
    and archive them directly into final_entities.json.
    """
    # Check if input file exists - if not, create an empty one
    if not os.path.exists(INPUT_FILE):
        logger.warning(f"Input file not found: {INPUT_FILE}")
        logger.info(f"Creating empty new_entities.json file")
        
        # Create empty structure
        current_time = get_current_utc_time()
        empty_db = {
            'entities': [],
            'last_updated': current_time,
            'total_count': 0
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(INPUT_FILE), exist_ok=True)
        
        # Save the empty file
        try:
            with open(INPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(empty_db, f, indent=2)
            logger.info(f"Successfully created empty file: {INPUT_FILE}")
        except Exception as e:
            logger.error(f"Failed to create input file: {e}")
            return False
    
    # Load input entities
    input_data = load_json_file(INPUT_FILE)
    if not input_data or "entities" not in input_data or not input_data["entities"]:
        logger.info(f"No entities found in {INPUT_FILE} to process")
        return True  # Return True because there's nothing to process (not an error)
    
    # Process and standardize all entities
    standardized_entities = []
    entity_count = 0
    
    logger.info(f"Processing {len(input_data['entities'])} entities from {INPUT_FILE}")
    
    for entity in input_data["entities"]:
        # Only process if we have a valid entity with at least an ID and domain
        if isinstance(entity, dict) and "id" in entity and "domain" in entity:
            standardized = standardize_entity(entity)
            standardized_entities.append(standardized)
            entity_count += 1
    
    if not standardized_entities:
        logger.warning("No valid entities to process")
        return False
    
    # Now add these standardized entities to the final archive
    current_time = get_current_utc_time()
    
    # Check if final archive exists
    if os.path.exists(FINAL_ENTITIES_FILE):
        # Load existing archive
        final_data = load_json_file(FINAL_ENTITIES_FILE)
        if not final_data or "entities" not in final_data:
            logger.error(f"Invalid format in final entities file: {FINAL_ENTITIES_FILE}")
            return False
        
        # Create a dictionary of existing entities for faster lookup
        existing_entities = {}
        for entity in final_data["entities"]:
            if "id" in entity and "domain" in entity:
                entity_key = f"{entity['id']}:{entity['domain']}"
                existing_entities[entity_key] = True
        
        # Add only new entities that don't already exist
        added_count = 0
        for entity in standardized_entities:
            if "id" in entity and "domain" in entity:
                entity_key = f"{entity['id']}:{entity['domain']}"
                if entity_key not in existing_entities:
                    final_data["entities"].append(entity)
                    existing_entities[entity_key] = True
                    added_count += 1
        
        # Update metadata
        final_data["total_count"] = len(final_data["entities"])
        final_data["last_updated"] = current_time
        
        logger.info(f"Added {added_count} new entities to the archive (skipped {entity_count - added_count} duplicates)")
    else:
        # Create new final entities file with standardized entities
        final_data = {
            "entities": standardized_entities,
            "last_updated": current_time,
            "total_count": len(standardized_entities),
            "description": "Complete archive of all discovered ransomware entities"
        }
        logger.info(f"Creating new final entities archive with {entity_count} entities")
    
    # Save the final archive file
    if save_json_file(final_data, FINAL_ENTITIES_FILE):
        # Reset the input file
        reset_input_file()
        return True
    else:
        logger.error(f"Failed to save final entities to {FINAL_ENTITIES_FILE}")
        return False

if __name__ == "__main__":
    logger.info("Starting entity processing and archiving")
    result = process_and_archive_entities()
    if result:
        logger.info("Entity processing and archiving completed successfully")
    else:
        logger.error("Entity processing and archiving failed")
#!/usr/bin/env python3
"""
New Entities Merger Script with online UTC time synchronization

This script:
1. Processes the central new_entities.json file from the output directory
2. Standardizes all entities and saves them to new_entities_merged.json
3. Resets the original new_entities.json file by emptying its entities array
4. Uses an online clock source to ensure accurate UTC timestamps
"""

import os
import json
import datetime
import re
import requests
from pathlib import Path
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
INPUT_DIR = os.path.join(PROJECT_ROOT, "data", "output")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define file paths
INPUT_FILE = os.path.join(INPUT_DIR, "new_entities.json")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "new_entities_merged.json")

# Define the fields we want to standardize across all entities
STANDARD_FIELDS = [
    "id",
    "domain",
    "status",
    "description_preview",
    "updated",
    "views",
    "countdown_remaining",
    "estimated_publish_date",
    "first_seen",
    "ransomware_group",
    "group_key",
    "country",
    "data_size",
    "last_view",
    "visits",
    "class"
]

# Define date fields that need standardization
DATE_FIELDS = [
    "updated",
    "estimated_publish_date", 
    "first_seen",
    "last_view"
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
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

def save_json_file(data, file_path):
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to {file_path}: {e}")
        return False

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

def reset_central_file():
    """Reset the central new_entities.json file by emptying its entities array."""
    # Get current UTC time from online source
    current_time = get_current_utc_time()
    
    empty_db = {
        'entities': [],
        'last_updated': current_time,
        'total_count': 0
    }
    
    return save_json_file(empty_db, INPUT_FILE)

def process_new_entities():
    """
    Process the central new_entities.json file, standardize all entities,
    save them to the output file, and reset the original file.
    """
    # Check if the input file exists
    if not os.path.exists(INPUT_FILE):
        logger.warning(f"Input file not found: {INPUT_FILE}")
        return False
    
    # Load the input file
    data = load_json_file(INPUT_FILE)
    
    if not data or "entities" not in data:
        logger.warning(f"No valid entities found in {INPUT_FILE}")
        return False
    
    # Check if there are entities to process
    if not data["entities"]:
        logger.info(f"No entities found in {INPUT_FILE}, nothing to process")
        return True
    
    # Process all entities
    standardized_entities = []
    entity_count = 0
    
    logger.info(f"Processing {len(data['entities'])} entities from {INPUT_FILE}")
    
    for entity in data["entities"]:
        # Only process if we have a valid entity with at least an ID and domain
        if isinstance(entity, dict) and "id" in entity and "domain" in entity:
            standardized = standardize_entity(entity)
            standardized_entities.append(standardized)
            entity_count += 1
    
    # Create the merged file
    if standardized_entities:
        # Get current UTC time from online source
        current_time = get_current_utc_time()
        
        merged_data = {
            "entities": standardized_entities,
            "last_updated": current_time,
            "total_count": entity_count
        }
        
        # Save to the output file
        if save_json_file(merged_data, OUTPUT_FILE):
            logger.info(f"Successfully processed {entity_count} entities")
            
            # Reset the central file
            if reset_central_file():
                logger.info(f"Successfully reset the central file {INPUT_FILE}")
            else:
                logger.error(f"Failed to reset the central file {INPUT_FILE}")
            
            return True
        else:
            logger.error(f"Failed to save to {OUTPUT_FILE}")
            return False
    else:
        logger.warning("No valid entities to process")
        return False

if __name__ == "__main__":
    logger.info("Starting new entities processing")
    process_new_entities()
    logger.info("New entities processing completed")
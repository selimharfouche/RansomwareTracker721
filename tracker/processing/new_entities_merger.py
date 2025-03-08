#!/usr/bin/env python3
"""
New Entities Merger Script

This script:
1. Processes the central new_entities.json file from the output directory
2. Standardizes all entities and saves them to new_entities_merged.json in the processed directory
3. Resets the original new_entities.json file by emptying its entities array

The script ensures all entities have a consistent format with standardized fields.
"""

import os
import json
import datetime
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

# Define fields that should have specific data types
TYPE_MAPPING = {
    "views": int,
    "visits": int
}

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

def standardize_entity(entity):
    """
    Standardize an entity by ensuring all required fields exist.
    Missing fields are set to null.
    """
    standardized = {}
    
    # Copy all standard fields, setting missing ones to null
    for field in STANDARD_FIELDS:
        if field in entity:
            standardized[field] = entity[field]
        else:
            standardized[field] = None
    
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
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
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
        merged_data = {
            "entities": standardized_entities,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
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
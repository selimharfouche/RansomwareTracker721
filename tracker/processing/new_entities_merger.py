#!/usr/bin/env python3
"""
New Entities Merger Script

This script specifically merges newly discovered entities from all ransomware groups
into a standardized format and saves the result as new_entities_merged.json in the
data/processed directory.
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

# The expected new entities file name
NEW_ENTITIES_FILE = "new_entities.json"
OUTPUT_FILE = "new_entities_merged.json"

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

def standardize_entity(entity, group_key=None, group_name=None):
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
    
    # Add group attribution if not present and provided
    if standardized["group_key"] is None and group_key:
        standardized["group_key"] = group_key
    
    if standardized["ransomware_group"] is None and group_name:
        standardized["ransomware_group"] = group_name
    
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

def process_new_entities():
    """
    Process the new_entities.json file and standardize all entities within it.
    """
    # Check if the new entities file exists
    new_entities_path = os.path.join(INPUT_DIR, NEW_ENTITIES_FILE)
    
    if not os.path.exists(new_entities_path):
        logger.warning(f"New entities file not found: {new_entities_path}")
        return False
    
    # Load the new entities file
    data = load_json_file(new_entities_path)
    
    if not data or "entities" not in data:
        logger.warning(f"No valid entities found in {NEW_ENTITIES_FILE}")
        return False
    
    # Process all entities in the file
    standardized_entities = []
    
    logger.info(f"Processing {len(data['entities'])} new entities")
    
    for entity in data["entities"]:
        # Only process if we have a valid entity with at least an ID and domain
        if isinstance(entity, dict) and "id" in entity and "domain" in entity:
            # The new_entities.json should already have group attribution,
            # but we'll extract it to use as a fallback if needed
            group_key = entity.get("group_key")
            group_name = entity.get("ransomware_group")
            
            standardized = standardize_entity(entity, group_key, group_name)
            standardized_entities.append(standardized)
    
    # Create the merged file
    if standardized_entities:
        merged_data = {
            "entities": standardized_entities,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_count": len(standardized_entities)
        }
        
        # Save to the output directory
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        save_json_file(merged_data, output_path)
        
        logger.info(f"Successfully processed {len(standardized_entities)} new entities")
        return True
    else:
        logger.warning("No valid entities found to process")
        return False

if __name__ == "__main__":
    logger.info("Starting new entities merging process")
    process_new_entities()
    logger.info("New entities merging process completed")
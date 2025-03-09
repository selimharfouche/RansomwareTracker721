#!/usr/bin/env python3
"""
Entity Archiver Script

This script:
1. Reads newly discovered entities from new_entities_merged.json
2. Archives them into a permanent final_entities.json file
3. Creates final_entities.json if it doesn't exist
4. Adds only entities that aren't already in the archive
5. Deletes the new_entities_merged.json file after successful processing

Usage: python archive_entities.py
"""

import os
import json
import logging
import datetime
from pathlib import Path
import shutil

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

# Define file paths
NEW_ENTITIES_FILE = os.path.join(PROCESSED_DIR, "new_entities_merged.json")
FINAL_ENTITIES_FILE = os.path.join(PROCESSED_DIR, "final_entities.json")

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
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write the new data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to {file_path}: {e}")
        return False

def archive_entities():
    """
    Archive new entities into the final entities file.
    
    This function reads new_entities_merged.json, adds its contents to final_entities.json
    (creating it if necessary), and then deletes the original new_entities_merged.json file.
    """
    # Check if new entities file exists
    if not os.path.exists(NEW_ENTITIES_FILE):
        logger.warning(f"New entities file not found: {NEW_ENTITIES_FILE}")
        return False
    
    # Load new entities
    new_data = load_json_file(NEW_ENTITIES_FILE)
    if not new_data or "entities" not in new_data or not new_data["entities"]:
        logger.warning("No new entities to archive")
        return False
    
    # Count of new entities
    new_entity_count = len(new_data["entities"])
    logger.info(f"Found {new_entity_count} new entities to archive")
    
    # Check if final entities file exists
    if os.path.exists(FINAL_ENTITIES_FILE):
        # Load existing archive
        final_data = load_json_file(FINAL_ENTITIES_FILE)
        if not final_data or "entities" not in final_data:
            logger.error(f"Invalid format in final entities file: {FINAL_ENTITIES_FILE}")
            return False
        
        # Create a dictionary of existing entities for faster lookup
        existing_entities = {}
        for entity in final_data["entities"]:
            # Use a combination of id and domain as a unique key
            if "id" in entity and "domain" in entity:
                entity_key = f"{entity['id']}:{entity['domain']}"
                existing_entities[entity_key] = True
        
        # Add only new entities that don't already exist
        added_count = 0
        for entity in new_data["entities"]:
            if "id" in entity and "domain" in entity:
                entity_key = f"{entity['id']}:{entity['domain']}"
                if entity_key not in existing_entities:
                    final_data["entities"].append(entity)
                    existing_entities[entity_key] = True
                    added_count += 1
        
        # Update metadata
        final_data["total_count"] = len(final_data["entities"])
        final_data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        logger.info(f"Added {added_count} new entities to the archive (skipped {new_entity_count - added_count} duplicates)")
    else:
        # Create new final entities file with new entities
        final_data = {
            "entities": new_data["entities"],
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_count": len(new_data["entities"]),
            "description": "Complete archive of all discovered ransomware entities"
        }
        logger.info(f"Creating new final entities archive with {new_entity_count} entities")
    
    # Save the updated final entities file
    if save_json_file(final_data, FINAL_ENTITIES_FILE):
        # Delete the new entities file after successful archiving
        try:
            os.remove(NEW_ENTITIES_FILE)
            logger.info(f"Successfully deleted {NEW_ENTITIES_FILE} after archiving")
        except Exception as e:
            logger.error(f"Error deleting {NEW_ENTITIES_FILE}: {e}")
        
        return True
    else:
        logger.error("Failed to save final entities file. New entities file was not deleted.")
        return False

if __name__ == "__main__":
    logger.info("Starting entity archiving process")
    result = archive_entities()
    if result:
        logger.info("Entity archiving completed successfully")
    else:
        logger.error("Entity archiving failed")
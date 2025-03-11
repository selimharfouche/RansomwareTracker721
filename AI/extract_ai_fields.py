#!/usr/bin/env python3
"""
Entity Field Extractor Script

This script extracts specific fields (id, domain, ransomware_group, group_key) 
from final_entities.json and creates a new AI.json file in the AI directory.
"""

import os
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Correct path calculation
SCRIPT_DIR = Path(__file__).parent.absolute()  # The AI directory
PROJECT_ROOT = SCRIPT_DIR.parent  # Go up one level to the project root
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "final_entities.json"
OUTPUT_FILE = SCRIPT_DIR / "AI.json"

def load_json_file(file_path):
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {file_path}")
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
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to {file_path}: {e}")
        return False

def extract_entity_fields():
    """
    Extract id, domain, ransomware_group, and group_key fields from final_entities.json
    and create a new AI.json file.
    """
    # Check if input file exists before attempting to load
    if not INPUT_FILE.exists():
        logger.error(f"Input file does not exist: {INPUT_FILE}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Project root: {PROJECT_ROOT}")
        return False
        
    # Load the input file
    data = load_json_file(INPUT_FILE)
    if not data or "entities" not in data:
        logger.error("No valid entities found in the input file")
        return False
    
    # Extract required fields
    extracted_entities = []
    for entity in data["entities"]:
        # Skip entities missing required fields
        if not all(field in entity for field in ["id", "domain"]):
            continue
        
        # Create a new entity with only the required fields
        extracted_entity = {
            "id": entity["id"],
            "domain": entity["domain"],
            "ransomware_group": entity.get("ransomware_group"),
            "group_key": entity.get("group_key")
        }
        extracted_entities.append(extracted_entity)
    
    # Create new JSON structure
    output_data = {
        "entities": extracted_entities,
        "total_count": len(extracted_entities),
        "last_updated": data.get("last_updated", ""),
        "description": "Extracted fields from ransomware entities for AI processing"
    }
    
    # Save to output file
    return save_json_file(output_data, OUTPUT_FILE)

if __name__ == "__main__":
    logger.info("Starting entity field extraction")
    logger.info(f"Looking for input file at: {INPUT_FILE}")
    success = extract_entity_fields()
    if success:
        logger.info(f"Successfully extracted fields to {OUTPUT_FILE}")
    else:
        logger.error("Failed to extract entity fields")
#!/usr/bin/env python3
"""
Entity Field Extractor Script

This script extracts specific fields (id, domain, ransomware_group, group_key) 
from final_entities.json and creates a new AI.json file in the specified output directory.
"""

import os
import json
import logging
import argparse
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description="Extract AI fields from entities")
parser.add_argument("--output", type=str, help="Output directory for AI.json")
args = parser.parse_args()

# Define paths using Path for cross-platform compatibility
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "final_entities.json"

# Determine output directory
if args.output:
    OUTPUT_DIR = Path(args.output)
else:
    # Default to script directory if no output specified
    OUTPUT_DIR = Path(__file__).parent

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "AI.json"

def load_json_file(file_path):
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {file_path}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Project root: {PROJECT_ROOT}")
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
    logger.info(f"Looking for input file at: {INPUT_FILE}")
    if not INPUT_FILE.exists():
        logger.error(f"Input file does not exist: {INPUT_FILE}")
        
        # Create a placeholder file if input doesn't exist
        placeholder_data = {
            "entities": [],
            "total_count": 0,
            "last_updated": "",
            "description": "Placeholder AI.json file (input file not found)"
        }
        save_json_file(placeholder_data, OUTPUT_FILE)
        logger.info(f"Created placeholder AI.json at {OUTPUT_FILE}")
        return False
        
    # Load the input file
    data = load_json_file(INPUT_FILE)
    if not data or "entities" not in data:
        logger.error("No valid entities found in the input file")
        
        # Create a placeholder file if input is invalid
        placeholder_data = {
            "entities": [],
            "total_count": 0,
            "last_updated": "",
            "description": "Placeholder AI.json file (no valid entities in input)"
        }
        save_json_file(placeholder_data, OUTPUT_FILE)
        logger.info(f"Created placeholder AI.json at {OUTPUT_FILE}")
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
    success = extract_entity_fields()
    if success:
        logger.info(f"Successfully extracted fields to {OUTPUT_FILE}")
    else:
        logger.error("Failed to extract entity fields")
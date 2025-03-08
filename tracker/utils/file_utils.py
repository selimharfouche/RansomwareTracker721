# utils/file_utils.py
import json
import os
import logging

# Create a logger for this module
logger = logging.getLogger(__name__)

def load_json(filename, output_dir):
    """Load JSON data from a file"""
    filepath = os.path.join(output_dir, filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info(f"File not found: {filepath}. Returning empty dictionary.")
        return {}
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in file: {filepath}. Returning empty dictionary.")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading JSON file {filepath}: {e}")
        return {}

def save_json(data, filename, output_dir):
    """Save JSON data to a file"""
    filepath = os.path.join(output_dir, filename)
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        logger.debug(f"Successfully saved data to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {filepath}: {e}")
        return False
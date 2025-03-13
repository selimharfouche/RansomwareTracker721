# utils/file_utils.py
import json
import os
import logging

# Create a logger for this module
logger = logging.getLogger(__name__)

def load_json(filename, output_dir):
    """
    Load JSON data from a file, checking both the specified directory and the parent directory
    for backward compatibility.
    """
    filepath = os.path.join(output_dir, filename)
    
    # First try the specified path
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # If file not found, check if output_dir ends with "per_group"
        if os.path.basename(output_dir) == "per_group":
            # Try the parent directory for backward compatibility
            parent_dir = os.path.dirname(output_dir)
            parent_filepath = os.path.join(parent_dir, filename)
            try:
                with open(parent_filepath, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Found file in parent directory: {parent_filepath}")
                    # Save to the new location for future use
                    save_json(data, filename, output_dir)
                    return data
            except FileNotFoundError:
                logger.info(f"File not found in either location: {filename}")
                return {}
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in file: {parent_filepath}")
                return {}
        # Return empty dict if file doesn't exist
        logger.info(f"File not found: {filepath}")
        return {}
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in file: {filepath}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading JSON file {filepath}: {e}")
        return {}

def save_json(data, filename, output_dir):
    """Save JSON data to a file."""
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
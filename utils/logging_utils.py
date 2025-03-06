# utils/logging_utils.py
import logging

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

# Create logger
logger = setup_logging()

# utils/file_utils.py
import json
import os
from config.settings import OUTPUT_DIR

def load_json(filename):
    """Load JSON data from a file"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return empty dict if file doesn't exist or is invalid
        return {}

def save_json(data, filename):
    """Save JSON data to a file"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
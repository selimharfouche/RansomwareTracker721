# utils/file_utils.py
import json
import os

def load_json(filename, output_dir):
    """Load JSON data from a file"""
    filepath = os.path.join(output_dir, filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return empty dict if file doesn't exist or is invalid
        return {}

def save_json(data, filename, output_dir):
    """Save JSON data to a file"""
    filepath = os.path.join(output_dir, filename)
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving JSON: {e}")
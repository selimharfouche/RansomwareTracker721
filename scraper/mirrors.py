# scraper/mirrors.py
import datetime
from config.settings import LOCKBIT_MIRRORS
from utils.logging_utils import logger
from utils.file_utils import load_json, save_json

def get_working_mirrors():
    """Load previously working mirrors if available"""
    mirrors_data = load_json("working_mirrors.json")
    
    if mirrors_data:
        # Sort mirrors by success rate
        working_mirrors = sorted(
            mirrors_data.items(), 
            key=lambda x: x[1]['success_rate'], 
            reverse=True
        )
        return [mirror for mirror, _ in working_mirrors]
    else:
        # If no data is available, return the default list
        return LOCKBIT_MIRRORS

def update_mirror_stats(mirror, success=True):
    """Update statistics about mirror reliability"""
    mirrors_data = load_json("working_mirrors.json")
    
    if not mirrors_data:
        mirrors_data = {m: {"success": 0, "failure": 0, "success_rate": 0.0} for m in LOCKBIT_MIRRORS}
    
    # Ensure the mirror is in our data
    if mirror not in mirrors_data:
        mirrors_data[mirror] = {"success": 0, "failure": 0, "success_rate": 0.0}
    
    # Update stats
    if success:
        mirrors_data[mirror]["success"] += 1
    else:
        mirrors_data[mirror]["failure"] += 1
    
    # Calculate success rate
    total = mirrors_data[mirror]["success"] + mirrors_data[mirror]["failure"]
    if total > 0:
        mirrors_data[mirror]["success_rate"] = mirrors_data[mirror]["success"] / total
    
    # Add timestamp
    mirrors_data[mirror]["last_check"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Save updated data
    save_json(mirrors_data, "working_mirrors.json")

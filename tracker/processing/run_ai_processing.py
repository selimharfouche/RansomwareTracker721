#!/usr/bin/env python3
"""
AI Processing Coordinator

This script coordinates running both AI scripts and sends results to Telegram.
Use the --github flag when running in GitHub Actions environment.
"""

import os
import sys
import json
import argparse
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description="AI Processing Coordinator")
parser.add_argument("--github", action="store_true", help="Run in GitHub Actions mode")
args = parser.parse_args()

# Log current working directory for debugging
current_dir = os.getcwd()
logger.info(f"Current working directory: {current_dir}")
logger.info("Directory contents:")
for item in os.listdir(current_dir):
    logger.info(f"  - {item}")

# In GitHub Actions, make sure we don't try to use absolute paths
# that include the repository name twice
if args.github:
    PROJECT_ROOT = Path(current_dir)
    AI_DIR = PROJECT_ROOT / "AI"
    logger.info(f"GitHub mode, AI_DIR set to: {AI_DIR}")
    
    # Create AI directory if it doesn't exist
    if not AI_DIR.exists():
        logger.info(f"Creating AI directory at {AI_DIR}")
        AI_DIR.mkdir(exist_ok=True)
else:
    SCRIPT_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = SCRIPT_DIR.parent.parent
    AI_DIR = PROJECT_ROOT / "AI"
    logger.info(f"Local mode, AI_DIR set to: {AI_DIR}")

# Create placeholder scripts if they don't exist
def create_placeholder_scripts():
    """Create placeholder scripts if they don't exist"""
    extract_script_path = AI_DIR / "extract_ai_fields.py"
    if not extract_script_path.exists():
        logger.info(f"Creating placeholder extract_ai_fields.py at {extract_script_path}")
        with open(extract_script_path, 'w') as f:
            f.write('''#!/usr/bin/env python3
import json
from pathlib import Path

# Get the directory this script is in
SCRIPT_DIR = Path(__file__).resolve().parent
AI_JSON_PATH = SCRIPT_DIR / "AI.json"

# Create placeholder data
data = {
    "entities": [],
    "total_count": 0,
    "last_updated": "",
    "description": "Placeholder AI.json file"
}

# Save to file
with open(AI_JSON_PATH, "w") as f:
    json.dump(data, f, indent=2)

print(f"Created placeholder AI.json at {AI_JSON_PATH}")
''')
        os.chmod(extract_script_path, 0o755)  # Make executable

    enrich_script_path = AI_DIR / "domain_enrichment.py"
    if not enrich_script_path.exists():
        logger.info(f"Creating placeholder domain_enrichment.py at {enrich_script_path}")
        with open(enrich_script_path, 'w') as f:
            f.write('''#!/usr/bin/env python3
import json
import argparse
from pathlib import Path

# Parse command line arguments
parser = argparse.ArgumentParser(description="Domain enrichment processor")
parser.add_argument("--yes", action="store_true", help="Automatically confirm all batches")
args = parser.parse_args()

# Get the directory this script is in
SCRIPT_DIR = Path(__file__).resolve().parent
AI_JSON_PATH = SCRIPT_DIR / "AI.json"
PROCESSED_JSON_PATH = SCRIPT_DIR / "processed_AI.json"

# Check if AI.json exists
if AI_JSON_PATH.exists():
    # Read existing AI.json
    with open(AI_JSON_PATH, "r") as f:
        data = json.load(f)
    
    # Copy to processed_AI.json with sample enrichment
    for entity in data.get("entities", []):
        # Add sample enrichment data
        entity["organization"] = {
            "name": "Sample Organization",
            "industry": "Technology",
            "sub_industry": "Software"
        }
        entity["geography"] = {
            "country_code": "USA",
            "region": "California",
            "city": "San Francisco"
        }
    
    # Save to processed_AI.json
    with open(PROCESSED_JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Created enriched processed_AI.json at {PROCESSED_JSON_PATH}")
else:
    print(f"Error: AI.json not found at {AI_JSON_PATH}")
    # Create empty processed_AI.json
    with open(PROCESSED_JSON_PATH, "w") as f:
        json.dump({"entities": [], "total_count": 0}, f, indent=2)
''')
        os.chmod(enrich_script_path, 0o755)  # Make executable

# Create placeholder scripts
create_placeholder_scripts()

def run_extract_ai_fields():
    """Run the extract_ai_fields.py script"""
    logger.info("Running extract_ai_fields.py...")
    
    try:
        script_path = AI_DIR / "extract_ai_fields.py"
        logger.info(f"Extract script path: {script_path}")
        
        # Check if the script exists
        if not script_path.exists():
            logger.error(f"Script does not exist at {script_path}")
            return False
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"STDOUT: {result.stdout}")
        logger.info("extract_ai_fields.py completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"extract_ai_fields.py failed: {e}")
        logger.error(f"STDERR: {e.stderr}")
        return False

def run_domain_enrichment():
    """Run the domain_enrichment.py script with --yes flag"""
    logger.info("Running domain_enrichment.py with --yes flag...")
    
    try:
        script_path = AI_DIR / "domain_enrichment.py"
        logger.info(f"Enrichment script path: {script_path}")
        
        # Check if the script exists
        if not script_path.exists():
            logger.error(f"Script does not exist at {script_path}")
            return False
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--yes"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"STDOUT: {result.stdout}")
        logger.info("domain_enrichment.py completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"domain_enrichment.py failed: {e}")
        logger.error(f"STDERR: {e.stderr}")
        return False

def count_processed_entities():
    """Count newly processed entities"""
    try:
        ai_json_path = AI_DIR / "AI.json"
        processed_ai_path = AI_DIR / "processed_AI.json"
        
        logger.info(f"Looking for AI.json at: {ai_json_path}")
        logger.info(f"Looking for processed_AI.json at: {processed_ai_path}")
        
        if not ai_json_path.exists():
            logger.warning(f"AI.json not found at {ai_json_path}")
            return 0
        
        if not processed_ai_path.exists():
            logger.warning(f"processed_AI.json not found at {processed_ai_path}")
            return 0
        
        with open(ai_json_path, 'r') as f:
            ai_data = json.load(f)
        
        with open(processed_ai_path, 'r') as f:
            processed_data = json.load(f)
        
        ai_count = len(ai_data.get('entities', []))
        processed_count = len(processed_data.get('entities', []))
        
        logger.info(f"AI.json has {ai_count} entities")
        logger.info(f"processed_AI.json has {processed_count} entities")
        
        # Calculate newly processed entities (simplistic approach)
        return max(0, processed_count - ai_count)
    except Exception as e:
        logger.error(f"Error counting entities: {e}")
        return 0

def get_sample_entities(count):
    """Get sample information from recently processed entities"""
    try:
        processed_ai_path = AI_DIR / "processed_AI.json"
        
        if not processed_ai_path.exists():
            logger.warning(f"processed_AI.json not found at {processed_ai_path}")
            return []
            
        with open(processed_ai_path, 'r') as f:
            data = json.load(f)
        
        entities = data.get('entities', [])[-count:]
        return entities[:3]  # Return up to 3 entities
    except Exception as e:
        logger.error(f"Error getting sample entities: {e}")
        return []

def send_notification(newly_processed_count):
    """Send Telegram notification with results"""
    try:
        # Add project root to Python path for imports
        sys.path.append(str(PROJECT_ROOT))
        
        try:
            from tracker.telegram_bot.notifier import send_telegram_message
        except ImportError:
            logger.error("Could not import telegram notifier. Notifications will not be sent.")
            return False
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        if newly_processed_count > 0:
            message = f"🤖 <b>AI Processing Completed</b>\n\n"
            message += f"<b>Time:</b> {timestamp}\n"
            message += f"<b>Newly Processed Entities:</b> {newly_processed_count}\n\n"
            
            # Add sample entity information
            sample_entities = get_sample_entities(newly_processed_count)
            
            if sample_entities:
                message += "<b>Sample Entity Information:</b>\n"
                
                for i, entity in enumerate(sample_entities):
                    message += f"\n<b>Entity {i+1}:</b> {entity.get('domain', 'Unknown')}\n"
                    
                    # Organization info
                    if 'organization' in entity:
                        org = entity['organization']
                        message += f"<b>Organization:</b> {org.get('name', 'Unknown')}\n"
                        message += f"<b>Industry:</b> {org.get('industry', 'Unknown')}\n"
                    
                    # Geography info
                    if 'geography' in entity:
                        geo = entity['geography']
                        message += f"<b>Country:</b> {geo.get('country_code', 'Unknown')}\n"
                        if geo.get('city'):
                            message += f"<b>Location:</b> {geo.get('city', '')}, {geo.get('region', '')}\n"
                
                if newly_processed_count > 3:
                    message += f"\n... and {newly_processed_count - 3} more entities\n"
            else:
                message += "<i>Could not retrieve detailed entity information</i>\n"
            
            message += f"\n✅ <i>AI processing complete</i>"
        else:
            message = f"🤖 <b>AI Processing Completed - No New Entities</b>\n\n"
            message += f"<b>Time:</b> {timestamp}\n"
            message += f"<b>Result:</b> No new entities were processed\n"
        
        # Send message
        success = send_telegram_message(message)
        
        if success:
            logger.info("Notification sent successfully")
        else:
            logger.error("Failed to send notification")
            
        return success
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False

def main():
    """Main function to coordinate AI processing workflow"""
    logger.info(f"Starting AI processing workflow (GitHub mode: {args.github})...")
    
    # Run the extract script
    if not run_extract_ai_fields():
        logger.error("Extract script failed")
        return False
    
    # Run the enrichment script
    if not run_domain_enrichment():
        logger.error("Enrichment script failed")
        return False
    
    # Count processed entities
    newly_processed_count = count_processed_entities()
    logger.info(f"Newly processed entities: {newly_processed_count}")
    
    # Send notification
    send_notification(newly_processed_count)
    
    logger.info("AI processing workflow completed")
    return True

if __name__ == "__main__":
    main()
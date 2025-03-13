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

# Define paths based on environment
if args.github:
    # GitHub Actions paths
    PROJECT_ROOT = Path(os.getcwd())
    AI_DIR = PROJECT_ROOT / "AI"
    DATA_DIR = PROJECT_ROOT / "data" / "processed"
else:
    # Local development paths
    SCRIPT_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = SCRIPT_DIR.parent.parent
    AI_DIR = PROJECT_ROOT / "AI"
    DATA_DIR = PROJECT_ROOT / "data" / "processed"

def run_extract_ai_fields():
    """Run the extract_ai_fields.py script"""
    logger.info("Running extract_ai_fields.py...")
    
    try:
        script_path = AI_DIR / "extract_ai_fields.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=True,
            text=True
        )
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
        result = subprocess.run(
            [sys.executable, str(script_path), "--yes"],
            check=True,
            capture_output=True,
            text=True
        )
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
        
        if not ai_json_path.exists() or not processed_ai_path.exists():
            logger.warning("Required JSON files not found")
            return 0
        
        with open(ai_json_path, 'r') as f:
            ai_data = json.load(f)
        
        with open(processed_ai_path, 'r') as f:
            processed_data = json.load(f)
        
        ai_count = len(ai_data.get('entities', []))
        processed_count = len(processed_data.get('entities', []))
        
        logger.info(f"AI.json has {ai_count} entities")
        logger.info(f"processed_AI.json has {processed_count} entities")
        
        # Calculate newly processed entities
        ai_ids = {entity.get('id') for entity in ai_data.get('entities', [])}
        processed_ids = {entity.get('id') for entity in processed_data.get('entities', [])}
        newly_processed = processed_ids - ai_ids
        
        return len(newly_processed)
    except Exception as e:
        logger.error(f"Error counting entities: {e}")
        return 0

def get_sample_entities(count):
    """Get sample information from recently processed entities"""
    try:
        processed_ai_path = AI_DIR / "processed_AI.json"
        
        if not processed_ai_path.exists():
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
        from tracker.telegram_bot.notifier import send_telegram_message
        
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
        send_telegram_message(message)
        logger.info("Notification sent successfully")
        return True
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
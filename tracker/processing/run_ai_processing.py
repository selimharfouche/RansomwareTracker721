#!/usr/bin/env python3
"""
AI Processing Coordinator

This script:
1. Runs the extract_ai_fields.py script to create AI.json from final_entities.json
2. Runs domain_enrichment.py with --yes flag to automatically process all domains
3. Compares files to determine how many new entities were processed
4. Sends a Telegram notification with the results
"""

import os
import sys
import json
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

# Define the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
AI_DIR = PROJECT_ROOT / "AI"

def run_extract_ai_fields():
    """Run the extract_ai_fields.py script to create AI.json."""
    logger.info("Running extract_ai_fields.py...")
    
    try:
        script_path = AI_DIR / "extract_ai_fields.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"extract_ai_fields.py completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"extract_ai_fields.py failed with error: {e}")
        logger.error(f"STDERR: {e.stderr}")
        return False

def run_domain_enrichment():
    """Run the domain_enrichment.py script with --yes flag."""
    logger.info("Running domain_enrichment.py with --yes flag...")
    
    try:
        script_path = AI_DIR / "domain_enrichment.py"
        result = subprocess.run(
            [sys.executable, str(script_path), "--yes"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"domain_enrichment.py completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"domain_enrichment.py failed with error: {e}")
        logger.error(f"STDERR: {e.stderr}")
        return False

def count_processed_entities():
    """Count how many entities were newly processed by comparing files."""
    try:
        ai_json_path = AI_DIR / "AI.json"
        processed_ai_path = AI_DIR / "processed_AI.json"
        
        # Check if both files exist
        if not ai_json_path.exists() or not processed_ai_path.exists():
            logger.warning("One or both of the required JSON files do not exist")
            return 0
        
        # Load the files
        with open(ai_json_path, 'r') as f:
            ai_data = json.load(f)
        
        with open(processed_ai_path, 'r') as f:
            processed_data = json.load(f)
        
        # Get counts
        ai_count = len(ai_data.get('entities', []))
        processed_count = len(processed_data.get('entities', []))
        
        logger.info(f"AI.json has {ai_count} entities")
        logger.info(f"processed_AI.json has {processed_count} entities")
        
        # Get ID sets for comparison
        ai_ids = {entity.get('id') for entity in ai_data.get('entities', [])}
        processed_ids = {entity.get('id') for entity in processed_data.get('entities', [])}
        
        # Find newly processed entities (those in processed_AI.json but not in previous run)
        newly_processed = processed_ids - ai_ids
        
        return len(newly_processed)
    except Exception as e:
        logger.error(f"Error counting processed entities: {e}")
        return 0

def get_sample_entities(newly_processed_count):
    """Get sample information from recently processed entities."""
    try:
        processed_ai_path = AI_DIR / "processed_AI.json"
        with open(processed_ai_path, 'r') as f:
            processed_data = json.load(f)
        
        # Get the most recent entities (assuming they're the newly processed ones)
        entities = processed_data.get('entities', [])[-newly_processed_count:]
        
        # Return up to 3 entities for the report
        return entities[:3]
    except Exception as e:
        logger.error(f"Error retrieving sample entities: {e}")
        return []

def send_telegram_notification(newly_processed_count):
    """Send a Telegram notification with the results of the AI processing."""
    try:
        # Import the Telegram notifier
        sys.path.append(str(PROJECT_ROOT))
        from tracker.telegram_bot.notifier import send_telegram_message
        
        # Format the message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        if newly_processed_count > 0:
            message = f"🤖 <b>AI Processing Completed</b>\n\n"
            message += f"<b>Time:</b> {timestamp}\n"
            message += f"<b>Newly Processed Entities:</b> {newly_processed_count}\n\n"
            
            # Add example information from processed entities
            sample_entities = get_sample_entities(newly_processed_count)
            
            if sample_entities:
                message += "<b>Sample Entity Information:</b>\n"
                
                for i, entity in enumerate(sample_entities):
                    message += f"\n<b>Entity {i+1}:</b> {entity.get('domain', 'Unknown')}\n"
                    
                    # Add organization information if available
                    if 'organization' in entity:
                        org = entity['organization']
                        message += f"<b>Organization:</b> {org.get('name', 'Unknown')}\n"
                        message += f"<b>Industry:</b> {org.get('industry', 'Unknown')}\n"
                    
                    # Add geography information if available
                    if 'geography' in entity:
                        geo = entity['geography']
                        message += f"<b>Country:</b> {geo.get('country_code', 'Unknown')}\n"
                        if geo.get('city'):
                            message += f"<b>Location:</b> {geo.get('city', '')}, {geo.get('region', '')}\n"
                
                # If there are more entities than we showed
                if newly_processed_count > 3:
                    message += f"\n... and {newly_processed_count - 3} more entities\n"
            else:
                message += "<i>Could not retrieve detailed entity information</i>\n"
            
            message += f"\n✅ <i>AI processing complete - entities enriched with organizational data</i>"
        else:
            message = f"🤖 <b>AI Processing Completed - No New Entities</b>\n\n"
            message += f"<b>Time:</b> {timestamp}\n"
            message += f"<b>Result:</b> No new entities were processed by the AI\n\n"
            message += f"<i>All previously discovered entities have already been processed</i>"
        
        # Send the message
        success = send_telegram_message(message)
        
        if success:
            logger.info("AI processing notification sent successfully")
        else:
            logger.error("Failed to send AI processing notification")
        
        return success
    except ImportError as e:
        logger.error(f"Failed to import telegram notifier module: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending telegram notification: {e}")
        return False

def main():
    """Main function to coordinate the AI processing workflow."""
    logger.info("Starting AI processing workflow...")
    
    # Step 1: Run extract_ai_fields.py
    if not run_extract_ai_fields():
        logger.error("Failed to extract AI fields. Stopping workflow.")
        return False
    
    # Step 2: Run domain_enrichment.py
    if not run_domain_enrichment():
        logger.error("Domain enrichment failed. Stopping workflow.")
        return False
    
    # Step 3: Count how many entities were newly processed
    newly_processed_count = count_processed_entities()
    logger.info(f"Newly processed entities: {newly_processed_count}")
    
    # Step 4: Send a Telegram notification with the results
    if not send_telegram_notification(newly_processed_count):
        logger.warning("Failed to send Telegram notification, but AI processing completed")
    
    logger.info("AI processing workflow completed successfully")
    return True

if __name__ == "__main__":
    main()
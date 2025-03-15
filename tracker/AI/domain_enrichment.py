#!/usr/bin/env python3
"""
Domain Enrichment Processor

This script extracts domains from AI.json that haven't been processed yet,
sends them to OpenAI API for enrichment, and saves the results to processed_AI.json.
"""

import json
import os
import time
import logging
import argparse
import traceback
import sys
from pathlib import Path
from typing import List, Dict, Any
import requests
from datetime import datetime

# Configure very detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Force output to stdout for GitHub Actions
    ]
)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description="Domain enrichment processor")
parser.add_argument("--yes", action="store_true", help="Automatically confirm all batches")
parser.add_argument("--output", type=str, help="Output directory for processed_AI.json")
args = parser.parse_args()

# Determine output directory
if args.output:
    OUTPUT_DIR = Path(args.output)
else:
    # Default to script directory if no output specified
    OUTPUT_DIR = Path(__file__).parent

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Define file paths relative to the output directory
INPUT_FILE = OUTPUT_DIR / "AI.json"
PROCESSED_FILE = OUTPUT_DIR / "processed_AI.json"
LOG_FILE = OUTPUT_DIR / "domain_enrichment.log"

# Set up file logging
file_handler = logging.FileHandler(LOG_FILE, mode='w')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logger.info("====== DOMAIN ENRICHMENT STARTING ======")
logger.info(f"Input file: {INPUT_FILE}")
logger.info(f"Output file: {PROCESSED_FILE}")
logger.info(f"Log file: {LOG_FILE}")

# Check for GitHub Actions environment
IN_GITHUB_ACTIONS = os.environ.get('GITHUB_ACTIONS') == 'true'
logger.info(f"Running in GitHub Actions: {IN_GITHUB_ACTIONS}")

# Load environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY:
    logger.info(f"OPENAI_API_KEY found (length: {len(OPENAI_API_KEY)})")
else:
    logger.error("OPENAI_API_KEY not found in environment variables")
    sys.exit(1)

def load_json_file(file_path: Path) -> Dict:
    """Load a JSON file and return its contents."""
    logger.info(f"Loading file: {file_path}")
    
    try:
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return {"entities": []}
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            count = len(data.get('entities', []))
            logger.info(f"Loaded {count} entities from {file_path}")
            return data
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        logger.error(traceback.format_exc())
        return {"entities": []}

def save_json_file(data: Dict, file_path: Path) -> bool:
    """Save data to a JSON file."""
    logger.info(f"Saving to file: {file_path}")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved {len(data.get('entities', []))} entities to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to {file_path}: {e}")
        logger.error(traceback.format_exc())
        return False

def get_unprocessed_domains(input_data, processed_data):
    """Get domains from input_data that are not in processed_data."""
    logger.info("Identifying unprocessed domains...")
    
    input_entities = input_data.get('entities', [])
    processed_entities = processed_data.get('entities', [])
    
    # Create lookup sets for quick comparison
    processed_ids = {(e.get('id'), e.get('group_key')) for e in processed_entities if e.get('id') and e.get('group_key')}
    processed_domains = {e.get('domain') for e in processed_entities if e.get('domain')}
    
    unprocessed = []
    for entity in input_entities:
        entity_id = entity.get('id')
        group_key = entity.get('group_key')
        domain = entity.get('domain')
        
        if not domain:
            continue
            
        # Check if entity is unprocessed
        if (entity_id and group_key and (entity_id, group_key) not in processed_ids) or (domain not in processed_domains):
            unprocessed.append(entity)
            logger.info(f"Unprocessed entity found: {domain} (id:{entity_id}, group:{group_key})")
    
    logger.info(f"Found {len(unprocessed)} unprocessed entities out of {len(input_entities)} total")
    
    # Print exact domains to be processed
    if unprocessed:
        domains_to_process = [e.get('domain') for e in unprocessed if e.get('domain')]
        logger.info(f"Domains to be processed: {', '.join(domains_to_process)}")
    
    return unprocessed

def enrich_domains(domains: List[str]) -> List[Dict]:
    """Send domains to OpenAI API for enrichment."""
    if not domains:
        logger.info("No domains to enrich")
        return []
    
    logger.info(f"⭐⭐⭐ ENRICHING {len(domains)} DOMAINS WITH OPENAI API ⭐⭐⭐")
    for i, domain in enumerate(domains):
        logger.info(f"Domain {i+1}: {domain}")
    
    try:
        # Prepare the prompt
        prompt = f"""Please provide detailed organizational information for these domains:
        
{', '.join(domains)}

For each domain, provide:
1. Geography (country_code, region, city)
2. Organization details (name, industry, sub_industry)
3. Size information (employees_range, revenue_range)
4. Organization status

Return a valid JSON array with an object for each domain."""
        
        logger.info("Sending request to OpenAI API...")
        logger.info(f"Request prompt: {prompt[:200]}...")
        
        # Make API call to OpenAI
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        data = {
            "model": "o3-mini",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that provides information about organizations based on domain names."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        }
        
        logger.info("⏱️ Making API request - this might take a minute...")
        start_time = time.time()
        
        # Set a long timeout (60 seconds)
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        end_time = time.time()
        logger.info(f"API request completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code}, {response.text}")
            return []
        
        # Extract content
        response_data = response.json()
        logger.info(f"Received response: {response_data.keys()}")
        
        content = response_data['choices'][0]['message']['content']
        logger.info(f"Content length: {len(content)} characters")
        logger.info(f"First 200 characters: {content[:200]}...")
        
        # Try to extract JSON from the response
        try:
            # Try to parse as JSON directly
            enriched_data = json.loads(content)
            if isinstance(enriched_data, list):
                logger.info(f"Successfully parsed {len(enriched_data)} entities")
                return enriched_data
            else:
                logger.warning(f"Response is not a list: {type(enriched_data)}")
                return []
        except json.JSONDecodeError:
            # Try to extract JSON from text response
            import re
            match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
            if match:
                try:
                    json_str = match.group(0)
                    enriched_data = json.loads(json_str)
                    logger.info(f"Extracted JSON with {len(enriched_data)} entities")
                    return enriched_data
                except json.JSONDecodeError:
                    logger.error("Failed to parse extracted JSON")
                    return []
            else:
                logger.error("Could not find JSON array in response")
                return []
                
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        logger.error(traceback.format_exc())
        return []

def process_domains():
    """Process domains from AI.json and update processed_AI.json."""
    # Load input and processed data
    input_data = load_json_file(INPUT_FILE)
    processed_data = load_json_file(PROCESSED_FILE)
    if not processed_data:
        processed_data = {"entities": [], "total_count": 0, "last_updated": ""}
    
    # Find unprocessed domains
    unprocessed_entities = get_unprocessed_domains(input_data, processed_data)
    
    if not unprocessed_entities:
        logger.info("No unprocessed entities found. Nothing to do.")
        return True
    
    # Extract domains from unprocessed entities
    domains_to_process = [entity.get('domain') for entity in unprocessed_entities if entity.get('domain')]
    
    # Enrich domains
    enriched_data = enrich_domains(domains_to_process)
    
    if not enriched_data:
        logger.error("Failed to get enriched data from OpenAI API")
        return False
    
    # Map enriched data back to original entities
    enriched_by_domain = {entity.get('domain'): entity for entity in enriched_data if entity.get('domain')}
    logger.info(f"Mapped {len(enriched_by_domain)} enriched domains")
    
    # Add enrichment data to entities
    newly_processed = []
    for entity in unprocessed_entities:
        domain = entity.get('domain')
        
        if domain and domain in enriched_by_domain:
            # Combine original entity data with enriched data
            enriched_entity = enriched_by_domain[domain]
            enriched_entity['id'] = entity.get('id')
            enriched_entity['group_key'] = entity.get('group_key')
            enriched_entity['ransomware_group'] = entity.get('ransomware_group')
            
            newly_processed.append(enriched_entity)
            logger.info(f"Enriched entity: {domain}")
    
    # Add newly processed entities to processed data
    if newly_processed:
        processed_data['entities'].extend(newly_processed)
        processed_data['total_count'] = len(processed_data['entities'])
        processed_data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Save updated processed data
        save_json_file(processed_data, PROCESSED_FILE)
        logger.info(f"Added {len(newly_processed)} newly processed entities")
        
        # Send notification about processed entities
        send_telegram_notification(newly_processed)
    
    return True

def send_telegram_notification(newly_processed_entities):
    """Send a Telegram notification with details about newly processed entities."""
    if not newly_processed_entities:
        logger.info("No entities to notify about")
        return False
    
    try:
        # Add project root to Python path for imports
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        import sys
        sys.path.append(str(PROJECT_ROOT))
        
        logger.info("Importing telegram notifier...")
        from tracker.telegram_bot.notifier import send_telegram_message
        
        # Format the notification message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        message = f"🤖 <b>AI Processing Completed</b>\n\n"
        message += f"<b>Time:</b> {timestamp}\n"
        message += f"<b>Newly Processed Entities:</b> {len(newly_processed_entities)}\n\n"
        
        # Add details for each entity
        message += "<b>Processed Entity Details:</b>\n"
        
        for i, entity in enumerate(newly_processed_entities):
            # Basic entity info
            domain = entity.get('domain', 'Unknown')
            message += f"\n<b>Entity {i+1}:</b> {domain}\n"
            
            # Organization info
            if 'organization' in entity:
                org = entity['organization']
                message += f"<b>Organization:</b> {org.get('name', 'Unknown')}\n"
                message += f"<b>Industry:</b> {org.get('industry', 'Unknown')}"
                if org.get('sub_industry'):
                    message += f" ({org.get('sub_industry')})"
                message += f"\n"
            
            # Geography info
            if 'geography' in entity:
                geo = entity['geography']
                message += f"<b>Country:</b> {geo.get('country_code', 'Unknown')}\n"
            
            # Ransomware group info
            if entity.get('ransomware_group'):
                message += f"<b>Ransomware Group:</b> {entity.get('ransomware_group')}\n"
        
        # Send the message
        logger.info(f"Sending Telegram notification for {len(newly_processed_entities)} entities")
        success = send_telegram_message(message)
        
        if success:
            logger.info("Telegram notification sent successfully")
        else:
            logger.error("Failed to send Telegram notification")
            
        return success
        
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("==== Starting domain enrichment process ====")
    try:
        process_domains()
        logger.info("==== Domain enrichment process completed ====")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
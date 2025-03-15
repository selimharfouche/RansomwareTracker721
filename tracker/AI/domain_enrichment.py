#!/usr/bin/env python3
"""
Domain Enrichment Processor

This script extracts domains from AI.json that haven't been processed yet,
sends them to OpenAI API for enrichment in batches of 100, and saves 
the results to processed_AI.json in the specified output directory.
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
    level=logging.DEBUG,  # Changed from INFO to DEBUG for more details
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Force output to stdout for GitHub Actions
    ]
)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description="Domain enrichment processor")
parser.add_argument("--yes", action="store_true", help="Automatically confirm all batches without prompting")
parser.add_argument("--no-preview", action="store_true", help="Hide the batch preview summary")
parser.add_argument("--output", type=str, help="Output directory for processed_AI.json")
parser.add_argument("--debug", action="store_true", help="Run in debug mode with extra logging")
args = parser.parse_args()

# Force debug mode on
DEBUG_MODE = True

# Determine output directory
if args.output:
    OUTPUT_DIR = Path(args.output)
else:
    # Default to script directory if no output specified
    OUTPUT_DIR = Path(__file__).parent

logger.debug(f"Output directory set to: {OUTPUT_DIR}")

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
logger.debug(f"Ensured output directory exists: {OUTPUT_DIR}")

# Define file paths relative to the output directory
INPUT_FILE = OUTPUT_DIR / "AI.json"
PROCESSED_FILE = OUTPUT_DIR / "processed_AI.json"
RAW_RESPONSES_DIR = OUTPUT_DIR / "raw_responses"
BATCH_PREVIEW_DIR = OUTPUT_DIR / "batch_previews"
DEBUG_LOG_FILE = OUTPUT_DIR / "domain_enrichment_debug.log"

logger.debug(f"Input file path: {INPUT_FILE}")
logger.debug(f"Processed file path: {PROCESSED_FILE}")

# Additional debug log file
if DEBUG_MODE:
    debug_handler = logging.FileHandler(DEBUG_LOG_FILE, mode='w')
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
    logging.getLogger().addHandler(debug_handler)
    logger.debug(f"Added debug log file: {DEBUG_LOG_FILE}")

# Ensure subdirectories exist
RAW_RESPONSES_DIR.mkdir(exist_ok=True)
BATCH_PREVIEW_DIR.mkdir(exist_ok=True)
logger.debug("Created subdirectories for raw responses and batch previews")

# Check for GitHub Actions environment
IN_GITHUB_ACTIONS = os.environ.get('GITHUB_ACTIONS') == 'true'
logger.debug(f"Running in GitHub Actions: {IN_GITHUB_ACTIONS}")

# Print all environment variables in debug mode
if DEBUG_MODE:
    logger.debug("Environment variables:")
    for key, value in os.environ.items():
        if 'KEY' in key or 'TOKEN' in key or 'SECRET' in key:
            # Mask sensitive values but show they exist
            logger.debug(f"  {key}: {'*' * (len(value) if value else 0)}")
        else:
            logger.debug(f"  {key}: {value}")

# Load environment variables - try different methods depending on environment
if IN_GITHUB_ACTIONS:
    # In GitHub Actions, read directly from environment
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    logger.debug(f"In GitHub Actions, OPENAI_API_KEY {'exists' if OPENAI_API_KEY else 'does not exist'}")
    if OPENAI_API_KEY:
        logger.debug(f"OPENAI_API_KEY length: {len(OPENAI_API_KEY)}")
else:
    # In local development, try to use dotenv
    try:
        from dotenv import load_dotenv
        # Look for .env file at project root
        ENV_FILE = Path(__file__).parent.parent.parent / ".env"
        logger.debug(f"Loading .env file from: {ENV_FILE}")
        load_dotenv(dotenv_path=ENV_FILE)
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        logger.debug(f"After loading .env, OPENAI_API_KEY {'exists' if OPENAI_API_KEY else 'does not exist'}")
    except ImportError:
        logger.warning("python-dotenv not installed. Using environment variables directly.")
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        logger.debug(f"OPENAI_API_KEY from env: {'exists' if OPENAI_API_KEY else 'does not exist'}")

if not OPENAI_API_KEY:
    logger.error("OpenAI API key not found in environment variables or .env file")
    logger.info("Please set OPENAI_API_KEY in your environment or .env file")
    # Instead of exiting, try fallback options for debugging
    if DEBUG_MODE:
        logger.warning("Running in debug mode - will use a fake API key for testing")
        OPENAI_API_KEY = "DEBUG_MODE_DUMMY_KEY"
    else:
        exit(1)

# Batch size for API calls
BATCH_SIZE = 100

def load_json_file(file_path: Path) -> Dict:
    """Load a JSON file and return its contents."""
    logger.debug(f"Attempting to load JSON from: {file_path}")
    
    try:
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return {"entities": []}
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.debug(f"File content length: {len(content)} bytes")
            if content.strip() == "":
                logger.warning(f"File is empty: {file_path}")
                return {"entities": []}
                
            data = json.loads(content)
            count = len(data.get('entities', []))
            logger.debug(f"Successfully loaded {file_path} with {count} entities")
            
            # Debug: Print first entity if exists
            if count > 0:
                logger.debug(f"First entity sample: {data['entities'][0]}")
                
            return data
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}. Will create new file.")
        return {"entities": []}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file: {file_path}. Error: {e}")
        logger.error(f"Error position: line {e.lineno}, column {e.colno}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.debug(f"File content around error: {content[max(0, e.pos-50):min(len(content), e.pos+50)]}")
        return {"entities": []}
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        logger.error(traceback.format_exc())
        return {"entities": []}

def save_json_file(data: Dict, file_path: Path) -> bool:
    """Save data to a JSON file."""
    logger.debug(f"Attempting to save JSON to: {file_path}")
    logger.debug(f"Data contains {len(data.get('entities', []))} entities")
    
    try:
        if file_path.exists():
            # Create a backup
            backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
            logger.debug(f"Creating backup of existing file: {backup_path}")
            import shutil
            shutil.copy2(file_path, backup_path)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to {file_path}: {e}")
        logger.error(traceback.format_exc())
        return False

def create_enrichment_prompt(domains: List[str]) -> str:
    """Create a prompt for OpenAI API to request enrichment data."""
    logger.debug(f"Creating enrichment prompt for {len(domains)} domains")
    
    prompt = """Your task is to provide detailed organizational information for each domain.

For each domain name:
1. Thoroughly research the organization to ensure accuracy
2. Determine the headquarters location, industry classification, and company attributes
3. Provide data in the exact JSON format shown below

IMPORTANT: Accuracy is critical, especially for country codes and industry classifications. Use your knowledge of global businesses and organizations. When information isn't explicitly known, determine the most likely values based on contextual indicators in the domain name, company structure, or industry patterns.

Required JSON format for each domain:
{
  "domain": "example.com",
  "geography": {
    "country_code": "USA",  // Always use 3-letter uppercase codes: USA, GBR, DEU, etc.
    "region": "California",  // State/province/region
    "city": "San Francisco"
  },
  "organization": {
    "name": "Example Corporation",
    "industry": "Technology",  // Primary industry sector - be specific and accurate
    "sub_industry": "Software Development",  // More specialized classification
    "size": {
      "employees_range": "100-499",  // Use ranges: 1-9, 10-49, 50-99, 100-499, 500-999, 1000-4999, 5000+
      "revenue_range": "$10M-$50M"   // Use ranges: <$1M, $1M-$10M, $10M-$50M, $50M-$100M, $100M-$500M, $500M-$1B, >$1B
    },
    "status": "Private"  // Private, Public, Government, Non-profit, Educational
  }
}

For domains where specific data cannot be determined with confidence, provide the most likely value while ensuring fields are never empty. Return a valid JSON array containing an object for each domain.

I understand you'll be processing all of these domains. There are exactly {num_domains} domains in this batch, and I need information on all of them.

Domains to research and enrich:
"""
    # Add the list of domains to the prompt
    for domain in domains:
        prompt += f"- {domain}\n"
    
    # Replace the placeholder with the actual count
    prompt = prompt.replace("{num_domains}", str(len(domains)))
    
    logger.debug(f"Created prompt with length: {len(prompt)} characters")
    return prompt

def get_unprocessed_domains(input_data, processed_data):
    """
    Get domains from input_data that are not in processed_data.
    Uses id+group_key combination for precise entity matching.
    """
    logger.debug(f"Looking for unprocessed domains")
    logger.debug(f"Input data has {len(input_data.get('entities', []))} entities")
    logger.debug(f"Processed data has {len(processed_data.get('entities', []))} entities")
    
    # Create lookup table using both id and group_key
    processed_entities = {}
    for entity in processed_data.get('entities', []):
        entity_id = entity.get('id')
        group_key = entity.get('group_key')
        domain = entity.get('domain')
        
        # Primary lookup: id + group_key
        if entity_id and group_key:
            entity_key = f"{entity_id}:{group_key}"
            processed_entities[entity_key] = True
            logger.debug(f"Added processed entity with key: {entity_key}")
        
        # Secondary lookup: just domain as fallback
        if domain:
            processed_entities[f"domain:{domain}"] = True
    
    unprocessed_entities = []
    for entity in input_data.get('entities', []):
        entity_id = entity.get('id')
        group_key = entity.get('group_key')
        domain = entity.get('domain')
        
        if not domain:
            # Skip entities without a domain
            logger.debug(f"Skipping entity without domain: {entity}")
            continue
            
        # Check if the entity exists using id+group_key combination
        if entity_id and group_key:
            entity_key = f"{entity_id}:{group_key}"
            if entity_key not in processed_entities:
                # Entity with this id+group_key doesn't exist yet
                unprocessed_entities.append(entity)
                logger.debug(f"Found unprocessed entity: {domain} (id:{entity_id}, group:{group_key})")
        else:
            # Fallback to domain-only checking if id or group_key is missing
            domain_key = f"domain:{domain}"
            if domain_key not in processed_entities:
                unprocessed_entities.append(entity)
                logger.debug(f"Found unprocessed entity using domain fallback: {domain}")
    
    logger.info(f"Found {len(unprocessed_entities)} unprocessed entities out of {len(input_data.get('entities', []))} total")
    return unprocessed_entities

def batch_domains(domain_entities, batch_size=BATCH_SIZE):
    """Split domain entities into batches of specified size."""
    batches = [domain_entities[i:i + batch_size] for i in range(0, len(domain_entities), batch_size)]
    logger.debug(f"Split {len(domain_entities)} entities into {len(batches)} batches")
    return batches

def enrich_domains_batch(domains: List[str], batch_number: int) -> List[Dict]:
    """
    Request enrichment data for a batch of domains using OpenAI API.
    Returns a list of enriched domain data.
    """
    if not domains:
        logger.warning("No domains to enrich in this batch")
        return []
    
    logger.info(f"Enriching batch {batch_number} with {len(domains)} domains")
    prompt = create_enrichment_prompt(domains)
    
    try:
        logger.info(f"Preparing API request for batch {batch_number}")
        
        # Make API call to OpenAI
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        logger.debug(f"API Headers prepared")
        
        data = {
            "model": "o3-mini",  # Using o3-mini as specified
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that provides accurate information about organizations based on their domain names. Always return data in the exact JSON format requested."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        }
        logger.debug(f"API Request data prepared. Message count: {len(data['messages'])}")
        
        logger.info(f"SENDING API REQUEST TO OPENAI - Batch {batch_number} with {len(domains)} domains")
        
        # ** DEBUG MODE HANDLING **
        if OPENAI_API_KEY == "DEBUG_MODE_DUMMY_KEY":
            logger.warning("DEBUG MODE: Simulating API response instead of making real API call")
            
            # Generate a simulated response for debugging
            simulated_response = []
            for domain in domains:
                simulated_response.append({
                    "domain": domain,
                    "geography": {
                        "country_code": "USA",
                        "region": "Debug Region",
                        "city": "Debug City"
                    },
                    "organization": {
                        "name": f"{domain.split('.')[0].capitalize()} Debug Organization",
                        "industry": "Technology",
                        "sub_industry": "Debugging",
                        "size": {
                            "employees_range": "100-499",
                            "revenue_range": "$10M-$50M"
                        },
                        "status": "Debug"
                    }
                })
            
            logger.debug(f"Generated simulated response with {len(simulated_response)} entities")
            
            # Sleep to simulate API delay
            logger.info("Simulating API delay (10 seconds)...")
            time.sleep(10)
            
            return simulated_response
        
        # Actual API call
        logger.debug("Making actual API request to OpenAI")
        # Set a longer timeout (60 seconds)
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60  # Longer timeout
        )
        
        # Log API response details
        logger.info(f"Received API response with status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        
        # Handle API errors
        if response.status_code != 200:
            logger.error(f"API ERROR: {response.status_code}, {response.text}")
            return []
        
        # Extract content
        logger.debug("Parsing API response JSON")
        response_data = response.json()
        logger.debug(f"Response data keys: {list(response_data.keys())}")
        
        if 'choices' not in response_data or not response_data['choices']:
            logger.error("No choices in API response")
            logger.debug(f"Full response: {response_data}")
            return []
            
        content = response_data['choices'][0]['message']['content']
        
        # Log a snippet of the content
        logger.info(f"API response content (first 100 chars): {content[:100]}...")
        
        # Save raw response for inspection
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        save_raw_response(content, batch_number, timestamp)
        
        # Try to parse the response
        try:
            # The response might be directly parsable as JSON
            logger.debug("Attempting to parse response as JSON")
            enriched_data = json.loads(content)
            
            if isinstance(enriched_data, list):
                logger.info(f"Successfully parsed {len(enriched_data)} entities from response")
                if len(enriched_data) > 0:
                    logger.debug(f"First entity sample: {enriched_data[0]}")
                return enriched_data
            else:
                logger.warning(f"Response is JSON but not a list: {type(enriched_data)}")
                
                # Check if it's a dict with an array inside
                if isinstance(enriched_data, dict) and "domains" in enriched_data:
                    logger.info(f"Found domains array in response with {len(enriched_data['domains'])} items")
                    return enriched_data["domains"]
                
                # Error checks
                if isinstance(enriched_data, dict) and "error" in enriched_data:
                    logger.error(f"API returned error: {enriched_data['error']}")
                
                logger.debug(f"Unexpected JSON structure: {enriched_data}")
                return []
        except json.JSONDecodeError:
            # If not directly parsable, we need to extract the JSON portion
            logger.warning("Could not parse response as JSON directly, trying to extract JSON portion")
            
            # Look for JSON array in the text (basic approach)
            import re
            json_match = re.search(r'\[\s*\{\s*"domain"', content)
            if json_match:
                logger.debug(f"Found JSON array starting at position {json_match.start()}")
                start_idx = json_match.start()
                # Find the closing bracket
                bracket_count = 0
                for i, char in enumerate(content[start_idx:]):
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            # We found the matching closing bracket
                            end_idx = start_idx + i + 1
                            json_str = content[start_idx:end_idx]
                            logger.debug(f"Extracted JSON string of length {len(json_str)}")
                            try:
                                data = json.loads(json_str)
                                logger.info(f"Successfully extracted and parsed JSON array with {len(data)} entities")
                                return data
                            except json.JSONDecodeError as e:
                                logger.error(f"Extracted text is not valid JSON: {e}")
                                logger.debug(f"JSON snippet: {json_str[:100]}...")
            
            logger.error("Could not extract JSON from response")
            # Save the full response to a debug file
            debug_file = OUTPUT_DIR / f"debug_failed_response_{batch_number}_{timestamp}.txt"
            with open(debug_file, 'w') as f:
                f.write(content)
            logger.debug(f"Saved full failed response to {debug_file}")
            return []
            
    except requests.RequestException as e:
        logger.error(f"Network error calling OpenAI API: {e}")
        logger.error(traceback.format_exc())
        return []
    except Exception as e:
        logger.error(f"Unexpected error calling OpenAI API: {e}")
        logger.error(traceback.format_exc())
        return []

def save_raw_response(content, batch_number, timestamp=None):
    """Save the raw API response to a file for inspection."""
    if timestamp is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    
    # Create filename for content
    content_file = RAW_RESPONSES_DIR / f"batch_{batch_number}_{timestamp}_content.txt"
    
    # Save content
    try:
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Response content saved to {content_file}")
        return content_file
    except Exception as e:
        logger.error(f"Error saving content: {e}")
        return None

def process_domain_enrichment(auto_confirm=False, show_preview=True):
    """
    Main function to process domain enrichment:
    1. Load AI.json and processed_AI.json files
    2. Identify unprocessed domains
    3. Process domains in batches of 100 with confirmation for each batch
    4. Parse and add enriched data to processed_AI.json after each batch
    5. Send notification about processed entities
    """
    logger.info("=== Starting domain enrichment process ===")
    logger.info(f"Input file: {INPUT_FILE}")
    logger.info(f"Processed file: {PROCESSED_FILE}")
    
    # Load input file
    logger.debug("Loading input data from AI.json")
    input_data = load_json_file(INPUT_FILE)
    if not input_data or "entities" not in input_data:
        logger.error("No valid entities found in the input file")
        return False
    
    # Load processed file (or create empty structure if file doesn't exist)
    logger.debug("Loading processed data from processed_AI.json")
    processed_data = load_json_file(PROCESSED_FILE)
    if not processed_data:
        logger.info("Creating new processed_AI.json file")
        processed_data = {"entities": [], "total_count": 0, "last_updated": ""}
    
    # Get unprocessed domains
    logger.debug("Finding unprocessed entities")
    unprocessed_entities = get_unprocessed_domains(input_data, processed_data)
    
    if not unprocessed_entities:
        logger.info("No new entities to process - all entities are already in processed_AI.json")
        return True
    
    # Split unprocessed entities into batches
    logger.debug("Splitting entities into batches")
    batched_entities = batch_domains(unprocessed_entities, BATCH_SIZE)
    logger.info(f"Found {len(unprocessed_entities)} unprocessed domains, split into {len(batched_entities)} batches of up to {BATCH_SIZE}")
    
    # Process each batch
    total_processed = 0
    all_newly_processed = []  # Track all newly processed entities for notification
    
    for batch_num, entity_batch in enumerate(batched_entities, 1):
        # Extract just the domains for the API call
        domains_to_process = [entity.get('domain') for entity in entity_batch if entity.get('domain')]
        logger.info(f"Processing batch {batch_num}/{len(batched_entities)} with {len(domains_to_process)} domains")
        
        # Ask for confirmation unless auto_confirm is True
        if not auto_confirm:
            confirmation = input(f"Process batch {batch_num} with {len(domains_to_process)} domains? (yes/no): ")
            if confirmation.lower() != "yes":
                logger.info(f"Skipping batch {batch_num}")
                continue
        
        # Enrich the domains with the API call
        logger.info(f"Sending batch {batch_num} to OpenAI for enrichment")
        enriched_data = enrich_domains_batch(domains_to_process, batch_num)
        
        if not enriched_data:
            logger.error(f"No enriched data obtained from API for batch {batch_num}. Continuing to next batch.")
            continue
        
        logger.info(f"Received enriched data for {len(enriched_data)} domains from OpenAI API")
        
        # Create a dictionary of enriched data by domain for easy lookup
        enriched_by_domain = {entity.get('domain'): entity for entity in enriched_data if entity.get('domain')}
        logger.debug(f"Created lookup dictionary with {len(enriched_by_domain)} domains")
        
        # Add enrichment data to each entity in this batch
        newly_processed = []
        for entity in entity_batch:
            domain = entity.get('domain')
            if domain and domain in enriched_by_domain:
                # Merge the basic entity data with the enrichment data
                enriched_entity = enriched_by_domain[domain]
                
                # Keep the original id, group_key, and ransomware_group
                enriched_entity['id'] = entity.get('id')
                enriched_entity['group_key'] = entity.get('group_key')
                enriched_entity['ransomware_group'] = entity.get('ransomware_group')
                
                newly_processed.append(enriched_entity)
                all_newly_processed.append(enriched_entity)  # Add to the complete list for notification
                logger.debug(f"Added enriched entity for domain: {domain}")
        
        # Add newly processed entities to the processed data
        if newly_processed:
            logger.info(f"Adding {len(newly_processed)} newly processed entities to processed_AI.json")
            processed_data['entities'].extend(newly_processed)
            total_processed += len(newly_processed)
            processed_data['total_count'] = len(processed_data['entities'])
            processed_data['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            
            # Save the updated processed data after each batch
            save_json_file(processed_data, PROCESSED_FILE)
            logger.info(f"Saved batch {batch_num} with {len(newly_processed)} entities to processed_AI.json")
        
        # Add delay between batches to avoid rate limiting
        if batch_num < len(batched_entities):
            delay = 2  # 2 second delay between batches
            logger.info(f"Waiting {delay} seconds before processing next batch")
            time.sleep(delay)
    
    logger.info(f"Total entities processed: {total_processed}")
    
    # Send notification about all newly processed entities
    if all_newly_processed:
        logger.info(f"Sending notification for {len(all_newly_processed)} newly processed entities")
        success = send_telegram_notification(all_newly_processed)
        logger.info(f"Notification sent successfully: {success}")
    
    return True

def send_telegram_notification(newly_processed_entities):
    """Send a Telegram notification with details about newly processed entities."""
    if not newly_processed_entities:
        logger.info("No newly processed entities to notify about")
        return False
    
    try:
        # Add project root to Python path for imports
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        import sys
        sys.path.append(str(PROJECT_ROOT))
        
        try:
            logger.debug(f"Attempting to import telegram_bot.notifier")
            from tracker.telegram_bot.notifier import send_telegram_message
            logger.debug(f"Successfully imported telegram_bot.notifier")
        except ImportError as e:
            logger.error(f"Failed to import telegram notifier module: {e}")
            logger.error(traceback.format_exc())
            return False
        
        # Format the notification message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        message = f"🤖 <b>AI Processing Completed</b>\n\n"
        message += f"<b>Time:</b> {timestamp}\n"
        message += f"<b>Newly Processed Entities:</b> {len(newly_processed_entities)}\n\n"
        
        # Add details for up to 5 entities
        message += "<b>Processed Entity Details:</b>\n"
        
        for i, entity in enumerate(newly_processed_entities[:5]):
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
                
                # Size info if available
                if 'size' in org:
                    size = org['size']
                    if size.get('employees_range'):
                        message += f"<b>Employees:</b> {size.get('employees_range')}\n"
                    if size.get('revenue_range'):
                        message += f"<b>Revenue:</b> {size.get('revenue_range')}\n"
                
                # Status if available
                if org.get('status'):
                    message += f"<b>Status:</b> {org.get('status')}\n"
            
            # Geography info
            if 'geography' in entity:
                geo = entity['geography']
                message += f"<b>Country:</b> {geo.get('country_code', 'Unknown')}\n"
                
                # Location if available
                if geo.get('city') or geo.get('region'):
                    location = []
                    if geo.get('city'):
                        location.append(geo.get('city'))
                    if geo.get('region'):
                        location.append(geo.get('region'))
                    message += f"<b>Location:</b> {', '.join(location)}\n"
            
            # Ransomware group info
            if entity.get('ransomware_group'):
                message += f"<b>Ransomware Group:</b> {entity.get('ransomware_group')}\n"
            
            # Add a separator between entities
            if i < min(4, len(newly_processed_entities) - 1):
                message += "\n" + "—" * 20 + "\n"
        
        # Add a note if there are more entities not shown
        if len(newly_processed_entities) > 5:
            message += f"\n... and {len(newly_processed_entities) - 5} more entities\n"
        
        # Send the message
        logger.debug(f"Sending Telegram notification message of length {len(message)}")
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
    logger.info("Starting domain enrichment process")
    
    # Check if API key is configured
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API key not found. Running in simulation mode.")
        simulate_enrichment()
    else:
        # Force auto_confirm to True if running in GitHub Actions
        if IN_GITHUB_ACTIONS:
            logger.info("Running in GitHub Actions, auto-confirming all batches")
            process_domain_enrichment(auto_confirm=True, show_preview=False)
        else:
            process_domain_enrichment(auto_confirm=args.yes, show_preview=not args.no_preview)
    
    logger.info("Domain enrichment process completed")
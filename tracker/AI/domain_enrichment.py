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
from pathlib import Path
from typing import List, Dict, Any
import requests
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description="Domain enrichment processor")
parser.add_argument("--yes", action="store_true", help="Automatically confirm all batches without prompting")
parser.add_argument("--no-preview", action="store_true", help="Hide the batch preview summary")
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
RAW_RESPONSES_DIR = OUTPUT_DIR / "raw_responses"
BATCH_PREVIEW_DIR = OUTPUT_DIR / "batch_previews"

# Ensure subdirectories exist
RAW_RESPONSES_DIR.mkdir(exist_ok=True)
BATCH_PREVIEW_DIR.mkdir(exist_ok=True)

# Check for GitHub Actions environment
IN_GITHUB_ACTIONS = os.environ.get('GITHUB_ACTIONS') == 'true'

# Load environment variables - try different methods depending on environment
if IN_GITHUB_ACTIONS:
    # In GitHub Actions, read directly from environment
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
else:
    # In local development, try to use dotenv
    try:
        from dotenv import load_dotenv
        # Look for .env file at project root
        ENV_FILE = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(dotenv_path=ENV_FILE)
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    except ImportError:
        logger.warning("python-dotenv not installed. Using environment variables directly.")
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logger.error("OpenAI API key not found in environment variables or .env file")
    logger.info("Please set OPENAI_API_KEY in your environment or .env file")
    exit(1)

# Batch size for API calls
BATCH_SIZE = 100

def load_json_file(file_path: Path) -> Dict:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info(f"File not found: {file_path}. Will create new file.")
        return {"entities": []}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        return {"entities": []}
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return {"entities": []}

def save_json_file(data: Dict, file_path: Path) -> bool:
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to {file_path}: {e}")
        return False

def create_enrichment_prompt(domains: List[str]) -> str:
    """Create a prompt for OpenAI API to request enrichment data."""
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
    
    return prompt

def save_batch_preview(domains: List[str], batch_number: int) -> Path:
    """
    Save a preview of what will be sent to the OpenAI API for a batch.
    Returns the path to the preview file.
    """
    # Generate the prompt that will be sent
    prompt = create_enrichment_prompt(domains)
    
    # Create a preview object with all information that will be sent
    preview = {
        "batch_number": batch_number,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "num_domains": len(domains),
        "domains": domains,
        "api_request": {
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
    }
    
    # Create a filename for the preview
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    preview_file = BATCH_PREVIEW_DIR / f"batch_{batch_number}_{timestamp}_preview.json"
    
    # Save the preview to a file
    try:
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(preview, f, indent=2, ensure_ascii=False)
        logger.info(f"Batch preview saved to {preview_file}")
        return preview_file
    except Exception as e:
        logger.error(f"Error saving batch preview: {e}")
        return None

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

def get_unprocessed_domains(input_data, processed_data):
    """
    Get domains from input_data that are not in processed_data.
    Uses id+group_key combination for precise entity matching.
    """
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
            continue
            
        # Check if the entity exists using id+group_key combination
        if entity_id and group_key:
            entity_key = f"{entity_id}:{group_key}"
            if entity_key not in processed_entities:
                # Entity with this id+group_key doesn't exist yet
                unprocessed_entities.append(entity)
                # Log for debugging
                logger.info(f"Found unprocessed entity with id+group_key: {entity_id}:{group_key}, domain: {domain}")
        else:
            # Fallback to domain-only checking if id or group_key is missing
            domain_key = f"domain:{domain}"
            if domain_key not in processed_entities:
                unprocessed_entities.append(entity)
                # Log for debugging
                logger.info(f"Found unprocessed entity using domain fallback: {domain}")
    
    logger.info(f"Found {len(unprocessed_entities)} unprocessed entities out of {len(input_data.get('entities', []))} total")
    return unprocessed_entities

def batch_domains(domain_entities, batch_size=BATCH_SIZE):
    """Split domain entities into batches of specified size."""
    return [domain_entities[i:i + batch_size] for i in range(0, len(domain_entities), batch_size)]

def print_batch_preview_summary(domains: List[str], batch_number: int):
    """Print a summary of the batch preview to the console."""
    print("\n" + "="*80)
    print(f"BATCH {batch_number} PREVIEW")
    print("="*80)
    print(f"Total domains in batch: {len(domains)}")
    print("\nFirst 5 domains in batch:")
    for i, domain in enumerate(domains[:5]):
        print(f"  {i+1}. {domain}")
    if len(domains) > 5:
        print(f"  ... and {len(domains) - 5} more")
    print("\nThe OpenAI API will be asked to:")
    print("  1. Research each organization based on its domain")
    print("  2. Determine the organization's location, industry, and attributes")
    print("  3. Return the data in a standardized JSON format")
    print("\nA complete preview of the API request has been saved to the batch_previews directory.")
    print("="*80 + "\n")

def enrich_domains_batch(domains: List[str], batch_number: int) -> List[Dict]:
    """
    Request enrichment data for a batch of domains using OpenAI API.
    Returns a list of enriched domain data.
    """
    if not domains:
        return []
    
    prompt = create_enrichment_prompt(domains)
    
    try:
        logger.info(f"Sending request to OpenAI API for batch {batch_number} ({len(domains)} domains)")
        
        # Make API call to OpenAI
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
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
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        # Handle API errors
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code}, {response.text}")
            return []
        
        # Extract content
        response_data = response.json()
        content = response_data['choices'][0]['message']['content']
        
        # Save raw response for inspection
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        save_raw_response(content, batch_number, timestamp)
        
        # Try to parse the response
        try:
            # The response might be directly parsable as JSON
            enriched_data = json.loads(content)
            if isinstance(enriched_data, list):
                logger.info(f"Successfully parsed {len(enriched_data)} entities from response")
                return enriched_data
            else:
                logger.warning(f"Response is JSON but not a list: {type(enriched_data)}")
                
                # Check if it's a dict with an array inside
                if isinstance(enriched_data, dict) and "domains" in enriched_data:
                    return enriched_data["domains"]
                
                # Error checks
                if isinstance(enriched_data, dict) and "error" in enriched_data:
                    logger.error(f"API returned error: {enriched_data['error']}")
                    
                return []
        except json.JSONDecodeError:
            # If not directly parsable, we need to extract the JSON portion
            logger.warning("Could not parse response as JSON directly, will try to extract JSON portion")
            
            # Look for JSON array in the text (basic approach)
            import re
            json_match = re.search(r'\[\s*\{\s*"domain"', content)
            if json_match:
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
                            try:
                                data = json.loads(json_str)
                                logger.info(f"Successfully extracted and parsed JSON array with {len(data)} entities")
                                return data
                            except json.JSONDecodeError:
                                logger.error(f"Extracted text is not valid JSON: {json_str[:100]}...")
            
            logger.error("Could not extract JSON from response")
            return []
            
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return []

def process_domain_enrichment():
    """
    Main function to process domain enrichment:
    1. Load AI.json and processed_AI.json files
    2. Identify unprocessed domains
    3. Process domains in batches of 100 with confirmation for each batch
    4. Parse and add enriched data to processed_AI.json after each batch
    """
    # Load input file
    input_data = load_json_file(INPUT_FILE)
    if not input_data or "entities" not in input_data:
        logger.error(f"No valid entities found in the input file: {INPUT_FILE}")
        return False
    
    # Load processed file (or create empty structure if file doesn't exist)
    processed_data = load_json_file(PROCESSED_FILE)
    if not processed_data:
        processed_data = {"entities": [], "total_count": 0, "last_updated": ""}
    
    # Get unprocessed domains
    unprocessed_entities = get_unprocessed_domains(input_data, processed_data)
    
    if not unprocessed_entities:
        logger.info("No new entities to process")
        return True
    
    # Split unprocessed entities into batches
    batched_entities = batch_domains(unprocessed_entities, BATCH_SIZE)
    logger.info(f"Found {len(unprocessed_entities)} unprocessed domains, split into {len(batched_entities)} batches of {BATCH_SIZE}")
    
    # Process each batch
    total_processed = 0
    
    for batch_num, entity_batch in enumerate(batched_entities, 1):
        # Extract just the domains for the API call
        domains_to_process = [entity.get('domain') for entity in entity_batch if entity.get('domain')]
        logger.info(f"Batch {batch_num}/{len(batched_entities)} with {len(domains_to_process)} domains")
        
        # Create and save a preview of what will be sent to the API
        preview_file = save_batch_preview(domains_to_process, batch_num)
        
        # Show a summary of the batch preview if requested
        if not args.no_preview:
            print_batch_preview_summary(domains_to_process, batch_num)
        
        # Ask for confirmation unless auto_confirm is True
        if not args.yes:
            confirmation = input(f"Process batch {batch_num} with {len(domains_to_process)} domains? (yes/no): ")
            if confirmation.lower() != "yes":
                logger.info(f"Skipping batch {batch_num}")
                continue
        
        # Enrich the domains with the API call
        enriched_data = enrich_domains_batch(domains_to_process, batch_num)
        
        if not enriched_data:
            logger.error(f"No enriched data obtained from API for batch {batch_num}. Continuing to next batch.")
            continue
        
        # Create a dictionary of enriched data by domain for easy lookup
        enriched_by_domain = {entity.get('domain'): entity for entity in enriched_data if entity.get('domain')}
        
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
        
        # Add newly processed entities to the processed data
        if newly_processed:
            processed_data['entities'].extend(newly_processed)
            total_processed += len(newly_processed)
            processed_data['total_count'] = len(processed_data['entities'])
            processed_data['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            
            # Save the updated processed data after each batch
            save_json_file(processed_data, PROCESSED_FILE)
            logger.info(f"Added {len(newly_processed)} newly processed entities from batch {batch_num}")
        
        # Add delay between batches to avoid rate limiting
        if batch_num < len(batched_entities):
            delay = 2  # 2 second delay between batches
            logger.info(f"Waiting {delay} seconds before processing next batch")
            time.sleep(delay)
    
    logger.info(f"Total entities processed: {total_processed}")
    return True

def simulate_enrichment():
    """
    Simulate enrichment for environments without an OpenAI API key.
    This creates placeholder enrichment data.
    """
    logger.info("Running in simulation mode (no real API calls will be made)")
    
    # Load input file
    input_data = load_json_file(INPUT_FILE)
    if not input_data or "entities" not in input_data:
        logger.error(f"No valid entities found in the input file: {INPUT_FILE}")
        return False
    
    # Load processed file (or create empty structure if file doesn't exist)
    processed_data = load_json_file(PROCESSED_FILE)
    if not processed_data:
        processed_data = {"entities": [], "total_count": 0, "last_updated": ""}
    
    # Get unprocessed domains
    unprocessed_entities = get_unprocessed_domains(input_data, processed_data)
    
    if not unprocessed_entities:
        logger.info("No new entities to process")
        return True
    
    # Create placeholder enrichment for each entity
    newly_processed = []
    for entity in unprocessed_entities:
        domain = entity.get('domain')
        if not domain:
            continue
            
        # Create placeholder enriched entity
        enriched_entity = {
            "id": entity.get('id'),
            "domain": domain,
            "group_key": entity.get('group_key'),
            "ransomware_group": entity.get('ransomware_group'),
            "geography": {
                "country_code": "USA",
                "region": "Unknown Region",
                "city": "Unknown City"
            },
            "organization": {
                "name": f"{domain.split('.')[0].capitalize()} Organization",
                "industry": "Technology",
                "sub_industry": "Software",
                "size": {
                    "employees_range": "100-499",
                    "revenue_range": "$10M-$50M"
                },
                "status": "Private"
            }
        }
        
        newly_processed.append(enriched_entity)
    
    # Add newly processed entities to the processed data
    if newly_processed:
        processed_data['entities'].extend(newly_processed)
        processed_data['total_count'] = len(processed_data['entities'])
        processed_data['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        
        # Save the updated processed data
        save_json_file(processed_data, PROCESSED_FILE)
        logger.info(f"Added {len(newly_processed)} simulated enriched entities")
    
    return True

if __name__ == "__main__":
    logger.info("Starting domain enrichment process")
    
    # Check if API key is configured
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API key not found. Running in simulation mode.")
        simulate_enrichment()
    else:
        process_domain_enrichment()
    
    logger.info("Domain enrichment process completed")
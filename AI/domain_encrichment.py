#!/usr/bin/env python3
"""
Domain Enrichment Processor Using OpenAI Batch API

This script:
1. Extracts unprocessed domains from AI.json
2. Creates a batch file for asynchronous processing
3. Submits the batch to OpenAI's Batch API
4. Retrieves and processes results when complete
5. Updates processed_AI.json with enriched data
"""

import json
import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Define file paths
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent  # Go up one level to the project root
ENV_FILE = PROJECT_ROOT / ".env"  # Path to .env file at root directory
INPUT_FILE = SCRIPT_DIR / "AI.json"
PROCESSED_FILE = SCRIPT_DIR / "processed_AI.json"
BATCH_DIR = SCRIPT_DIR / "batch_files"
BATCH_INPUT_FILE = BATCH_DIR / "batch_input.jsonl"
BATCH_OUTPUT_FILE = BATCH_DIR / "batch_output.jsonl"

# Ensure directories exist
BATCH_DIR.mkdir(exist_ok=True)

# Load environment variables from .env file
load_dotenv(dotenv_path=ENV_FILE)

# OpenAI API Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OpenAI API key not found in environment variables or .env file")
    exit(1)

openai.api_key = OPENAI_API_KEY

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

def get_unprocessed_domains(input_data, processed_data):
    """Get domains from input_data that are not in processed_data."""
    processed_domains = {entity.get('domain'): True for entity in processed_data.get('entities', [])}
    
    unprocessed_entities = []
    for entity in input_data.get('entities', []):
        domain = entity.get('domain')
        if domain and domain not in processed_domains:
            unprocessed_entities.append(entity)
    
    return unprocessed_entities

def create_batch_file(entities: List[Dict], batch_file_path: Path) -> bool:
    """Create a JSONL batch file for OpenAI Batch API."""
    try:
        with open(batch_file_path, 'w', encoding='utf-8') as f:
            for idx, entity in enumerate(entities):
                domain = entity.get('domain')
                if not domain:
                    continue
                
                # Create prompt for this domain
                system_message = "You are a helpful assistant that provides accurate information about organizations based on their domain names."
                user_message = f"""
Provide detailed organizational information for the domain: {domain}

Research the organization thoroughly to determine its:
1. Headquarters location (country, region, city)
2. Industry classification (primary industry and sub-industry)
3. Company attributes (size, status)

Return data in this exact JSON format:
{{
  "domain": "{domain}",
  "geography": {{
    "country_code": "USA",  /* Always use 3-letter uppercase codes */
    "region": "California",
    "city": "San Francisco"
  }},
  "organization": {{
    "name": "Example Corporation",
    "industry": "Technology",
    "sub_industry": "Software Development",
    "size": {{
      "employees_range": "100-499",
      "revenue_range": "$10M-$50M"
    }},
    "status": "Private"  /* Private, Public, Government, Non-profit, Educational */
  }}
}}

IMPORTANT: Determine the most accurate values possible, ensuring all fields have values.
"""
                
                # Create the batch request object
                request = {
                    "custom_id": f"{entity.get('id', f'domain-{idx}')}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "o3-mini",
                        "messages": [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_message}
                        ],
                        "response_format": {"type": "json_object"}
                    }
                }
                
                # Write the request to the batch file
                f.write(json.dumps(request) + '\n')
        
        logger.info(f"Successfully created batch file with {len(entities)} requests at {batch_file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error creating batch file: {e}")
        return False

def upload_batch_file(file_path: Path) -> str:
    """Upload a batch file to OpenAI and return the file ID."""
    try:
        with open(file_path, 'rb') as f:
            response = openai.files.create(
                file=f,
                purpose="batch"
            )
        
        file_id = response.id
        logger.info(f"Successfully uploaded batch file with ID: {file_id}")
        return file_id
    
    except Exception as e:
        logger.error(f"Error uploading batch file: {e}")
        return None

def create_batch(file_id: str) -> str:
    """Create a batch processing job and return the batch ID."""
    try:
        batch = openai.batches.create(
            input_file_id=file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        
        batch_id = batch.id
        logger.info(f"Successfully created batch with ID: {batch_id}")
        return batch_id
    
    except Exception as e:
        logger.error(f"Error creating batch: {e}")
        return None

def check_batch_status(batch_id: str) -> Dict:
    """Check the status of a batch and return the batch object."""
    try:
        batch = openai.batches.retrieve(batch_id)
        logger.info(f"Batch {batch_id} status: {batch.status}")
        return batch
    
    except Exception as e:
        logger.error(f"Error checking batch status: {e}")
        return None

def download_batch_results(file_id: str, output_path: Path) -> bool:
    """Download batch results and save to a file."""
    try:
        response = openai.files.content(file_id)
        content = response.text
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Successfully downloaded batch results to {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error downloading batch results: {e}")
        return False

def parse_batch_results(result_path: Path, entities: List[Dict]) -> List[Dict]:
    """Parse batch results and merge with original entity data."""
    try:
        # Create a lookup dictionary of entities by ID
        entity_by_id = {entity.get('id'): entity for entity in entities if entity.get('id')}
        
        enriched_entities = []
        
        with open(result_path, 'r', encoding='utf-8') as f:
            for line in f:
                result = json.loads(line)
                custom_id = result.get('custom_id')
                
                # Skip if there was an error
                if result.get('error'):
                    logger.warning(f"Error processing domain with ID {custom_id}: {result.get('error')}")
                    continue
                
                # Extract the response
                response = result.get('response', {})
                if response.get('status_code') != 200:
                    logger.warning(f"Non-200 status code for domain with ID {custom_id}: {response.get('status_code')}")
                    continue
                
                # Get the body from the response
                body = response.get('body', {})
                
                # Extract the assistant's message content
                choices = body.get('choices', [])
                if not choices:
                    logger.warning(f"No choices in response for domain with ID {custom_id}")
                    continue
                
                content = choices[0].get('message', {}).get('content', '{}')
                
                try:
                    # Parse the content as JSON
                    enrichment_data = json.loads(content)
                    
                    # Get the original entity data
                    original_entity = entity_by_id.get(custom_id)
                    if not original_entity:
                        logger.warning(f"Could not find original entity with ID {custom_id}")
                        continue
                    
                    # Merge the enrichment data with the original entity data
                    enriched_entity = enrichment_data.copy()
                    enriched_entity['id'] = original_entity.get('id')
                    enriched_entity['group_key'] = original_entity.get('group_key')
                    enriched_entity['ransomware_group'] = original_entity.get('ransomware_group')
                    
                    enriched_entities.append(enriched_entity)
                
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON from response content for domain with ID {custom_id}")
                    continue
        
        logger.info(f"Successfully parsed {len(enriched_entities)} enriched entities from batch results")
        return enriched_entities
    
    except Exception as e:
        logger.error(f"Error parsing batch results: {e}")
        return []

def process_domain_enrichment():
    """
    Main function to process domain enrichment using OpenAI Batch API:
    1. Load AI.json and processed_AI.json files
    2. Identify unprocessed domains
    3. Create a batch file
    4. Submit the batch for processing
    5. Wait for completion
    6. Download and parse results
    7. Update processed_AI.json
    """
    # Load input file
    input_data = load_json_file(INPUT_FILE)
    if not input_data or "entities" not in input_data:
        logger.error("No valid entities found in the input file")
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
    
    logger.info(f"Found {len(unprocessed_entities)} unprocessed domains")
    
    # Create a batch file for OpenAI Batch API
    if not create_batch_file(unprocessed_entities, BATCH_INPUT_FILE):
        logger.error("Failed to create batch file")
        return False
    
    # Upload the batch file
    file_id = upload_batch_file(BATCH_INPUT_FILE)
    if not file_id:
        logger.error("Failed to upload batch file")
        return False
    
    # Create a batch
    batch_id = create_batch(file_id)
    if not batch_id:
        logger.error("Failed to create batch")
        return False
    
    # Check batch status until complete
    batch = check_batch_status(batch_id)
    if not batch:
        logger.error("Failed to check batch status")
        return False
    
    # Wait for batch to complete
    while batch.status not in ["completed", "failed", "expired", "cancelled"]:
        logger.info(f"Batch status: {batch.status}, waiting 60 seconds before checking again...")
        time.sleep(60)
        batch = check_batch_status(batch_id)
        if not batch:
            logger.error("Failed to check batch status")
            return False
    
    # Check if batch completed successfully
    if batch.status != "completed":
        logger.error(f"Batch failed with status: {batch.status}")
        return False
    
    # Download batch results
    output_file_id = batch.output_file_id
    if not output_file_id:
        logger.error("No output file ID in batch")
        return False
    
    if not download_batch_results(output_file_id, BATCH_OUTPUT_FILE):
        logger.error("Failed to download batch results")
        return False
    
    # Parse batch results
    enriched_entities = parse_batch_results(BATCH_OUTPUT_FILE, unprocessed_entities)
    if not enriched_entities:
        logger.error("No enriched entities from batch results")
        return False
    
    # Add newly processed entities to the processed data
    processed_data['entities'].extend(enriched_entities)
    processed_data['total_count'] = len(processed_data['entities'])
    processed_data['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    
    # Save the updated processed data
    if not save_json_file(processed_data, PROCESSED_FILE):
        logger.error("Failed to save processed data")
        return False
    
    logger.info(f"Successfully added {len(enriched_entities)} enriched entities to {PROCESSED_FILE}")
    return True

if __name__ == "__main__":
    logger.info("Starting domain enrichment process using OpenAI Batch API")
    
    # Check if API key is configured
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found. Please add it to your .env file.")
        logger.info("Create a .env file at the project root with: OPENAI_API_KEY=your-key-here")
        exit(1)
    
    success = process_domain_enrichment()
    
    if success:
        logger.info("Domain enrichment process completed successfully")
    else:
        logger.error("Domain enrichment process failed")
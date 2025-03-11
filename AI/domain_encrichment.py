#!/usr/bin/env python3
"""
Domain Enrichment Script

This script extracts domain names from AI.json, uses the OpenAI API to enrich
them with additional data, and saves raw API responses for inspection.

By default, processes only the first batch of 50 domains. Use the --all flag
to process all batches.
"""

import json
import os
import time
import logging
import argparse
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
OUTPUT_FILE = SCRIPT_DIR / "AI_enriched.json"
RAW_RESPONSES_DIR = SCRIPT_DIR / "raw_responses"

# Ensure raw responses directory exists
RAW_RESPONSES_DIR.mkdir(exist_ok=True)

# Load environment variables from .env file
load_dotenv(dotenv_path=ENV_FILE)

# OpenAI API Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OpenAI API key not found in environment variables or .env file")
    exit(1)

openai.api_key = OPENAI_API_KEY

# Batch size for API calls
BATCH_SIZE = 50

def load_json_file(file_path: Path) -> Dict:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {file_path}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

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

def batch_domains(domains: List[str], batch_size: int = BATCH_SIZE) -> List[List[str]]:
    """Split a list of domains into batches of specified size."""
    return [domains[i:i + batch_size] for i in range(0, len(domains), batch_size)]

def create_enrichment_prompt(domains: List[str]) -> str:
    """Create a prompt for OpenAI API to request enrichment data."""
    prompt = """For each of the following domain names, provide structured data about the organization in this exact JSON format:
{
  "domain": "example.com",
  "geography": {
    "country_code": "USA",  // Always use 3-letter uppercase codes: USA, GBR, DEU, etc.
    "region": "California",  // State/province/region
    "city": "San Francisco"
  },
  "organization": {
    "name": "Example Corporation",
    "industry": "Technology",  // Primary industry sector
    "sub_industry": "Software Development",
    "size": {
      "employees_range": "100-499",  // Use ranges: 1-9, 10-49, 50-99, 100-499, 500-999, 1000-4999, 5000+
      "revenue_range": "$10M-$50M"   // Use ranges: <$1M, $1M-$10M, $10M-$50M, $50M-$100M, $100M-$500M, $500M-$1B, >$1B
    },
    "status": "Private"  // Private, Public, Government, Non-profit, Educational
  }
}

Only include factual information. If information is unknown, use null value. Return a valid JSON array with an object for each domain.

Domains to enrich:
"""
    # Add the list of domains to the prompt
    for domain in domains:
        prompt += f"- {domain}\n"
    
    return prompt

def save_raw_response(response, content, batch_index: int):
    """Save the raw API response to a file for inspection."""
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    
    # Create filenames for raw response and content
    response_file = RAW_RESPONSES_DIR / f"batch_{batch_index+1}_{timestamp}_response.json"
    content_file = RAW_RESPONSES_DIR / f"batch_{batch_index+1}_{timestamp}_content.txt"
    
    # Save API response details
    try:
        response_data = {
            "timestamp": timestamp,
            "batch_index": batch_index,
            "model": response.model,
            "usage": response.usage.model_dump() if hasattr(response.usage, "model_dump") else vars(response.usage),
            "finish_reason": response.choices[0].finish_reason
        }
        
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Raw response metadata saved to {response_file}")
    except Exception as e:
        logger.error(f"Error saving response metadata: {e}")
    
    # Save content separately (for easier inspection)
    try:
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Response content saved to {content_file}")
        return content_file
    except Exception as e:
        logger.error(f"Error saving content: {e}")
        return None

def enrich_domains_batch(domains: List[str], batch_index: int) -> None:
    """
    Request enrichment data for a batch of domains using OpenAI API
    and save the raw response for inspection.
    """
    if not domains:
        return
    
    prompt = create_enrichment_prompt(domains)
    
    try:
        logger.info(f"Sending request to OpenAI API for batch {batch_index+1} ({len(domains)} domains)")
        
        # Make API call with minimal parameters to avoid unsupported parameter errors
        response = openai.chat.completions.create(
            model="o3-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides accurate information about organizations based on their domain names. Always return data in the exact JSON format requested."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract content
        content = response.choices[0].message.content
        
        # Save raw response and content for inspection
        save_raw_response(response, content, batch_index)
        
        logger.info(f"Successfully saved raw response for batch {batch_index+1}")
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API for batch {batch_index+1}: {e}")

def process_domain_enrichment(process_all=False):
    """
    Main function to process domain enrichment:
    1. Load the AI.json file
    2. Extract domains from entities
    3. Batch domains into groups of 50
    4. Process first batch only (or all batches if process_all=True)
    5. Save raw responses for inspection
    """
    # Load input file
    data = load_json_file(INPUT_FILE)
    if not data or "entities" not in data:
        logger.error("No valid entities found in the input file")
        return False
    
    # Extract domains from entities
    domains = []
    
    for entity in data["entities"]:
        domain = entity.get("domain")
        if domain:
            domains.append(domain)
    
    if not domains:
        logger.warning("No domains found in entities")
        return False
    
    logger.info(f"Found {len(domains)} domains to enrich")
    
    # Batch domains into groups of 50
    batched_domains = batch_domains(domains)
    total_batches = len(batched_domains)
    logger.info(f"Split into {total_batches} batches of up to {BATCH_SIZE} domains each")
    
    # Process first batch only by default, or all batches if requested
    batches_to_process = total_batches if process_all else 1
    batches_to_process = min(batches_to_process, total_batches)
    
    logger.info(f"Will process {batches_to_process} batch(es) out of {total_batches}")
    
    # Process each batch
    for i in range(batches_to_process):
        batch = batched_domains[i]
        logger.info(f"Processing batch {i+1}/{total_batches} ({len(batch)} domains)")
        
        enrich_domains_batch(batch, i)
        
        # Add delay between batches if processing multiple
        if i < batches_to_process - 1:
            time.sleep(2)  # 2 second delay between batches
    
    logger.info(f"Done processing {batches_to_process} batch(es)")
    logger.info(f"Raw responses saved to {RAW_RESPONSES_DIR}")
    
    return True

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Domain enrichment script")
    parser.add_argument("--all", action="store_true", help="Process all batches instead of just the first one")
    args = parser.parse_args()
    
    logger.info("Starting domain enrichment process")
    
    # Check if API key is configured
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found. Please add it to your .env file.")
        logger.info("Create a .env file at the project root with: OPENAI_API_KEY=your-key-here")
        exit(1)
    
    success = process_domain_enrichment(process_all=args.all)
    
    if success:
        logger.info("Domain enrichment process completed")
        logger.info(f"Raw responses saved to {RAW_RESPONSES_DIR}")
        logger.info("You can now inspect the responses and develop a custom processing script")
    else:
        logger.error("Domain enrichment process failed")
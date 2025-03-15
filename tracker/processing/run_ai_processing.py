#!/usr/bin/env python3
"""
AI Processing Coordinator

This script coordinates running AI scripts from tracker/AI and saves results to data/AI.
Use the --github flag when running in GitHub Actions environment.
"""

import os
import sys
import json
import argparse
import subprocess
import logging
import time
import traceback
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Force logs to stdout for GitHub Actions
    ]
)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description="AI Processing Coordinator")
parser.add_argument("--github", action="store_true", help="Run in GitHub Actions mode")
args = parser.parse_args()

# Define paths based on environment
current_dir = os.getcwd()
logger.info(f"Current working directory: {current_dir}")

# Set up directory paths
if args.github:
    PROJECT_ROOT = Path(current_dir)
else:
    SCRIPT_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Define key directories
SCRIPTS_DIR = PROJECT_ROOT / "tracker" / "AI"
OUTPUT_DIR = PROJECT_ROOT / "data" / "AI"

logger.info(f"Scripts directory: {SCRIPTS_DIR}")
logger.info(f"Output directory: {OUTPUT_DIR}")

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def check_api_key():
    """Check if OpenAI API key is available and valid."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return False
    
    logger.info(f"OPENAI_API_KEY found (length: {len(api_key)})")
    return True

def run_extract_ai_fields():
    """Run the extract_ai_fields.py script"""
    logger.info("Running extract_ai_fields.py...")
    
    try:
        script_path = SCRIPTS_DIR / "extract_ai_fields.py"
        if not script_path.exists():
            logger.error(f"Script does not exist: {script_path}")
            return False
        
        cmd = [sys.executable, str(script_path), "--output", str(OUTPUT_DIR)]
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Use subprocess.run to capture all output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Print all output
        if result.stdout:
            logger.info(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            logger.info(f"STDERR:\n{result.stderr}")
        
        # Verify that AI.json was created
        ai_json_path = OUTPUT_DIR / "AI.json"
        if not ai_json_path.exists():
            logger.error(f"Failed to create {ai_json_path}")
            return False
        
        try:
            with open(ai_json_path, 'r') as f:
                data = json.load(f)
                entity_count = len(data.get('entities', []))
                logger.info(f"AI.json created with {entity_count} entities")
        except Exception as e:
            logger.error(f"Error reading AI.json: {e}")
            return False
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"extract_ai_fields.py failed with exit code {e.returncode}")
        if e.stdout:
            logger.info(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            logger.error(f"STDERR:\n{e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running extract_ai_fields.py: {e}")
        logger.error(traceback.format_exc())
        return False

def run_domain_enrichment():
    """Run the domain_enrichment.py script"""
    logger.info("Running domain_enrichment.py...")
    
    try:
        script_path = SCRIPTS_DIR / "domain_enrichment.py"
        if not script_path.exists():
            logger.error(f"Script does not exist: {script_path}")
            return False
        
        # Ensure API key is available
        if not check_api_key():
            logger.error("OpenAI API key not available. Cannot continue.")
            return False
        
        # Run the script with --yes flag for automatic confirmation
        cmd = [sys.executable, str(script_path), "--yes", "--output", str(OUTPUT_DIR)]
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Stream output in real-time
        logger.info("Starting domain_enrichment.py process (this may take a while)...")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Print output as it comes in
        for line in process.stdout:
            print(line.strip())  # Print directly to ensure visibility
            logger.info(f"DOMAIN_ENRICHMENT: {line.strip()}")
        
        # Wait for process to finish
        return_code = process.wait()
        
        # Check if there was an error
        if return_code != 0:
            # Read error output
            stderr = process.stderr.read()
            logger.error(f"domain_enrichment.py failed with exit code {return_code}")
            logger.error(f"STDERR:\n{stderr}")
            return False
        
        # Verify that processed_AI.json was updated
        processed_ai_path = OUTPUT_DIR / "processed_AI.json"
        if not processed_ai_path.exists():
            logger.error(f"Failed to create/update {processed_ai_path}")
            return False
        
        try:
            with open(processed_ai_path, 'r') as f:
                data = json.load(f)
                entity_count = len(data.get('entities', []))
                logger.info(f"processed_AI.json now has {entity_count} entities")
        except Exception as e:
            logger.error(f"Error reading processed_AI.json: {e}")
            return False
        
        logger.info("domain_enrichment.py completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error running domain_enrichment.py: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function to coordinate AI processing workflow"""
    logger.info("====== STARTING AI PROCESSING WORKFLOW ======")
    
    # Check if OpenAI API key is available
    if not check_api_key():
        logger.warning("OpenAI API key not available. Processing may fail.")
    
    # Run the extract script
    if not run_extract_ai_fields():
        logger.error("Extract script failed. Aborting.")
        return False
    
    # Wait a moment to ensure files are written
    logger.info("Waiting 2 seconds before continuing...")
    time.sleep(2)
    
    # Run the enrichment script
    if not run_domain_enrichment():
        logger.error("Enrichment script failed")
        return False
    
    logger.info("====== AI PROCESSING WORKFLOW COMPLETED ======")
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
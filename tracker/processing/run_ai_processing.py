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
    level=logging.DEBUG,  # Set to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Force logs to stdout for GitHub Actions
    ]
)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description="AI Processing Coordinator")
parser.add_argument("--github", action="store_true", help="Run in GitHub Actions mode")
parser.add_argument("--debug", action="store_true", help="Run in debug mode with extra logging")
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
SCRIPTS_DIR = PROJECT_ROOT / "tracker" / "AI"  # Where scripts are located
OUTPUT_DIR = PROJECT_ROOT / "data" / "AI"      # Where to save output data
DEBUG_DIR = OUTPUT_DIR / "debug"               # Debug logs directory

logger.info(f"Scripts directory: {SCRIPTS_DIR}")
logger.info(f"Output directory: {OUTPUT_DIR}")

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

# Add a file logger for debug mode
debug_log_file = DEBUG_DIR / f"ai_processing_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(debug_log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
logging.getLogger().addHandler(file_handler)
logger.info(f"Added debug log file: {debug_log_file}")

# Log environment variables (masking sensitive ones)
if args.debug:
    logger.debug("Environment variables:")
    for key, value in os.environ.items():
        if 'KEY' in key or 'TOKEN' in key or 'SECRET' in key:
            # Mask sensitive values
            logger.debug(f"  {key}: {'*' * (len(value) if value else 0)}")
        else:
            logger.debug(f"  {key}: {value}")

def run_extract_ai_fields():
    """Run the extract_ai_fields.py script"""
    logger.info("Running extract_ai_fields.py...")
    
    try:
        script_path = SCRIPTS_DIR / "extract_ai_fields.py"
        logger.info(f"Extract script path: {script_path}")
        
        # Check if the script exists
        if not script_path.exists():
            logger.error(f"Script does not exist at {script_path}")
            return False
        
        # Run the script, passing the output directory as an argument
        cmd = [sys.executable, str(script_path), "--output", str(OUTPUT_DIR)]
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Log the full output
        logger.info(f"STDOUT: {result.stdout}")
        if result.stderr:
            logger.warning(f"STDERR: {result.stderr}")
            
        # Check if AI.json was created
        ai_json_path = OUTPUT_DIR / "AI.json"
        if ai_json_path.exists():
            try:
                with open(ai_json_path, 'r') as f:
                    data = json.load(f)
                    entity_count = len(data.get('entities', []))
                    logger.info(f"AI.json created successfully with {entity_count} entities")
            except Exception as e:
                logger.error(f"Error reading AI.json: {e}")
        else:
            logger.warning(f"AI.json not found at expected location: {ai_json_path}")
        
        logger.info("extract_ai_fields.py completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"extract_ai_fields.py failed: {e}")
        logger.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running extract_ai_fields.py: {e}")
        logger.error(traceback.format_exc())
        return False

def run_domain_enrichment():
    """Run the domain_enrichment.py script with --yes flag"""
    logger.info("Running domain_enrichment.py with --yes flag...")
    
    try:
        script_path = SCRIPTS_DIR / "domain_enrichment.py"
        logger.info(f"Enrichment script path: {script_path}")
        
        # Check if the script exists
        if not script_path.exists():
            logger.error(f"Script does not exist at {script_path}")
            return False
        
        # Check for OpenAI API key
        if not os.environ.get("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEY environment variable is not set")
            logger.info("Setting a dummy API key for testing purposes")
            os.environ["OPENAI_API_KEY"] = "DUMMY_KEY_FOR_TESTING_ONLY"
        else:
            logger.debug(f"OPENAI_API_KEY exists with length: {len(os.environ.get('OPENAI_API_KEY'))}")
        
        # Run the script with --yes and --debug flags
        cmd = [sys.executable, str(script_path), "--yes", "--debug", "--output", str(OUTPUT_DIR)]
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        logger.info("Starting domain_enrichment.py process...")
        
        # Use Popen to capture output in real-time
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Log output in real-time
        for line in process.stdout:
            logger.info(f"DOMAIN_ENRICHMENT: {line.strip()}")
        
        # Wait for process to complete and get return code
        return_code = process.wait()
        
        # Check for errors
        if return_code != 0:
            for line in process.stderr:
                logger.error(f"DOMAIN_ENRICHMENT ERROR: {line.strip()}")
            logger.error(f"domain_enrichment.py failed with return code {return_code}")
            return False
        
        # Check if processed_AI.json was created/updated
        processed_ai_path = OUTPUT_DIR / "processed_AI.json"
        if processed_ai_path.exists():
            try:
                with open(processed_ai_path, 'r') as f:
                    data = json.load(f)
                    entity_count = len(data.get('entities', []))
                    logger.info(f"processed_AI.json has {entity_count} entities")
            except Exception as e:
                logger.error(f"Error reading processed_AI.json: {e}")
        else:
            logger.warning(f"processed_AI.json not found at expected location: {processed_ai_path}")
        
        logger.info("domain_enrichment.py completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error running domain_enrichment.py: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function to coordinate AI processing workflow"""
    logger.info(f"Starting AI processing workflow (GitHub mode: {args.github})...")
    
    # Run the extract script
    if not run_extract_ai_fields():
        logger.error("Extract script failed")
        return False
    
    # Wait a bit to ensure files are written
    logger.info("Waiting 5 seconds before continuing...")
    time.sleep(5)
    
    # Run the enrichment script
    if not run_domain_enrichment():
        logger.error("Enrichment script failed")
        return False
    
    logger.info("AI processing workflow completed")
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
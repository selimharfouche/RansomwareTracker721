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

logger.info(f"Scripts directory: {SCRIPTS_DIR}")
logger.info(f"Output directory: {OUTPUT_DIR}")

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
        result = subprocess.run(
            [sys.executable, str(script_path), "--output", str(OUTPUT_DIR)],
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
        script_path = SCRIPTS_DIR / "domain_enrichment.py"
        logger.info(f"Enrichment script path: {script_path}")
        
        # Check if the script exists
        if not script_path.exists():
            logger.error(f"Script does not exist at {script_path}")
            return False
        
        # Run the script, passing both the --yes flag and output directory
        result = subprocess.run(
            [sys.executable, str(script_path), "--yes", "--output", str(OUTPUT_DIR)],
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
    
    logger.info("AI processing workflow completed")
    return True

if __name__ == "__main__":
    main()
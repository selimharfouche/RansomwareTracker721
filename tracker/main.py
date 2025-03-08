# tracker/main.py
import os
import time
import random
import datetime
import argparse
import sys
from pathlib import Path

# Add project root to path to allow importing from tracker modules
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.append(str(PROJECT_ROOT))

from tracker.utils.logging_utils import logger
from tracker.browser.tor_browser import setup_tor_browser, test_tor_connection
from tracker.scraper.generic_parser import GenericParser
from tracker.config.config_handler import ConfigHandler

# Define paths relative to project root
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config", "sites")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "output")
HTML_SNAPSHOTS_DIR = os.path.join(PROJECT_ROOT, "data", "html_snapshots")

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(HTML_SNAPSHOTS_DIR, exist_ok=True)

def get_random_wait_time(min_time=10, max_time=20):
    """Generate a random wait time to appear more human-like"""
    return random.uniform(min_time, max_time)

def process_site(driver, site_config):
    """Process a single site based on its configuration"""
    site_key = site_config.get('site_key', 'unknown')
    site_name = site_config.get('site_name', site_key)
    
    logger.info(f"Processing site: {site_name}")
    
    try:
        # Create generic parser for this site
        parser = GenericParser(driver, site_config, OUTPUT_DIR, HTML_SNAPSHOTS_DIR)
        
        # Scrape the site
        html_content = parser.scrape_site()
        
        if html_content:
            logger.info(f"Successfully captured {site_name} site content")
            return True
        else:
            logger.error(f"Failed to capture {site_name} site content")
            return False
    
    except Exception as e:
        logger.error(f"Error processing {site_name}: {e}")
        return False

def main(target_sites=None):
    """
    Main function to scrape multiple sites based on configuration files
    
    Args:
        target_sites (list): Optional list of site keys to process. If None, process all sites.
    """
    logger.info(f"Starting ransomware leak site tracker at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load site configurations
    config_handler = ConfigHandler(CONFIG_DIR)
    available_sites = config_handler.get_all_site_keys()
    
    if not available_sites:
        logger.error("No site configurations found. Please add configuration files to the config/sites directory.")
        return
    
    # If no specific sites requested, process all available sites
    if not target_sites:
        target_sites = available_sites
    else:
        # Validate requested sites
        for site_key in list(target_sites):  # Create a copy to modify during iteration
            if site_key not in available_sites:
                logger.error(f"Unknown site key: {site_key}. Skipping.")
                target_sites.remove(site_key)
    
    if not target_sites:
        logger.error("No valid sites to process. Exiting.")
        return
    
    logger.info(f"Will process these sites: {', '.join(target_sites)}")
    
    driver = None
    try:
        # Initialize Selenium with Tor
        logger.info("Setting up Tor browser...")
        driver = setup_tor_browser()
        
        # Test Tor connectivity
        if not test_tor_connection(driver):
            logger.error("Cannot connect to Tor. Make sure Tor is running on port 9050.")
            return
        
        # Process each requested site
        for site_key in target_sites:
            site_config = config_handler.get_site_config(site_key)
            if site_config:
                process_site(driver, site_config)
            else:
                logger.error(f"Configuration for site {site_key} not found or invalid")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
    finally:
        # Always close the browser properly
        if driver:
            driver.quit()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Ransomware leak site tracker")
    parser.add_argument('--sites', type=str, nargs='+', help='Specific sites to scrape (e.g., lockbit bashe)')
    args = parser.parse_args()
    
    # Run the main function
    main(args.sites)
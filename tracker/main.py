# tracker/main.py
import os
import time
import datetime
import argparse
import json
import sys
from pathlib import Path

# Add the project root to the path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.append(str(PROJECT_ROOT))

# Import Tor manager first
from tracker.utils.tor_manager import ensure_tor_running
from tracker.utils.logging_utils import logger
from tracker.utils.file_utils import load_json
from tracker.browser.tor_browser import setup_tor_browser, test_tor_connection
from tracker.scraper.generic_parser import GenericParser
from tracker.config.config_handler import ConfigHandler
# Import the processing functionality
from tracker.processing.process_entities import process_and_archive_entities

# Constants with relative paths
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config", "sites")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "output")
HTML_SNAPSHOTS_DIR = os.path.join(PROJECT_ROOT, "data", "html_snapshots")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(HTML_SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)  # Ensure logs directory exists for notification logs

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

def main(target_sites=None, skip_processing=False):
    """
    Main function to scrape multiple sites based on configuration files
    
    Args:
        target_sites (list): Optional list of site keys to process. If None, process all sites.
        skip_processing (bool): If True, skip entity processing after scraping
    """
    logger.info(f"Starting ransomware leak site tracker at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize tracking variables for the final notification
    sites_processed = []
    total_entities_found = 0
    new_entities_found = 0
    
    # Check if we're running in GitHub Actions
    in_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    
    if not in_github_actions:
        # Only try to start Tor if we're not in GitHub Actions
        if not ensure_tor_running():
            logger.error("Failed to start Tor. Exiting.")
            return
    else:
        logger.info("Running in GitHub Actions environment. Assuming Tor is already running.")
        
        # Verify Telegram credentials are available in GitHub Actions
        if not os.environ.get('TELEGRAM_BOT_TOKEN') or not os.environ.get('TELEGRAM_CHANNEL_ID'):
            logger.warning("Telegram credentials not found in GitHub Actions environment. "
                          "Notifications may not work. Please add TELEGRAM_BOT_TOKEN and "
                          "TELEGRAM_CHANNEL_ID as repository secrets.")
    
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
        driver = setup_tor_browser(headless=in_github_actions)  # Use headless mode in GitHub Actions
        
        # Test Tor connectivity
        if not test_tor_connection(driver):
            logger.error("Cannot connect to Tor. Make sure Tor is running on port 9050.")
            return
        
        # Process each requested site
        for site_key in target_sites:
            site_config = config_handler.get_site_config(site_key)
            if site_config:
                # Add site to processed list for the notification
                site_name = site_config.get('site_name', site_key)
                sites_processed.append(site_name)
                
                # Process the site
                success = process_site(driver, site_config)
                
                # Count entities if successfully processed
                if success:
                    try:
                        # Get entity counts for this site
                        json_file = site_config.get("json_file", f"{site_key}_entities.json")
                        entity_data = load_json(json_file, OUTPUT_DIR)
                        site_total = len(entity_data.get('entities', []))
                        total_entities_found += site_total
                        
                        # Try to count new entities from the central file
                        new_entities_file = os.path.join(OUTPUT_DIR, "new_entities.json")
                        if os.path.exists(new_entities_file):
                            with open(new_entities_file, 'r') as f:
                                new_entities_data = json.load(f)
                                new_entities = [e for e in new_entities_data.get('entities', []) 
                                              if e.get('group_key') == site_key]
                                new_entities_found += len(new_entities)
                    except Exception as e:
                        logger.error(f"Error counting entities for site {site_key}: {e}")
            else:
                logger.error(f"Configuration for site {site_key} not found or invalid")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
    finally:
        # Always close the browser properly
        if driver:
            driver.quit()
        
        # Send completion notification
        try:
            # Import the notifier dynamically to avoid module import issues
            # Note: The notifier module will handle environment differences internally
            from tracker.telegram_bot.notifier import send_scan_completion_notification
            
            logger.info("Sending scan completion notification...")
            send_scan_completion_notification(sites_processed, total_entities_found, new_entities_found)
            logger.info("Scan completion notification sent successfully")
        except ImportError as e:
            logger.error(f"Failed to import telegram notifier module: {e}")
            logger.info("If you want to use Telegram notifications, make sure 'requests' is installed")
            logger.info("For local development, also install 'python-dotenv'")
        except Exception as e:
            logger.error(f"Failed to send scan completion notification: {e}")
        
        # Process entities if not skipped
        if not skip_processing:
            try:
                logger.info("Starting entity processing and archiving...")
                success = process_and_archive_entities()
                if success:
                    logger.info("Entity processing and archiving completed successfully")
                else:
                    logger.error("Entity processing and archiving failed")
            except Exception as e:
                logger.error(f"Error during entity processing: {e}")
        else:
            logger.info("Entity processing skipped (--no-process flag was used)")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Ransomware leak site tracker")
    parser.add_argument('--sites', type=str, nargs='+', help='Specific sites to scrape (e.g., lockbit bashe)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--no-process', action='store_true', help='Skip entity processing after scraping')
    args = parser.parse_args()
    
    # Run the main function with the parsed arguments
    main(args.sites, args.no_process)
# tracker/main.py
import os
import time
import datetime
import argparse
import json
import sys
import subprocess
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

# Constants with relative paths
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config", "sites")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "output")
PER_GROUP_DIR = os.path.join(OUTPUT_DIR, "per_group")  # New directory for per-group files
HTML_SNAPSHOTS_DIR = os.path.join(PROJECT_ROOT, "data", "snapshots", "html_snapshots")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PER_GROUP_DIR, exist_ok=True)  # Create per_group directory
os.makedirs(HTML_SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def override_config(config, override_options):
    """
    Override configuration values with command-line specified options.
    
    Args:
        config: Original config dictionary to be modified
        override_options: List of strings in format "key.subkey=value"
    
    Returns:
        Modified config dictionary
    """
    if not override_options:
        return config
    
    for option in override_options:
        # Split the option into key path and value
        if '=' not in option:
            logger.warning(f"Invalid config override format: {option}. Should be key.subkey=value")
            continue
            
        key_path, value_str = option.split('=', 1)
        
        # Convert the value to appropriate type (bool, int, float, or string)
        if value_str.lower() == 'true':
            value = True
        elif value_str.lower() == 'false':
            value = False
        elif value_str.isdigit():
            value = int(value_str)
        elif all(c.isdigit() or c == '.' for c in value_str) and value_str.count('.') == 1:
            value = float(value_str)
        else:
            value = value_str
        
        # Apply the override by traversing the config dictionary
        keys = key_path.split('.')
        current = config
        
        # Navigate through nested dictionaries to the parent of the target key
        for i, k in enumerate(keys[:-1]):
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value at the target key
        current[keys[-1]] = value
        logger.info(f"Overriding config value {key_path} = {value}")
    
    return config

def process_site(driver, site_config):
    """Process a single site based on its configuration"""
    site_key = site_config.get('site_key', 'unknown')
    site_name = site_config.get('site_name', site_key)
    
    logger.info(f"Processing site: {site_name}")
    
    try:
        # Create generic parser for this site
        # Pass both directories: OUTPUT_DIR for shared files, PER_GROUP_DIR for group-specific files
        parser = GenericParser(driver, site_config, OUTPUT_DIR, PER_GROUP_DIR, HTML_SNAPSHOTS_DIR)
        
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

def main(target_sites=None, skip_processing=False, disable_telegram=False, 
         browser_config_overrides=None, constant_monitoring=False):
    """
    Main function to scrape multiple sites based on configuration files
    
    Args:
        target_sites (list): Optional list of site keys to process. If None, process all sites.
        skip_processing (bool): If True, skip entity processing after scraping
        disable_telegram (bool): If True, disable all Telegram notifications
        browser_config_overrides (list): List of browser config overrides in format "key.subkey=value"
        constant_monitoring (bool): If True, only send notifications when new entities are found
                                   and trigger AI processing for new entities
    """
    logger.info(f"Starting ransomware leak site tracker at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Constant monitoring mode: {constant_monitoring}")
    
    # Set target_sites in environment if specified for site filtering
    if target_sites:
        os.environ["TARGET_SITES"] = ",".join(target_sites)
        logger.info(f"Set TARGET_SITES environment variable: {os.environ['TARGET_SITES']}")
    
    # Set browser config overrides in environment
    if browser_config_overrides:
        for override in browser_config_overrides:
            if '=' in override:
                key_path, value = override.split('=', 1)
                env_key = "BROWSER_" + key_path.upper().replace('.', '_')
                os.environ[env_key] = value
                logger.info(f"Set environment variable {env_key}={value}")
    
    # Check for new_entities.json to see if it exists and has content
    new_entities_file = os.path.join(OUTPUT_DIR, "new_entities.json")
    had_new_entities_file = os.path.exists(new_entities_file)
    if had_new_entities_file:
        try:
            with open(new_entities_file, 'r') as f:
                new_entities_data = json.load(f)
                initial_entities_count = len(new_entities_data.get('entities', []))
                logger.info(f"Initial new_entities.json has {initial_entities_count} entities")
        except Exception as e:
            logger.error(f"Error reading new_entities.json: {e}")
            initial_entities_count = 0
    else:
        initial_entities_count = 0
        logger.info("No new_entities.json file found initially")
                
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
        
        # Verify Telegram credentials are available in GitHub Actions if notifications are enabled
        if not disable_telegram and (not os.environ.get('TELEGRAM_BOT_TOKEN') or not os.environ.get('TELEGRAM_CHANNEL_ID')):
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
        # Already filtered by ConfigHandler using TARGET_SITES environment variable
        # But log for visibility
        logger.info(f"Processing specific sites: {target_sites}")
        
        # Validate requested sites exist in the available sites
        for site_key in list(target_sites):  # Create a copy to modify during iteration
            if site_key not in available_sites:
                logger.error(f"Unknown site key: {site_key}. Skipping.")
                target_sites.remove(site_key)
    
    if not target_sites:
        logger.error("No valid sites to process. Exiting.")
        return
    
    logger.info(f"Will process these sites: {', '.join(target_sites)}")
    
    # Set Telegram notification state in environment
    # In constant_monitoring mode, we'll decide later if we want to send notifications
    if constant_monitoring:
        logger.info("Constant monitoring mode: Telegram notifications will only be sent for new entities")
        os.environ['DISABLE_TELEGRAM'] = 'true'  # Start with disabled
    elif disable_telegram:
        logger.info("Telegram notifications are disabled")
        os.environ['DISABLE_TELEGRAM'] = 'true'
    else:
        logger.info("Telegram notifications are enabled")
        os.environ['DISABLE_TELEGRAM'] = 'false'
    
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
                        # Get entity counts for this site - use PER_GROUP_DIR
                        json_file = site_config.get("json_file", f"{site_key}_entities.json")
                        entity_data = load_json(json_file, PER_GROUP_DIR)
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
        
        # In constant monitoring mode, check if we found new entities
        found_new_entities = False
        if constant_monitoring:
            # Check for new entities by comparing new_entities.json with its initial state
            if os.path.exists(new_entities_file):
                try:
                    with open(new_entities_file, 'r') as f:
                        new_entities_data = json.load(f)
                        current_entities_count = len(new_entities_data.get('entities', []))
                        
                    if current_entities_count > initial_entities_count:
                        found_new_entities = True
                        logger.info(f"Found {current_entities_count - initial_entities_count} new entities")
                        
                        # Enable Telegram notifications for the scan completion
                        os.environ['DISABLE_TELEGRAM'] = 'false'
                except Exception as e:
                    logger.error(f"Error reading new_entities.json: {e}")
        
        # Send completion notification if Telegram is enabled
        if not disable_telegram and (not constant_monitoring or found_new_entities):
            try:
                # Import the notifier dynamically to avoid module import issues
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
        else:
            if constant_monitoring and not found_new_entities:
                logger.info("No new entities found, skipping completion notification in constant monitoring mode")
            else:
                logger.info("Skipping scan completion notification (Telegram notifications disabled)")
        
        # Process entities if not skipped
        if not skip_processing:
            try:
                logger.info("Starting entity processing and archiving...")
                # Import process_entities function here to avoid circular imports
                from tracker.processing.process_entities import process_and_archive_entities
                success = process_and_archive_entities()
                if success:
                    logger.info("Entity processing and archiving completed successfully")
                else:
                    logger.error("Entity processing and archiving failed")
            except Exception as e:
                logger.error(f"Error during entity processing: {e}")
        else:
            logger.info("Entity processing skipped (--no-process flag was used)")
            
        # In constant monitoring mode, run AI processing if new entities were found
        if constant_monitoring and found_new_entities:
            logger.info("New entities found in constant monitoring mode, running AI processing...")
            logger.info("AI processing will be executed by separate workflow")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Ransomware leak site tracker")
    parser.add_argument('--sites', type=str, nargs='+', help='Specific sites to scrape (e.g., lockbit bashe)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--no-process', action='store_true', help='Skip entity processing after scraping')
    parser.add_argument('--no-telegram', action='store_true', help='Disable Telegram notifications')
    parser.add_argument('--constant-monitoring', action='store_true', 
                       help='Only send notifications for new entities and run AI processing when new entities are found')
    
    # Configuration override arguments - only browser config is available now
    parser.add_argument('--browser-config', type=str, nargs='+', 
                       help='Override browser config values (e.g., timing.min_wait_time=15)')
    
    args = parser.parse_args()
    
    # Run the main function with the parsed arguments
    main(args.sites, args.no_process, args.no_telegram, args.browser_config, args.constant_monitoring)

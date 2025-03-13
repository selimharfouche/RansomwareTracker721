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
from tracker.browser.tor_browser import (
    load_browser_config, load_proxy_config, load_scraping_config,
    save_config_file, setup_tor_browser, test_tor_connection
)
from tracker.scraper.generic_parser import GenericParser
from tracker.config.config_handler import ConfigHandler

# Constants with relative paths
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config", "sites")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "output")
PER_GROUP_DIR = os.path.join(OUTPUT_DIR, "per_group")  # Directory for per-group files
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
    
    has_changes = False
    
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
        if keys[-1] not in current or current[keys[-1]] != value:
            current[keys[-1]] = value
            has_changes = True
            logger.info(f"Overriding config value {key_path} = {value}")
    
    return config, has_changes

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
         browser_config_overrides=None, proxy_config_overrides=None, scraping_config_overrides=None,
         use_last_config=False):
    """
    Main function to scrape multiple sites based on configuration files
    
    Args:
        target_sites (list): Optional list of site keys to process. If None, process all sites.
        skip_processing (bool): If True, skip entity processing after scraping
        disable_telegram (bool): If True, disable all Telegram notifications
        browser_config_overrides (list): List of browser config overrides in format "key.subkey=value"
        proxy_config_overrides (list): List of proxy config overrides in format "key.subkey=value"
        scraping_config_overrides (list): List of scraping config overrides in format "key.subkey=value"
        use_last_config (bool): If True, load the last saved configuration
    """
    logger.info(f"Starting ransomware leak site tracker at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ===== Handle configuration loading and overrides =====
    
    # If using last config, we'll pass this to setup_tor_browser later
    # Otherwise, apply any configuration overrides and save them
    if not use_last_config:
        # Apply browser configuration overrides if provided
        if browser_config_overrides:
            # Load the browser configuration directly
            browser_config = load_browser_config()
            browser_config, has_changes = override_config(browser_config, browser_config_overrides)
            
            # Save the modified config if changes were made
            if has_changes:
                save_config_file(browser_config, "browser")
                logger.info(f"Applied and saved browser configuration overrides: {browser_config_overrides}")
        
        # Apply proxy configuration overrides if provided
        if proxy_config_overrides:
            # Load and override proxy configuration
            proxy_config = load_proxy_config()
            proxy_config, has_changes = override_config(proxy_config, proxy_config_overrides)
            
            # Save the modified config if changes were made
            if has_changes:
                save_config_file(proxy_config, "proxy")
                logger.info(f"Applied and saved proxy configuration overrides: {proxy_config_overrides}")
        
        # Apply scraping configuration overrides if provided
        if scraping_config_overrides:
            # Load and override scraping configuration
            scraping_config = load_scraping_config()
            scraping_config, has_changes = override_config(scraping_config, scraping_config_overrides)
            
            # Save the modified config if changes were made
            if has_changes:
                save_config_file(scraping_config, "scraping")
                logger.info(f"Applied and saved scraping configuration overrides: {scraping_config_overrides}")
    else:
        logger.info("Using last saved configuration")
    
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
        # Validate requested sites
        for site_key in list(target_sites):  # Create a copy to modify during iteration
            if site_key not in available_sites:
                logger.error(f"Unknown site key: {site_key}. Skipping.")
                target_sites.remove(site_key)
    
    if not target_sites:
        logger.error("No valid sites to process. Exiting.")
        return
    
    logger.info(f"Will process these sites: {', '.join(target_sites)}")
    
    # Set Telegram notification state in environment
    if disable_telegram:
        logger.info("Telegram notifications are disabled")
        os.environ['DISABLE_TELEGRAM'] = 'true'
    else:
        logger.info("Telegram notifications are enabled")
        os.environ['DISABLE_TELEGRAM'] = 'false'
    
    driver = None
    try:
        # Initialize Selenium with Tor, using last config if specified
        logger.info("Setting up Tor browser...")
        driver = setup_tor_browser(headless=in_github_actions, use_last_config=use_last_config)
        
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
        
        # Send completion notification if Telegram is enabled
        if not disable_telegram:
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

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Ransomware leak site tracker")
    parser.add_argument('--sites', type=str, nargs='+', help='Specific sites to scrape (e.g., lockbit bashe)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--no-process', action='store_true', help='Skip entity processing after scraping')
    parser.add_argument('--no-telegram', action='store_true', help='Disable Telegram notifications')
    
    # Configuration override arguments
    parser.add_argument('--browser-config', type=str, nargs='+', 
                       help='Override browser config values (e.g., timing.min_wait_time=15)')
    parser.add_argument('--proxy-config', type=str, nargs='+', 
                       help='Override proxy config values (e.g., proxy.port=9051)')
    parser.add_argument('--scraping-config', type=str, nargs='+', 
                       help='Override scraping config values (e.g., snapshots.save_html=true)')
    
    # Add the last-config flag
    parser.add_argument('--last-config', action='store_true', 
                       help='Use the last saved configuration instead of the default')
    
    args = parser.parse_args()
    
    # Run the main function with the parsed arguments
    main(args.sites, args.no_process, args.no_telegram, 
         args.browser_config, args.proxy_config, args.scraping_config,
         args.last_config)
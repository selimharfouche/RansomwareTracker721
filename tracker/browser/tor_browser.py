# tracker/browser/tor_browser.py
import time
import os
import datetime
import json
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from tracker.utils.logging_utils import logger

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
BROWSER_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "code", "browser_config.json")

def load_browser_config():
    """Load browser configuration from config file"""
    try:
        if not os.path.exists(BROWSER_CONFIG_PATH):
            logger.warning(f"Browser config file not found at {BROWSER_CONFIG_PATH}. Using default values.")
            return {
                "timing": {
                    "min_wait_time": 10,
                    "max_wait_time": 20,
                    "tor_check_wait_time": 3,
                    "page_load_timeout": 120
                },
                "anti_bot": {
                    "enabled": True,
                    "randomize_timing": True
                },
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"
            }
        
        with open(BROWSER_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading browser config: {e}. Using default values.")
        return {
            "timing": {
                "min_wait_time": 10,
                "max_wait_time": 20,
                "tor_check_wait_time": 3,
                "page_load_timeout": 120
            },
            "anti_bot": {
                "enabled": True,
                "randomize_timing": True
            },
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"
        }

# Load browser configuration
BROWSER_CONFIG = load_browser_config()

def setup_tor_browser(headless=False):
    """Configure Firefox to use Tor"""
    options = Options()
    options.set_preference('network.proxy.type', 1)
    options.set_preference('network.proxy.socks', '127.0.0.1')
    options.set_preference('network.proxy.socks_port', 9050)
    options.set_preference('network.proxy.socks_remote_dns', True)
    
    # Get user agent from config
    user_agent = BROWSER_CONFIG.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0")
    
    # Additional settings to make us look more like a normal browser
    options.set_preference('general.useragent.override', user_agent)
    options.set_preference('javascript.enabled', True)
    options.set_preference('dom.webnotifications.enabled', False)
    options.set_preference('app.shield.optoutstudies.enabled', False)
    
    # Prevent popup notifications that might interfere with scraping
    options.set_preference('dom.popup_allowed_events', '')
    
    # Headless mode for production
    if headless:
        options.add_argument("--headless")
    
    # Create the driver
    driver = webdriver.Firefox(options=options)
    
    # Set page load timeout from config
    page_load_timeout = BROWSER_CONFIG.get("timing", {}).get("page_load_timeout", 120)
    driver.set_page_load_timeout(page_load_timeout)
    
    return driver

def test_tor_connection(driver):
    """Test if we can connect through Tor"""
    try:
        driver.get('https://check.torproject.org/')
        
        # Get wait time from config
        tor_check_wait_time = BROWSER_CONFIG.get("timing", {}).get("tor_check_wait_time", 3)
        time.sleep(tor_check_wait_time)  # Give page time to load
        
        if "Congratulations" in driver.page_source:
            logger.info("Successfully connected to Tor!")
            return True
        else:
            logger.warning("Connected to the site, but not through Tor")
            return False
    except Exception as e:
        logger.error(f"Failed to connect to Tor: {e}")
        return False

def get_wait_time():
    """Get a wait time based on configuration settings"""
    timing_config = BROWSER_CONFIG.get("timing", {})
    anti_bot_config = BROWSER_CONFIG.get("anti_bot", {})
    
    min_wait_time = timing_config.get("min_wait_time", 10)
    max_wait_time = timing_config.get("max_wait_time", 20)
    
    if anti_bot_config.get("enabled", True) and anti_bot_config.get("randomize_timing", True):
        return random.uniform(min_wait_time, max_wait_time)
    else:
        return min_wait_time

def browse_with_selenium(driver, url, site_config, wait_time=None):
    """Browse to a URL with Selenium, handling anti-bot measures"""
    site_name = site_config.get('site_name', 'Unknown')
    site_verification = site_config.get('site_verification', {})
    verification_type = site_verification.get('type', 'text')
    verification_value = site_verification.get('value', '')
    
    # Use configured wait time if not specified
    if wait_time is None:
        wait_time = get_wait_time()
    
    try:
        logger.info(f"Navigating to {url}...")
        driver.get(url)
        
        # Only wait if anti-bot measures are enabled
        if BROWSER_CONFIG.get("anti_bot", {}).get("enabled", True):
            logger.info(f"Waiting {wait_time:.2f} seconds for anti-bot measures...")
            time.sleep(wait_time)
        
        # Check if the page has content we expect based on verification type
        if verification_type == 'text':
            if verification_value not in driver.page_source:
                logger.warning(f"Text '{verification_value}' not found in page for {site_name}, might not be the correct site")
                return None
        elif verification_type == 'class':
            if f'class="{verification_value}"' not in driver.page_source and f"class='{verification_value}'" not in driver.page_source:
                logger.warning(f"Class '{verification_value}' not found in page for {site_name}, might not be the correct site")
                return None
        elif verification_type == 'selector':
            from selenium.webdriver.common.by import By
            elements = driver.find_elements(By.CSS_SELECTOR, verification_value)
            if not elements:
                logger.warning(f"Selector '{verification_value}' not found in page for {site_name}, might not be the correct site")
                return None
        
        return driver.page_source
    
    except Exception as e:
        logger.error(f"Error visiting {url}: {e}")
        return None

def get_working_mirror(driver, site_config):
    """Try to connect to each mirror until finding one that works"""
    site_name = site_config.get('site_name', 'Unknown')
    mirrors = site_config.get('mirrors', [])
    
    for mirror in mirrors:
        url = f"http://{mirror}"
        logger.info(f"Trying {site_name} mirror: {mirror}")
        
        html_content = browse_with_selenium(driver, url, site_config)
        
        if html_content:
            logger.info(f"Successfully connected to {mirror}")
            return mirror, html_content
    
    logger.error(f"All {site_name} mirrors failed")
    return None, None

def save_html_snapshot(html_content, site_key, html_snapshots_dir):
    """Save HTML content to a timestamped file for analysis"""
    # Check if saving snapshots is enabled
    scraping_config = load_scraping_config()
    if not scraping_config.get("snapshots", {}).get("save_html", False):
        logger.info("HTML snapshot saving is disabled in configuration. Skipping.")
        return None
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    site_snapshot_dir = os.path.join(html_snapshots_dir, site_key)
    os.makedirs(site_snapshot_dir, exist_ok=True)
    
    html_filename = os.path.join(site_snapshot_dir, f"{site_key}_snapshot_{timestamp}.html")
    
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    logger.info(f"Raw HTML saved to {html_filename}")
    
    # Cleanup old snapshots if enabled
    if scraping_config.get("snapshots", {}).get("cleanup_old_snapshots", True):
        max_snapshots = scraping_config.get("snapshots", {}).get("max_snapshots_per_site", 5)
        cleanup_old_snapshots(site_snapshot_dir, max_snapshots)
    
    return html_filename

def cleanup_old_snapshots(snapshot_dir, max_keep=5):
    """Delete older snapshots to maintain only a fixed number of recent ones"""
    try:
        # List all snapshot files in the directory
        snapshot_files = [f for f in os.listdir(snapshot_dir) if f.endswith('.html')]
        
        # If we have more files than the max to keep
        if len(snapshot_files) > max_keep:
            # Sort by modification time (oldest first)
            snapshot_files.sort(key=lambda f: os.path.getmtime(os.path.join(snapshot_dir, f)))
            
            # Remove the oldest files
            for old_file in snapshot_files[:-max_keep]:
                os.remove(os.path.join(snapshot_dir, old_file))
                logger.info(f"Removed old snapshot: {old_file}")
    except Exception as e:
        logger.error(f"Error cleaning up old snapshots: {e}")

def load_scraping_config():
    """Load scraping configuration from config file"""
    PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
    SCRAPING_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "code", "scraping_config.json")
    
    try:
        if not os.path.exists(SCRAPING_CONFIG_PATH):
            logger.warning(f"Scraping config file not found at {SCRAPING_CONFIG_PATH}. Using default values.")
            return {
                "snapshots": {
                    "save_html": False,
                    "max_snapshots_per_site": 5,
                    "cleanup_old_snapshots": True
                }
            }
        
        with open(SCRAPING_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading scraping config: {e}. Using default values.")
        return {
            "snapshots": {
                "save_html": False,
                "max_snapshots_per_site": 5,
                "cleanup_old_snapshots": True
            }
        }
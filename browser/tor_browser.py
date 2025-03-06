# browser/tor_browser.py
import time
import os
import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from utils.logging_utils import logger
from config.settings import WAIT_TIME, HTML_SNAPSHOTS_DIR

def setup_tor_browser():
    """Configure Firefox to use Tor"""
    options = Options()
    options.set_preference('network.proxy.type', 1)
    options.set_preference('network.proxy.socks', '127.0.0.1')
    options.set_preference('network.proxy.socks_port', 9050)
    options.set_preference('network.proxy.socks_remote_dns', True)
    
    # Additional settings to make us look more like a normal browser
    options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0')
    options.set_preference('javascript.enabled', True)
    options.set_preference('dom.webnotifications.enabled', False)
    options.set_preference('app.shield.optoutstudies.enabled', False)
    
    # Prevent popup notifications that might interfere with scraping
    options.set_preference('dom.popup_allowed_events', '')
    
    # Uncomment the line below for headless mode (good for production)
    # options.add_argument("-headless")
    
    # Create the driver
    driver = webdriver.Firefox(options=options)
    driver.set_page_load_timeout(120)  # Longer timeout for onion sites
    
    return driver

def test_tor_connection(driver):
    """Test if we can connect through Tor"""
    try:
        driver.get('https://check.torproject.org/')
        time.sleep(3)  # Give page time to load
        if "Congratulations" in driver.page_source:
            logger.info("Successfully connected to Tor!")
            return True
        else:
            logger.warning("Connected to the site, but not through Tor")
            return False
    except Exception as e:
        logger.error(f"Failed to connect to Tor: {e}")
        return False

def browse_with_selenium(driver, url, site_identifier, wait_time=WAIT_TIME):
    """Browse to a URL with Selenium, handling waiting periods and anti-bot measures"""
    try:
        logger.info(f"Navigating to {url}...")
        driver.get(url)
        
        # Wait for initial page load to handle anti-bot measures
        logger.info(f"Waiting {wait_time} seconds for anti-bot measures...")
        time.sleep(wait_time)
        
        # Check if the page has content we expect - either by text or class identifiers
        if site_identifier.startswith(".") or site_identifier.startswith("#"):
            # This is a CSS selector
            elements = driver.find_elements_by_css_selector(site_identifier)
            if not elements:
                logger.warning(f"CSS selector '{site_identifier}' not found in page, might not be the correct site")
                return None
        elif "." in site_identifier and not site_identifier.startswith("."):
            # This looks like a CSS class but without the dot prefix
            if f'class="{site_identifier}"' not in driver.page_source and f"class='{site_identifier}'" not in driver.page_source:
                logger.warning(f"Class '{site_identifier}' not found in page, might not be the correct site")
                return None
        else:
            # This is regular text
            if site_identifier not in driver.page_source:
                logger.warning(f"'{site_identifier}' text not found in page, might not be the correct site")
                return None
        
        return driver.page_source
    
    except WebDriverException as e:
        logger.error(f"Browser error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error visiting {url}: {e}")
        return None

def get_working_mirror(driver, site_config):
    """Try to connect to each mirror until finding one that works"""
    site_name = site_config["name"]
    mirrors = site_config["mirrors"]
    site_identifier = site_config["identifier"]
    
    for mirror in mirrors:
        url = f"http://{mirror}"
        logger.info(f"Trying {site_name} mirror: {mirror}")
        
        html_content = browse_with_selenium(driver, url, site_identifier)
        
        if html_content and site_identifier in html_content:
            logger.info(f"Successfully connected to {mirror}")
            return mirror, html_content
    
    logger.error(f"All {site_name} mirrors failed")
    return None, None

def save_html_snapshot(html_content, site_name):
    """Save HTML content to a timestamped file for analysis"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    site_name_cleaned = site_name.lower().replace(" ", "_")
    
    # Create site-specific snapshot directory
    site_snapshot_dir = os.path.join(HTML_SNAPSHOTS_DIR, site_name_cleaned)
    os.makedirs(site_snapshot_dir, exist_ok=True)
    
    # Create filename
    html_filename = os.path.join(site_snapshot_dir, f"{site_name_cleaned}_snapshot_{timestamp}.html")
    
    # Save the raw HTML
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    logger.info(f"Raw HTML saved to {html_filename}")
    return html_filename
# browser/tor_browser.py
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from utils.logging_utils import logger
from config.settings import WAIT_TIME

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

def browse_with_selenium(driver, url, wait_time=WAIT_TIME):
    """Browse to a URL with Selenium, handling waiting periods and anti-bot measures"""
    try:
        logger.info(f"Navigating to {url}...")
        driver.get(url)
        
        # Wait for initial page load to handle anti-bot measures
        logger.info(f"Waiting {wait_time} seconds for anti-bot measures...")
        time.sleep(wait_time)
        
        # Check if the page has content we expect
        if "LockBit" not in driver.page_source:
            logger.warning("LockBit text not found in page, might not be the correct site")
            return None
        
        return driver.page_source
    
    except WebDriverException as e:
        logger.error(f"Browser error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error visiting {url}: {e}")
        return None
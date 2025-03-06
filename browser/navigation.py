# browser/navigation.py
import time
from selenium.common.exceptions import TimeoutException, WebDriverException
from utils.logging_utils import logger
from config.settings import WAIT_TIME

def browse_with_selenium(driver, url, wait_time=WAIT_TIME):
    """Browse to a URL with Selenium, handling waiting periods and potential anti-bot measures"""
    try:
        logger.info(f"Navigating to {url}...")
        driver.get(url)
        
        # First wait for initial page load
        logger.info(f"Waiting {wait_time} seconds for anti-bot measures...")
        time.sleep(wait_time)  # This wait helps with anti-bot measures
        
        # Check if the page has content we expect
        if "LockBit" not in driver.page_source:
            logger.warning("LockBit text not found in page, might not be the correct site")
            # Still proceed - maybe the structure changed
        
        # Return the page source after waiting
        return driver.page_source
    
    except WebDriverException as e:
        logger.error(f"Browser error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error visiting {url}: {e}")
        return None

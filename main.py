# main.py
import time
import datetime
from utils.logging_utils import logger
from browser.tor_browser import setup_tor_browser, test_tor_connection
from scraper.entities import scrape_all_entities, update_entities_database
from config.settings import LOCKBIT_MIRRORS, WAIT_TIME

def main():
    """Main function to scrape LockBit and update the entities database"""
    logger.info(f"Starting LockBit entity tracker at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    driver = None
    try:
        # Initialize Selenium with Tor
        logger.info("Setting up Tor browser...")
        driver = setup_tor_browser()
        
        # Test Tor connectivity
        if not test_tor_connection(driver):
            logger.error("Cannot connect to Tor. Make sure Tor is running on port 9050.")
            return
        
        # Connect to the site and save raw HTML for debugging
        for mirror in LOCKBIT_MIRRORS:
            url = f"http://{mirror}"
            logger.info(f"Trying LockBit mirror: {mirror}")
            
            try:
                driver.get(url)
                time.sleep(WAIT_TIME)  # Wait for the page to load
                
                if "LockBit" in driver.page_source:
                    logger.info(f"Successfully connected to {mirror}")
                    
                    # Save the raw HTML to a file for debugging
                    html_content = driver.page_source
                    with open("lockbit_raw_html.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                    
                    logger.info("Raw HTML saved to lockbit_raw_html.html")
                    break  # Exit the loop if we found a working mirror
                else:
                    logger.warning(f"Mirror {mirror} did not return LockBit content")
            except Exception as e:
                logger.error(f"Error accessing {mirror}: {e}")
        
        # Scrape all entities from the LockBit leak site
        logger.info("Scraping LockBit leak site for all entities...")
        entities = scrape_all_entities(driver)
        
        if not entities:
            logger.error("No entities found or error occurred while scraping")
            return
        
        # Update the entities database
        logger.info(f"Found {len(entities)} entities, updating database...")
        updated_db, added_count, updated_count = update_entities_database(entities)
        
        # Report results
        if added_count > 0 or updated_count > 0:
            logger.info(f"Successfully updated database: {added_count} new entities, {updated_count} field updates")
        else:
            logger.info("No changes detected in the entities list")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
    finally:
        # Always close the browser properly
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
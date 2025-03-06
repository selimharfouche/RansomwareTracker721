# main.py
import datetime
from utils.logging_utils import logger
from browser.tor_browser import setup_tor_browser, test_tor_connection
from scraper.entities import scrape_all_entities, update_entities_database

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
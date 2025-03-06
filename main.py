# main.py
import time
import datetime
import argparse
from utils.logging_utils import logger
from browser.tor_browser import setup_tor_browser, test_tor_connection
from scraper.lockbit_parser import LockBitParser
from scraper.bashe_parser import BasheParser
from config.settings import SITES

# Parser mapping - each site name maps to its parser class
PARSER_CLASSES = {
    "lockbit": LockBitParser,
    "bashe": BasheParser,
    # Add more parsers here as they're implemented
    # "blackcat": BlackCatParser,
    # "clop": ClopParser,
}

def main(target_sites=None):
    """
    Main function to scrape multiple sites and update their databases
    
    Args:
        target_sites (list): Optional list of site keys to process. If None, process all sites.
    """
    logger.info(f"Starting ransomware leak site tracker at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # If no specific sites requested, process all sites
    if not target_sites:
        target_sites = list(SITES.keys())
    
    # Validate requested sites
    for site_key in target_sites:
        if site_key not in SITES:
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
        
        # Process each site
        for site_key in target_sites:
            site_config = SITES[site_key]
            logger.info(f"Processing site: {site_config['name']}")
            
            # Get the appropriate parser class for this site
            if site_key in PARSER_CLASSES:
                parser_class = PARSER_CLASSES[site_key]
                parser = parser_class(driver, site_config)
                
                try:
                    # Scrape the site
                    html_content = parser.scrape_site()
                    
                    if html_content:
                        logger.info(f"Successfully captured {site_config['name']} site content")
                    else:
                        logger.error(f"Failed to capture {site_config['name']} site content")
                except Exception as e:
                    logger.error(f"Error processing {site_config['name']}: {e}")
            else:
                logger.warning(f"No parser implemented for {site_key}, skipping")
        
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
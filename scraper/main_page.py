# scraper/main_page.py
from bs4 import BeautifulSoup
from utils.logging_utils import logger
from browser.navigation import browse_with_selenium
from scraper.mirrors import get_working_mirrors, update_mirror_stats
from parsers.victim_parser import parse_victim_block

def scrape_lockbit_main_page(driver):
    """Scrape the main LockBit leak site to get victim information by trying multiple mirrors"""
    # Get previously working mirrors
    mirrors = get_working_mirrors()
    logger.info(f"Trying {len(mirrors)} potential mirrors")
    
    # Try each mirror
    for mirror in mirrors:
        try:
            # Use just the base mirror domain - the main page is the leaked data
            url = f"http://{mirror}"
            logger.info(f"Trying LockBit mirror: {mirror}")
            
            html_content = browse_with_selenium(driver, url)
            
            if not html_content:
                logger.warning(f"No content received from {mirror}")
                update_mirror_stats(mirror, success=False)
                continue
                
            # Check if we got actual content (not a redirect or error page)
            if "LockBit" not in html_content:
                logger.warning(f"Mirror {mirror} returned non-LockBit content")
                update_mirror_stats(mirror, success=False)
                continue
                
            logger.info(f"Successfully connected to {mirror}")
            update_mirror_stats(mirror, success=True)
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all victim entries
            victim_entries = []
            for entry in soup.select('a.post-block'):
                victim = parse_victim_block(entry)
                if victim and 'domain' in victim:
                    victim_entries.append(victim)
                    logger.info(f"Found victim: {victim['domain']}")
            
            if victim_entries:
                # The first 5 victims on the page are the most recent
                logger.info(f"Found {len(victim_entries)} total victims")
                return victim_entries[:5], mirror  # Return the 5 most recent victims and working mirror
            else:
                logger.warning(f"No victim entries found on {mirror}")
                
        except Exception as e:
            logger.warning(f"Mirror {mirror} failed: {e}")
            update_mirror_stats(mirror, success=False)
    
    logger.error("All LockBit mirrors failed")
    return None, None

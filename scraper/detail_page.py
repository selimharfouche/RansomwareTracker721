# scraper/detail_page.py
from bs4 import BeautifulSoup
from utils.logging_utils import logger
from browser.navigation import browse_with_selenium
from parsers.detail_parser import parse_victim_details

def get_victim_details(driver, detail_url, working_mirror):
    """Get detailed information about a victim from their specific page"""
    try:
        # Strip leading slash if present
        if detail_url.startswith('/'):
            detail_url = detail_url[1:]
        
        url = f"http://{working_mirror}/{detail_url}"
        html_content = browse_with_selenium(driver, url)
        
        if not html_content:
            logger.error(f"Could not fetch victim detail page: {detail_url}")
            return {}
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Use the more robust parsing function
        details = parse_victim_details(soup)
        
        return details
        
    except Exception as e:
        logger.error(f"Error getting victim details: {e}")
        return {}

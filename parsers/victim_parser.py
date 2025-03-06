# parsers/victim_parser.py
import re

def parse_victim_block(block):
    """Extract data from a victim block on the LockBit site"""
    victim = {}
    
    # Extract domain name
    domain_elem = block.select_one('.post-title')
    if domain_elem:
        victim['domain'] = domain_elem.text.strip()
    
    # Extract status (published or countdown)
    status_elem = block.select_one('.post-timer-end')
    if status_elem:
        victim['status'] = status_elem.text.strip().upper()
    
    # Extract description snippet
    desc_elem = block.select_one('.post-block-text')
    if desc_elem:
        # Get a preview of the description
        victim['description_preview'] = desc_elem.text.strip()[:200] + "..." if len(desc_elem.text.strip()) > 200 else desc_elem.text.strip()
    
    # Extract update timestamp - try multiple possible selectors
    time_elem = block.select_one('.updated-post-date span')
    if not time_elem:
        time_elem = block.select_one('.views .updated-post-date')
    
    if time_elem:
        # Clean up the timestamp text
        timestamp_text = time_elem.text.strip()
        # Remove any non-timestamp text
        if "Updated:" in timestamp_text:
            timestamp_text = timestamp_text.split("Updated:")[1].strip()
        victim['updated'] = timestamp_text
    
    # Extract view count - try multiple possible selectors
    views_elem = block.select_one('div[style*="opacity"] span[style*="font-weight: bold"]')
    if not views_elem:
        views_elem = block.select_one('.views span[style*="font-weight: bold"]')
    if not views_elem:
        views_elem = block.select_one('.views span[style*="font-size: 12px"]')
    
    if views_elem:
        try:
            # Clean up and extract just the number
            views_text = views_elem.text.strip()
            # Extract digits only
            digits = re.findall(r'\d+', views_text)
            if digits:
                victim['views'] = int(digits[0])
        except ValueError:
            victim['views'] = 0
    
    # Extract link to detailed page
    link_elem = block.get('href')
    if link_elem:
        victim['detail_link'] = link_elem
    
    return victim

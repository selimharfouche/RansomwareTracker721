# scraper/entities.py
import re
import datetime
from bs4 import BeautifulSoup
from utils.logging_utils import logger
from browser.tor_browser import browse_with_selenium
from utils.file_utils import load_json, save_json
from config.settings import LOCKBIT_MIRRORS, ENTITIES_JSON

def get_working_mirror(driver):
    """Try to connect to each mirror until finding one that works"""
    for mirror in LOCKBIT_MIRRORS:
        url = f"http://{mirror}"
        logger.info(f"Trying LockBit mirror: {mirror}")
        
        html_content = browse_with_selenium(driver, url)
        
        if html_content and "LockBit" in html_content:
            logger.info(f"Successfully connected to {mirror}")
            return mirror, html_content
    
    logger.error("All LockBit mirrors failed")
    return None, None

def parse_entity(entity_block):
    """Extract data from an entity block on the LockBit site"""
    entity = {}
    
    # Extract unique identifier from href
    post_id = entity_block.get('href')
    if post_id:
        # Strip leading slash if present
        if post_id.startswith('/'):
            post_id = post_id[1:]
        entity['id'] = post_id
    
    # Extract domain name
    domain_elem = entity_block.select_one('.post-title')
    if domain_elem:
        entity['domain'] = domain_elem.text.strip()
    
    # First check if there's a timer container
    timer_container = entity_block.select_one('.post-timer')
    if timer_container:
        # This entity has a timer, so it's in countdown status
        entity['status'] = 'countdown'
        
        # Extract the timer spans and parse their values
        days_span = entity_block.select_one('.timer .days')
        hours_span = entity_block.select_one('.timer .hours')
        minutes_span = entity_block.select_one('.timer .minutes')
        seconds_span = entity_block.select_one('.timer .seconds')
        
        countdown = {}
        
        if days_span:
            # Extract just the number from "10D" format
            days_text = days_span.text.strip()
            days_match = re.search(r'(\d+)', days_text)
            if days_match:
                countdown['days'] = int(days_match.group(1))
        
        if hours_span:
            # Extract just the number from "03h" format
            hours_text = hours_span.text.strip()
            hours_match = re.search(r'(\d+)', hours_text)
            if hours_match:
                countdown['hours'] = int(hours_match.group(1))
        
        if minutes_span:
            # Extract just the number from "21m" format
            minutes_text = minutes_span.text.strip()
            minutes_match = re.search(r'(\d+)', minutes_text)
            if minutes_match:
                countdown['minutes'] = int(minutes_match.group(1))
        
        if seconds_span:
            # Extract just the number from "20s" format
            seconds_text = seconds_span.text.strip()
            seconds_match = re.search(r'(\d+)', seconds_text)
            if seconds_match:
                countdown['seconds'] = int(seconds_match.group(1))
        
        if countdown:
            entity['countdown_remaining'] = countdown
            
            # Calculate and store the estimated end date based on current time + countdown
            if 'days' in countdown and 'hours' in countdown and 'minutes' in countdown and 'seconds' in countdown:
                current_time = datetime.datetime.now()
                delta = datetime.timedelta(
                    days=countdown.get('days', 0),
                    hours=countdown.get('hours', 0),
                    minutes=countdown.get('minutes', 0),
                    seconds=countdown.get('seconds', 0)
                )
                end_time = current_time + delta
                entity['estimated_publish_date'] = end_time.strftime("%Y-%m-%d %H:%M:%S UTC")
                
                # Log what we found
                logger.info(f"Countdown for {entity.get('domain')}: {countdown.get('days', 0)}d {countdown.get('hours', 0)}h {countdown.get('minutes', 0)}m {countdown.get('seconds', 0)}s")
                logger.info(f"Estimated publish date: {entity['estimated_publish_date']}")
    else:
        # No timer container found, check for published status
        status_elem = entity_block.select_one('.post-timer-end')
        if status_elem and "d-none" not in status_elem.get('class', []):
            entity['status'] = status_elem.text.strip().lower()
    
    # Extract description snippet
    desc_elem = entity_block.select_one('.post-block-text')
    if desc_elem:
        entity['description_preview'] = desc_elem.text.strip()
    
    # Extract update timestamp
    time_elem = entity_block.select_one('.updated-post-date span')
    if not time_elem:
        time_elem = entity_block.select_one('.views .updated-post-date')
    
    if time_elem:
        timestamp_text = time_elem.text.strip()
        if "Updated:" in timestamp_text:
            timestamp_text = timestamp_text.split("Updated:")[1].strip()
        entity['updated'] = timestamp_text
    
    # Extract view count
    views_elem = entity_block.select_one('div[style*="opacity"] span[style*="font-weight: bold"]')
    if not views_elem:
        views_elem = entity_block.select_one('.views span[style*="font-weight: bold"]')
    if not views_elem:
        views_elem = entity_block.select_one('.views span[style*="font-size: 12px"]')
    
    if views_elem:
        try:
            views_text = views_elem.text.strip()
            digits = re.findall(r'\d+', views_text)
            if digits:
                entity['views'] = int(digits[0])
        except ValueError:
            entity['views'] = 0
    
    # Extract class (good, bad, etc) if present
    entity_class = entity_block.get('class')
    if entity_class:
        for cls in entity_class:
            if cls not in ['post-block']:
                entity['class'] = cls
                break
    
    return entity

def scrape_all_entities(driver):
    """Scrape all entities from the main LockBit page"""
    working_mirror, html_content = get_working_mirror(driver)
    
    if not working_mirror or not html_content:
        logger.error("Failed to connect to any LockBit mirror")
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all entity blocks
    entity_blocks = soup.select('a.post-block')
    
    if not entity_blocks:
        logger.warning("No entity blocks found on the page")
        return None
    
    logger.info(f"Found {len(entity_blocks)} entity blocks")
    
    # Parse each entity block
    entities = []
    for block in entity_blocks:
        entity = parse_entity(block)
        if entity and 'id' in entity:
            entities.append(entity)
    
    return entities

def update_entities_database(new_entities):
    """Update the entities database with new information and track changes"""
    # Load existing entities if available
    existing_entities = load_json(ENTITIES_JSON)
    
    # Convert to dictionary for easier lookup
    entities_dict = {entity.get('id'): entity for entity in existing_entities.get('entities', [])}
    
    # Track changes
    added_count = 0
    updated_count = 0
    
    # Process new entities
    for entity in new_entities:
        entity_id = entity.get('id')
        if not entity_id:
            continue
        
        if entity_id not in entities_dict:
            # This is a new entity
            entity['first_seen'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            entities_dict[entity_id] = entity
            added_count += 1
            logger.info(f"New entity added: {entity.get('domain')}")
        else:
            # This is an existing entity, update its fields
            existing = entities_dict[entity_id]
            changed = False
            
            # Update fields except first_seen
            for key, value in entity.items():
                if key != 'first_seen':
                    if key not in existing or existing[key] != value:
                        existing[key] = value
                        changed = True
            
            if changed:
                updated_count += 1
                logger.info(f"Updated entity: {entity.get('domain')}")
    
    # Create updated database
    updated_db = {
        'entities': list(entities_dict.values()),
        'last_updated': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        'total_count': len(entities_dict)
    }
    
    # Save if there were changes
    if added_count > 0 or updated_count > 0:
        save_json(updated_db, ENTITIES_JSON)
        logger.info(f"Database updated with {added_count} new entities and {updated_count} field updates")
    else:
        logger.info("No changes detected, database remains unchanged")
    
    return updated_db, added_count, updated_count
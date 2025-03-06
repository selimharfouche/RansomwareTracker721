# scraper/bashe_parser.py
import re
import datetime
from bs4 import BeautifulSoup
from scraper.base_parser import BaseParser
from utils.logging_utils import logger

class BasheParser(BaseParser):
    """Parser for Bashe leak site"""
    
    def parse_entities(self, html_content):
        """Parse the HTML content to extract entities from Bashe site"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all entity segments
        entity_blocks = soup.select('div.segment.published, div.segment[class*="segment timer"]')
        
        if not entity_blocks:
            logger.warning(f"No entity blocks found on the {self.site_name} page")
            return None
        
        logger.info(f"Found {len(entity_blocks)} entity blocks on {self.site_name}")
        
        # Parse each entity block
        entities = []
        for block in entity_blocks:
            entity = self._parse_entity(block)
            if entity and 'id' in entity:
                entities.append(entity)
        
        return entities
    
    def _parse_entity(self, entity_block):
        """Extract data from an entity block on the Bashe site"""
        entity = {}
        
        # Extract unique identifier from onclick attribute
        onclick = entity_block.get('onclick', '')
        id_match = re.search(r'id=(\d+)', onclick)
        if id_match:
            entity['id'] = id_match.group(1)
        else:
            # Try to find it in a child element if not in the main block
            link_with_id = entity_block.select_one('[onclick*="id="]')
            if link_with_id:
                onclick = link_with_id.get('onclick', '')
                id_match = re.search(r'id=(\d+)', onclick)
                if id_match:
                    entity['id'] = id_match.group(1)
            
            if 'id' not in entity:
                logger.warning("Could not find entity ID, skipping")
                return None
        
        # Extract status
        status_elem = entity_block.select_one('.segment__block')
        if status_elem:
            status_text = status_elem.text.strip().lower()
            entity['status'] = status_text
        
        # Extract company/domain name
        domain_elem = entity_block.select_one('.segment__text__off')
        if domain_elem:
            entity['domain'] = domain_elem.text.strip()
        
        # Extract country
        country_elem = entity_block.select_one('.segment__country__deadline')
        if country_elem:
            entity['country'] = country_elem.text.strip()
        
        # Extract description
        desc_elem = entity_block.select_one('.segment__text__dsc')
        if desc_elem:
            entity['description_preview'] = desc_elem.text.strip()
        
        # Extract date and views
        date_elem = entity_block.select_one('.segment__date__deadline')
        if date_elem:
            date_text = date_elem.text.strip()
            
            # Parse date from format like: "2025/02/10 12:00:00 UTC +0 (views: 24823)"
            datetime_match = re.search(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})', date_text)
            if datetime_match:
                entity['updated'] = datetime_match.group(1)
            
            # Extract views
            views_match = re.search(r'views: (\d+)', date_text)
            if views_match:
                entity['views'] = int(views_match.group(1))
        
        # Check if it's a timer (countdown) or published
        if 'timer' in entity_block.get('class', []):
            entity['status'] = 'countdown'
            
            # For countdown entities, try to parse the timer
            timer_elem = entity_block.select_one('.timer')
            if timer_elem:
                # This would need to be adapted based on how the timer is structured in the HTML
                countdown = {}
                
                # Attempt to extract days, hours, minutes, seconds
                days_elem = timer_elem.select_one('.days')
                hours_elem = timer_elem.select_one('.hours')
                minutes_elem = timer_elem.select_one('.minutes')
                seconds_elem = timer_elem.select_one('.seconds')
                
                if days_elem:
                    days_match = re.search(r'(\d+)', days_elem.text.strip())
                    if days_match:
                        countdown['days'] = int(days_match.group(1))
                
                if hours_elem:
                    hours_match = re.search(r'(\d+)', hours_elem.text.strip())
                    if hours_match:
                        countdown['hours'] = int(hours_match.group(1))
                
                if minutes_elem:
                    minutes_match = re.search(r'(\d+)', minutes_elem.text.strip())
                    if minutes_match:
                        countdown['minutes'] = int(minutes_match.group(1))
                
                if seconds_elem:
                    seconds_match = re.search(r'(\d+)', seconds_elem.text.strip())
                    if seconds_match:
                        countdown['seconds'] = int(seconds_match.group(1))
                
                if countdown:
                    entity['countdown_remaining'] = countdown
                    
                    # Calculate estimated publish date if we have the components
                    if all(key in countdown for key in ['days', 'hours', 'minutes', 'seconds']):
                        current_time = datetime.datetime.now()
                        delta = datetime.timedelta(
                            days=countdown.get('days', 0),
                            hours=countdown.get('hours', 0),
                            minutes=countdown.get('minutes', 0),
                            seconds=countdown.get('seconds', 0)
                        )
                        end_time = current_time + delta
                        entity['estimated_publish_date'] = end_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return entity
# tracker/scraper/generic_parser.py
import re
import datetime
from bs4 import BeautifulSoup
from tracker.scraper.base_parser import BaseParser
from tracker.utils.logging_utils import logger

class GenericParser(BaseParser):
    """Generic parser that uses configuration to parse any site"""
    
    def __init__(self, driver, site_config, output_dir, html_snapshots_dir):
        """Initialize with site configuration"""
        super().__init__(driver, site_config, output_dir, html_snapshots_dir)
        # Extract parsing configuration
        self.parsing_config = site_config.get('parsing', {})
        self.entity_selector = self.parsing_config.get('entity_selector')
        self.field_configs = self.parsing_config.get('fields', [])
    
    def parse_entities(self, html_content):
        """Parse the HTML content to extract entities based on configuration"""
        if not self.entity_selector:
            logger.error(f"No entity selector defined for {self.site_name}")
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all entity blocks using the configured selector
        entity_blocks = soup.select(self.entity_selector)
        
        if not entity_blocks:
            logger.warning(f"No entity blocks found on {self.site_name} using selector: {self.entity_selector}")
            return None
        
        logger.info(f"Found {len(entity_blocks)} entity blocks on {self.site_name}")
        
        # Parse each entity block
        entities = []
        for block in entity_blocks:
            entity = self._parse_entity(block)
            if entity and 'id' in entity:
                entities.append(entity)
            else:
                logger.warning(f"Skipping entity without ID on {self.site_name}")
        
        return entities
    
    def _parse_entity(self, entity_block):
        """Parse an entity block based on field configurations"""
        entity = {}
        
        # Process each configured field
        for field_config in self.field_configs:
            field_name = field_config.get('name')
            field_type = field_config.get('type')
            
            if not field_name or not field_type:
                continue
            
            try:
                # Different handling based on field type
                if field_type == 'text':
                    self._extract_text_field(entity, entity_block, field_config)
                elif field_type == 'attribute':
                    self._extract_attribute_field(entity, entity_block, field_config)
                elif field_type == 'conditional':
                    self._extract_conditional_field(entity, entity_block, field_config)
                elif field_type == 'complex':
                    self._extract_complex_field(entity, entity_block, field_config)
            except Exception as e:
                is_optional = field_config.get('optional', False)
                if is_optional:
                    logger.debug(f"Error extracting optional field '{field_name}': {e}")
                else:
                    logger.warning(f"Error extracting field '{field_name}': {e}")
        
        # Add timestamp for countdown entities (for sites like LockBit)
        if 'status' in entity and entity['status'] == 'countdown' and 'countdown_remaining' in entity:
            countdown = entity['countdown_remaining']
            if all(key in countdown for key in ['days', 'hours', 'minutes', 'seconds']):
                try:
                    current_time = datetime.datetime.now()
                    delta = datetime.timedelta(
                        days=countdown.get('days', 0),
                        hours=countdown.get('hours', 0),
                        minutes=countdown.get('minutes', 0),
                        seconds=countdown.get('seconds', 0)
                    )
                    end_time = current_time + delta
                    entity['estimated_publish_date'] = end_time.strftime("%Y-%m-%d %H:%M:%S UTC")
                except Exception as e:
                    logger.warning(f"Error calculating estimated publish date: {e}")
        
        # Special handler for RansomHub's countdown format (e.g., "5D 21h 16m 8s")
        if 'status' in entity and entity['status'] == 'countdown' and 'countdown_remaining' in entity:
            countdown = entity['countdown_remaining']
            if 'countdown_text' in countdown:
                try:
                    countdown_text = countdown['countdown_text']
                    
                    # Extract days, hours, minutes, seconds using regex patterns
                    days = 0
                    hours = 0
                    minutes = 0
                    seconds = 0
                    
                    days_match = re.search(r'(\d+)D', countdown_text)
                    if days_match:
                        days = int(days_match.group(1))
                        
                    hours_match = re.search(r'(\d+)h', countdown_text)
                    if hours_match:
                        hours = int(hours_match.group(1))
                        
                    minutes_match = re.search(r'(\d+)m', countdown_text)
                    if minutes_match:
                        minutes = int(minutes_match.group(1))
                        
                    seconds_match = re.search(r'(\d+)s', countdown_text)
                    if seconds_match:
                        seconds = int(seconds_match.group(1))
                    
                    # Update countdown object with parsed values
                    countdown['days'] = days
                    countdown['hours'] = hours
                    countdown['minutes'] = minutes
                    countdown['seconds'] = seconds
                    
                    # Calculate the estimated publish date
                    current_time = datetime.datetime.now()
                    delta = datetime.timedelta(
                        days=days,
                        hours=hours,
                        minutes=minutes,
                        seconds=seconds
                    )
                    end_time = current_time + delta
                    entity['estimated_publish_date'] = end_time.strftime("%Y-%m-%d %H:%M:%S UTC")
                    
                    logger.info(f"Parsed RansomHub countdown: {countdown_text} → {entity['estimated_publish_date']}")
                except Exception as e:
                    logger.warning(f"Error parsing RansomHub countdown format: {e}")
        
        # For sites that provide an exact countdown date (like some other sites might)
        if 'status' in entity and entity['status'] == 'countdown' and 'countdown_date' in entity:
            try:
                countdown_date = entity['countdown_date']
                # Parse the date string (assuming YYYY-MM-DD HH:MM:SS format)
                date_obj = datetime.datetime.strptime(countdown_date, "%Y-%m-%d %H:%M:%S")
                # Format with UTC suffix
                entity['estimated_publish_date'] = date_obj.strftime("%Y-%m-%d %H:%M:%S UTC")
            except Exception as e:
                logger.warning(f"Error parsing countdown date: {e}")
        
        return entity
    
    def _extract_text_field(self, entity, entity_block, field_config):
        """Extract a text field from the entity block"""
        field_name = field_config['name']
        selector = field_config['selector']
        regex = field_config.get('regex')
        regex_group = field_config.get('regex_group', 0)
        convert = field_config.get('convert')
        
        # Check for condition if present
        condition = field_config.get('condition')
        if condition:
            cond_selector = condition.get('selector')
            cond_exists = condition.get('exists', True)
            
            # Handle 'self' selector for condition
            if cond_selector == 'self':
                element = entity_block
            else:
                element = entity_block.select_one(cond_selector)
            
            # Skip if condition not met
            if (cond_exists and not element) or (not cond_exists and element):
                return
        
        # Handle 'self' selector specially
        if selector == 'self':
            element = entity_block
        else:
            element = entity_block.select_one(selector)
        
        if not element:
            if not field_config.get('optional', False):
                logger.debug(f"Could not find element with selector '{selector}' for field '{field_name}'")
            return
        
        text = element.text.strip()
        
        # Apply regex if specified
        if regex and text:
            match = re.search(regex, text)
            if match and regex_group <= len(match.groups()):
                text = match.group(regex_group)
            else:
                if not field_config.get('optional', False):
                    logger.debug(f"Regex '{regex}' did not match for field '{field_name}'")
                return
        
        # Convert value if needed
        if convert == 'int':
            try:
                text = int(text)
            except ValueError:
                if not field_config.get('optional', False):
                    logger.debug(f"Could not convert value '{text}' to int for field '{field_name}'")
                return
        
        entity[field_name] = text
    
    def _extract_attribute_field(self, entity, entity_block, field_config):
        """Extract an attribute field from the entity block"""
        field_name = field_config['name']
        selector = field_config['selector']
        attribute = field_config['attribute']
        regex = field_config.get('regex')
        regex_group = field_config.get('regex_group', 0)
        
        # Handle 'self' selector specially
        if selector == 'self':
            element = entity_block
        else:
            element = entity_block.select_one(selector)
        
        if not element:
            if not field_config.get('optional', False):
                logger.debug(f"Could not find element with selector '{selector}' for field '{field_name}'")
            return
        
        value = element.get(attribute, '')
        
        # Apply regex if specified
        if regex and value:
            match = re.search(regex, value)
            if match and regex_group <= len(match.groups()):
                value = match.group(regex_group)
            else:
                if not field_config.get('optional', False):
                    logger.debug(f"Regex '{regex}' did not match for field '{field_name}'")
                return
        
        entity[field_name] = value
    
    def _extract_conditional_field(self, entity, entity_block, field_config):
        """Extract a conditional field based on element existence"""
        field_name = field_config['name']
        conditions = field_config.get('conditions', [])
        default_value = field_config.get('default')
        
        for condition in conditions:
            selector = condition['selector']
            exists = condition.get('exists', True)
            value = condition.get('value')
            
            # Handle 'self' and special selectors
            if selector == 'self':
                element = entity_block
            elif selector.startswith('self['):
                # Handle self with attributes like 'self[class*="timer"]'
                attr_name = re.search(r'self\[(.*?)=', selector)
                attr_value = re.search(r'="(.*?)"\]', selector)
                if attr_name and attr_value:
                    attr = attr_name.group(1)
                    val = attr_value.group(1)
                    attr_value = entity_block.get(attr, '')
                    element = entity_block if val in attr_value else None
                else:
                    element = None
            else:
                element = entity_block.select_one(selector)
            
            # Check if the element exists as expected
            if (exists and element) or (not exists and not element):
                entity[field_name] = value
                return
        
        # Use default value if no condition matched
        if default_value is not None:
            entity[field_name] = default_value
    
    def _extract_complex_field(self, entity, entity_block, field_config):
        """Extract a complex field with sub-fields"""
        field_name = field_config['name']
        condition = field_config.get('condition', {})
        sub_fields = field_config.get('fields', [])
        
        # Check condition first
        if condition:
            selector = condition.get('selector')
            exists = condition.get('exists', True)
            
            # Handle 'self' and special selectors
            if selector == 'self':
                element = entity_block
            elif selector.startswith('self['):
                # Handle self with attributes like 'self[class*="timer"]'
                attr_name = re.search(r'self\[(.*?)=', selector)
                attr_value = re.search(r'="(.*?)"\]', selector)
                if attr_name and attr_value:
                    attr = attr_name.group(1)
                    val = attr_value.group(1)
                    attr_value = entity_block.get(attr, '')
                    element = entity_block if val in attr_value else None
                else:
                    element = None
            else:
                element = entity_block.select_one(selector)
            
            if (exists and not element) or (not exists and element):
                return
        
        # Extract sub-fields into a nested object
        sub_entity = {}
        for sub_field in sub_fields:
            sub_field_name = sub_field.get('name')
            sub_field_type = sub_field.get('type')
            
            if not sub_field_name or not sub_field_type:
                continue
            
            try:
                # Different handling based on field type
                if sub_field_type == 'text':
                    self._extract_text_field(sub_entity, entity_block, sub_field)
                elif sub_field_type == 'attribute':
                    self._extract_attribute_field(sub_entity, entity_block, sub_field)
            except Exception as e:
                is_optional = sub_field.get('optional', False)
                if is_optional:
                    logger.debug(f"Error extracting optional sub-field '{sub_field_name}': {e}")
                else:
                    logger.warning(f"Error extracting sub-field '{sub_field_name}': {e}")
        
        # Only add the complex field if at least one sub-field was extracted
        if sub_entity:
            entity[field_name] = sub_entity
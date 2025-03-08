# scraper/base_parser.py
from abc import ABC, abstractmethod
import datetime
import json
import os
from utils.logging_utils import logger
from utils.file_utils import load_json, save_json
from browser.tor_browser import get_working_mirror, save_html_snapshot

class BaseParser(ABC):
    """Base class for all site parsers"""
    
    def __init__(self, driver, site_config, output_dir, html_snapshots_dir):
        self.driver = driver
        self.site_config = site_config
        self.site_name = site_config["name"] if "name" in site_config else site_config.get("site_name", "Unknown")
        self.site_key = site_config.get("site_key", "unknown")
        self.json_file = site_config.get("json_file", f"{self.site_key}_entities.json")
        self.output_dir = output_dir
        self.html_snapshots_dir = html_snapshots_dir
        self.new_entities_file = "new_entities.json"
    
    def scrape_site(self):
        """Connect to the site, save HTML snapshot, and extract entities"""
        working_mirror, html_content = get_working_mirror(self.driver, self.site_config)
        
        if not working_mirror or not html_content:
            logger.error(f"Failed to connect to any {self.site_name} mirror")
            return None
        
        # Save HTML snapshot for analysis
        html_file = save_html_snapshot(html_content, self.site_key, self.html_snapshots_dir)
        logger.info(f"Saved HTML snapshot to {html_file}")
        
        # Parse entities from HTML content
        entities = self.parse_entities(html_content)
        
        # Update database if entities were found
        if entities:
            logger.info(f"Found {len(entities)} entities on {self.site_name}")
            self.update_entities_database(entities)
        
        return html_content
    
    @abstractmethod
    def parse_entities(self, html_content):
        """Parse the HTML content to extract entities, must be implemented by subclasses"""
        pass
    
    def update_entities_database(self, new_entities):
        """Update the entities database with new information and track changes"""
        # Load existing entities if available
        existing_entities = load_json(self.json_file, self.output_dir)
        
        # Convert to dictionary for easier lookup
        entities_dict = {entity.get('id'): entity for entity in existing_entities.get('entities', [])}
        
        # Track changes
        added_count = 0
        updated_count = 0
        
        # Newly discovered entities to be added to the central tracking file
        newly_discovered = []
        
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
                logger.info(f"New entity added: {entity.get('domain', entity_id)}")
                
                # Add to newly discovered list with ransomware group attribution
                entity_copy = entity.copy()
                entity_copy['ransomware_group'] = self.site_name
                entity_copy['group_key'] = self.site_key
                newly_discovered.append(entity_copy)
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
                    logger.info(f"Updated entity: {entity.get('domain', entity_id)}")
        
        # Create updated database
        updated_db = {
            'entities': list(entities_dict.values()),
            'last_updated': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            'total_count': len(entities_dict)
        }
        
        # Save if there were changes
        if added_count > 0 or updated_count > 0:
            save_json(updated_db, self.json_file, self.output_dir)
            logger.info(f"Database updated with {added_count} new entities and {updated_count} field updates")
        else:
            logger.info("No changes detected, database remains unchanged")
        
        # Update the new_entities.json file if we discovered new entities
        if newly_discovered:
            self.update_new_entities_file(newly_discovered)
        
        return updated_db, added_count, updated_count
    
    def update_new_entities_file(self, newly_discovered):
        """Update the central new_entities.json file with newly discovered entities"""
        new_entities_path = os.path.join(self.output_dir, self.new_entities_file)
        
        # Load existing new entities file or create a new one
        try:
            if os.path.exists(new_entities_path):
                with open(new_entities_path, 'r') as f:
                    new_entities_db = json.load(f)
            else:
                new_entities_db = {
                    'entities': [],
                    'last_updated': '',
                    'total_count': 0
                }
        except Exception as e:
            logger.error(f"Error loading new entities file: {e}. Creating a new one.")
            new_entities_db = {
                'entities': [],
                'last_updated': '',
                'total_count': 0
            }
        
        # Get existing entities as a dictionary for quick lookup
        existing_ids = {entity.get('id'): True for entity in new_entities_db.get('entities', [])}
        
        # Add new entities if they don't already exist in the file
        added_to_file = 0
        for entity in newly_discovered:
            entity_id = entity.get('id')
            if entity_id and entity_id not in existing_ids:
                new_entities_db['entities'].append(entity)
                existing_ids[entity_id] = True
                added_to_file += 1
        
        # Update metadata
        if added_to_file > 0:
            new_entities_db['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            new_entities_db['total_count'] = len(new_entities_db['entities'])
            
            # Save the updated file
            try:
                # Ensure directory exists
                os.makedirs(self.output_dir, exist_ok=True)
                
                with open(new_entities_path, 'w') as f:
                    json.dump(new_entities_db, f, indent=4)
                
                logger.info(f"Added {added_to_file} new entities to the central tracking file")
            except Exception as e:
                logger.error(f"Error saving new entities file: {e}")
        else:
            logger.info("No new entities to add to the central tracking file")
# scraper/base_parser.py
from abc import ABC, abstractmethod
import datetime
import json
import os
import importlib
import shutil
from pathlib import Path
from utils.logging_utils import logger
from utils.file_utils import load_json, save_json
from browser.tor_browser import get_working_mirror, save_html_snapshot

# Define the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()

class BaseParser(ABC):
    """Base class for all site parsers"""
    
    def __init__(self, driver, site_config, output_dir, per_group_dir, html_snapshots_dir):
        """
        Initialize the base parser.
        
        Args:
            driver: Selenium WebDriver instance
            site_config: Configuration dictionary for the site
            output_dir: Directory for common/shared files (e.g., new_entities.json)
            per_group_dir: Directory for group-specific files (e.g., lockbit_entities.json)
            html_snapshots_dir: Directory for HTML snapshots
        """
        self.driver = driver
        self.site_config = site_config
        self.site_name = site_config["name"] if "name" in site_config else site_config.get("site_name", "Unknown")
        self.site_key = site_config.get("site_key", "unknown")
        self.json_file = site_config.get("json_file", f"{self.site_key}_entities.json")
        self.output_dir = output_dir  # For shared files
        self.per_group_dir = per_group_dir  # For group-specific files
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
        """
        Update the entities database with the newly scraped entities.
        This completely overwrites the existing file with new data.
        
        Args:
            new_entities: List of entities scraped from the site
        """
        # Load existing entities to identify which ones are truly new
        existing_entities = load_json(self.json_file, self.per_group_dir)  # Use per_group_dir for group files
        existing_dict = {entity.get('id'): entity for entity in existing_entities.get('entities', [])}
        
        # Create a completely new database with all current entities
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # List to track truly new entities for the new_entities.json file
        truly_new_entities = []
        
        # Process entities and preserve first_seen dates for existing ones
        for entity in new_entities:
            entity_id = entity.get('id')
            if not entity_id:
                continue
                
            # Check if this is a truly new entity
            if entity_id not in existing_dict:
                # This is a new entity, set first_seen to current time
                entity['first_seen'] = current_time
                logger.info(f"New entity discovered: {entity.get('domain', entity_id)}")
                
                # Add to the list of truly new entities with group attribution
                entity_copy = entity.copy()
                entity_copy['ransomware_group'] = self.site_name
                entity_copy['group_key'] = self.site_key
                truly_new_entities.append(entity_copy)
                
                # Send Telegram notification for new entity if not disabled
                if os.environ.get('DISABLE_TELEGRAM') != 'true':
                    try:
                        # Try to import the telegram notifier module
                        from tracker.telegram_bot.notifier import notify_new_entity
                        
                        # Send the notification
                        notify_new_entity(entity_copy, self.site_name)
                        logger.info(f"Telegram notification sent for {entity.get('domain', entity_id)}")
                    except ImportError:
                        logger.warning("Could not import telegram notifier. Notifications will not be sent.")
                        logger.warning("If you want notifications, ensure 'requests' is installed.")
                        logger.warning("For local development, also install 'python-dotenv'.")
                    except Exception as e:
                        logger.error(f"Failed to send Telegram notification: {e}")
                else:
                    logger.debug(f"Telegram notification skipped for {entity.get('domain', entity_id)} (notifications disabled)")
            else:
                # This is an existing entity, preserve its first_seen date
                entity['first_seen'] = existing_dict[entity_id].get('first_seen', current_time)
        
        # Create the complete updated database
        updated_db = {
            'entities': new_entities,
            'last_updated': current_time,
            'total_count': len(new_entities)
        }
        
        # Save the group-specific entity file to the per_group directory 
        save_json(updated_db, self.json_file, self.per_group_dir)  # Use per_group_dir for group files
        logger.info(f"Saved complete database with {len(new_entities)} entities to {os.path.join(self.per_group_dir, self.json_file)}")
        
        # Update the new_entities.json file if we discovered truly new entities
        if truly_new_entities:
            self.update_new_entities_file(truly_new_entities)
            
        return updated_db, len(truly_new_entities), len(new_entities)
    
    def update_new_entities_file(self, truly_new_entities):
        """
        Two-part approach for handling new entities:
        1. Save newly discovered entities to a timestamped file in the new_entities_snapshot directory
        2. Append these entities to the central new_entities.json file in the output directory
        
        If no new entities are found, no action is taken.
        
        Args:
            truly_new_entities: List of entities that are truly new (not seen before)
        """
        # Check if we have any new entities
        if not truly_new_entities:
            logger.info("No new entities found. No files will be created or updated.")
            return
        
        # 1. Save to snapshot directory with timestamped filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_dir = os.path.join(PROJECT_ROOT, "data", "snapshots", "new_entities_snapshot")
        os.makedirs(snapshot_dir, exist_ok=True)
        
        snapshot_filename = f"new_entities_{timestamp}.json"
        snapshot_path = os.path.join(snapshot_dir, snapshot_filename)
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        snapshot_db = {
            'entities': truly_new_entities,
            'last_updated': current_time,
            'total_count': len(truly_new_entities),
            'ransomware_group': self.site_name,
            'group_key': self.site_key
        }
        
        # Save the snapshot file
        try:
            with open(snapshot_path, 'w') as f:
                json.dump(snapshot_db, f, indent=4)
            logger.info(f"Created snapshot file {snapshot_filename} with {len(truly_new_entities)} new entities")
        except Exception as e:
            logger.error(f"Error saving snapshot file: {e}")
        
        # 2. Update the central new_entities.json file by appending the new entities
        # Important: Use self.output_dir (not per_group_dir) for the central file
        central_file = self.new_entities_file
        central_path = os.path.join(self.output_dir, central_file)  # Use main output_dir, not per_group
        
        try:
            # Load existing central file or create a new one
            if os.path.exists(central_path):
                with open(central_path, 'r') as f:
                    central_db = json.load(f)
                
                # Get existing entities as a dictionary for deduplication
                existing_ids = {entity.get('id'): True for entity in central_db.get('entities', [])}
                
                # Append new entities, avoiding duplicates
                for entity in truly_new_entities:
                    entity_id = entity.get('id')
                    if entity_id and entity_id not in existing_ids:
                        central_db['entities'].append(entity)
                        existing_ids[entity_id] = True
                
                # Update metadata
                central_db['last_updated'] = current_time
                central_db['total_count'] = len(central_db['entities'])
            else:
                # Create new central file with the same content as the snapshot
                central_db = {
                    'entities': truly_new_entities,
                    'last_updated': current_time,
                    'total_count': len(truly_new_entities)
                }
            
            # Save the updated central file to the MAIN output directory
            with open(central_path, 'w') as f:
                json.dump(central_db, f, indent=4)
            
            logger.info(f"Updated central {central_file} with {len(truly_new_entities)} new entities")
        except Exception as e:
            logger.error(f"Error updating central file: {e}")
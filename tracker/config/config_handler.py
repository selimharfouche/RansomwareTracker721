# config/config_handler.py
import os
import json
import glob
from utils.logging_utils import logger

class ConfigHandler:
    """Handler for site configuration files"""
    
    def __init__(self, config_dir):
        """Initialize with the directory containing site configs"""
        self.config_dir = config_dir
        self.site_configs = {}
        self.load_all_configs()
    
    def load_all_configs(self):
        """Load all JSON configuration files from the config directory"""
        pattern = os.path.join(self.config_dir, "*.json")
        config_files = glob.glob(pattern)
        
        if not config_files:
            logger.warning(f"No configuration files found in {self.config_dir}")
            return
        
        # Check if we should only load specific sites
        target_sites_env = os.environ.get("TARGET_SITES")
        target_sites = target_sites_env.split(",") if target_sites_env else None
        
        if target_sites:
            logger.info(f"Filtering site configurations to: {target_sites}")
        
        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Make sure the config has a site_key
                if 'site_key' not in config:
                    filename = os.path.basename(config_file)
                    logger.warning(f"Configuration file {filename} missing 'site_key', skipping")
                    continue
                
                site_key = config['site_key']
                
                # Skip sites not in target_sites if filtering is enabled
                if target_sites and site_key not in target_sites:
                    logger.info(f"Skipping site {site_key} (not in target sites)")
                    continue
                
                self.site_configs[site_key] = config
                logger.info(f"Loaded configuration for site: {config.get('site_name', site_key)}")
            
            except json.JSONDecodeError:
                filename = os.path.basename(config_file)
                logger.error(f"Error parsing JSON in {filename}, skipping")
            except Exception as e:
                filename = os.path.basename(config_file)
                logger.error(f"Error loading config from {filename}: {e}")
    
    def get_site_config(self, site_key):
        """Get configuration for a specific site"""
        return self.site_configs.get(site_key)
    
    def get_all_site_keys(self):
        """Get list of all available site keys"""
        return list(self.site_configs.keys())
    
    def get_all_site_configs(self):
        """Get all site configurations"""
        return self.site_configs
    
    def save_site_config(self, config):
        """Save a site configuration to file"""
        if 'site_key' not in config:
            logger.error("Cannot save configuration without 'site_key'")
            return False
        
        site_key = config['site_key']
        filename = f"{site_key}.json"
        file_path = os.path.join(self.config_dir, filename)
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Update in-memory config
            self.site_configs[site_key] = config
            logger.info(f"Saved configuration for site: {config.get('site_name', site_key)}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving config for {site_key}: {e}")
            return False
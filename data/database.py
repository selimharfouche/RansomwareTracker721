# data/database.py
import datetime
from config.settings import HISTORY_FILE
from utils.logging_utils import logger
from utils.file_utils import load_json, save_json

def update_victim_database(victims, history_file=HISTORY_FILE):
    """Update the victim database with new information and track changes"""
    # Load existing history if available
    history = load_json(history_file) or []
    
    # Create a dictionary of existing victims by domain for easy lookup
    existing_victims = {victim['domain']: victim for victim in history if 'domain' in victim}
    
    # Track changes for reporting
    new_victims = []
    updated_victims = []
    
    # Process current victims
    for victim in victims:
        domain = victim.get('domain')
        if not domain:
            continue
            
        if domain not in existing_victims:
            # This is a new victim
            victim['first_seen'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            history.append(victim)
            new_victims.append(domain)
            logger.info(f"New victim added: {domain}")
        else:
            # This is an existing victim, check for updates
            existing = existing_victims[domain]
            
            # Check if status changed
            if victim.get('status') != existing.get('status'):
                existing['status_history'] = existing.get('status_history', [])
                existing['status_history'].append({
                    'status': existing.get('status'),
                    'timestamp': existing.get('updated')
                })
                existing['status'] = victim.get('status')
                updated_victims.append(domain)
                logger.info(f"Status updated for {domain}: {victim.get('status')}")
            
            # Update other fields
            for key, value in victim.items():
                if key != 'first_seen' and key != 'status_history':
                    existing[key] = value
    
    # Save the updated history
    save_json(history, history_file)
    
    return history, new_victims, updated_victims

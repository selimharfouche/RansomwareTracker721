# tracker/telegram_bot/notifier.py
import os
import logging
import requests
import json
from datetime import datetime
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Check if running in GitHub Actions
IN_GITHUB_ACTIONS = os.environ.get('GITHUB_ACTIONS') == 'true'

# Define log directory for notification records
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
LOGS_DIR = PROJECT_ROOT / 'logs'
LOGS_DIR.mkdir(exist_ok=True)
NOTIFICATION_LOG = LOGS_DIR / 'telegram_notifications.log'

# Get Telegram credentials from environment
# In GitHub Actions, these should be set as repository secrets
if not IN_GITHUB_ACTIONS:
    # Only try to use dotenv in local development
    try:
        from dotenv import load_dotenv
        ENV_PATH = PROJECT_ROOT / '.env'
        load_dotenv(dotenv_path=ENV_PATH)
    except ImportError:
        logger.warning("python-dotenv not installed. Using environment variables directly.")

# Get credentials from environment (works for both .env and GitHub secrets)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')

def log_notification(entity, message, success):
    """Log notification details to file for record-keeping."""
    try:
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'entity_id': entity.get('id'),
            'domain': entity.get('domain'),
            'group': entity.get('ransomware_group', ''),
            'message_length': len(message),
            'success': success
        }
        
        with open(NOTIFICATION_LOG, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
            
    except Exception as e:
        logger.error(f"Failed to log notification: {e}")

def send_telegram_message(message):
    """Send a message to the Telegram channel."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        logger.error("Telegram credentials not set in environment variables")
        if IN_GITHUB_ACTIONS:
            logger.error("Make sure TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID are set as GitHub repository secrets")
        else:
            logger.error("Make sure these are set in your .env file or environment")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": message,
            "parse_mode": "HTML"  # Enable HTML formatting
        }
        
        response = requests.post(url, data=data)
        response.raise_for_status()  # Raise an exception for bad responses
        
        logger.info(f"Telegram message sent successfully: {response.status_code}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

def format_entity_notification(entity, site_name):
    """Format entity data into a readable Telegram notification message."""
    message = f"🚨 <b>New Ransomware Victim Discovered!</b>\n\n"
    
    # Core information
    message += f"<b>Domain:</b> {entity.get('domain', 'Unknown')}\n"
    message += f"<b>Ransomware Group:</b> {site_name}\n"
    
    # Entity status
    if entity.get('status'):
        status = entity.get('status').capitalize()
        if status == "Countdown":
            message += f"<b>Status:</b> ⏳ {status}\n"
        elif status == "Published":
            message += f"<b>Status:</b> 📢 {status}\n"
        else:
            message += f"<b>Status:</b> {status}\n"
    
    # Views/visits information
    if entity.get('views'):
        message += f"<b>Views:</b> {entity.get('views')}\n"
    elif entity.get('visits'):
        message += f"<b>Visits:</b> {entity.get('visits')}\n"
    
    # Data size if available (RansomHub specific)
    if entity.get('data_size'):
        message += f"<b>Data Size:</b> {entity.get('data_size')}\n"
    
    # Country information
    if entity.get('country'):
        message += f"<b>Country:</b> {entity.get('country')}\n"
        
    # Description preview
    if entity.get('description_preview'):
        # Truncate long descriptions
        description = entity.get('description_preview').strip()
        if len(description) > 200:
            description = description[:197] + "..."
        message += f"\n<b>Description:</b>\n{description}\n"
    
    # Countdown information
    if entity.get('status') == 'countdown' and entity.get('countdown_remaining'):
        countdown = entity.get('countdown_remaining')
        if isinstance(countdown, dict):
            # Handle different countdown formats
            if all(key in countdown for key in ['days', 'hours', 'minutes', 'seconds']):
                message += f"\n<b>Countdown:</b> {countdown.get('days', 0)}d {countdown.get('hours', 0)}h "
                message += f"{countdown.get('minutes', 0)}m {countdown.get('seconds', 0)}s\n"
            elif 'countdown_text' in countdown:
                message += f"\n<b>Countdown:</b> {countdown.get('countdown_text')}\n"
    
    # Publication date
    if entity.get('estimated_publish_date'):
        message += f"<b>Estimated Publication:</b> {entity.get('estimated_publish_date')}\n"
    
    # Add discovery timestamp
    message += f"\n<i>First seen: {entity.get('first_seen', 'Unknown')}</i>"
    
    return message

def notify_new_entity(entity, site_name):
    """Send a Telegram notification for a newly discovered entity."""
    try:
        message = format_entity_notification(entity, site_name)
        success = send_telegram_message(message)
        
        # Log the notification
        log_notification(entity, message, success)
        
        return success
    except Exception as e:
        logger.error(f"Error in notify_new_entity: {e}")
        return False

def send_scan_completion_notification(sites_processed, total_entities, new_entities):
    """
    Send a notification when a scan completes, even if no new entities were found.
    
    Args:
        sites_processed: List of site names that were processed
        total_entities: Total number of entities found across all sites
        new_entities: Number of new entities discovered in this scan
    """
    try:
        # Format the message with scan results
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Create a message with scan summary
        message = f"🔍 <b>Ransomware Tracker Scan Completed</b>\n\n"
        message += f"<b>Time:</b> {timestamp}\n"
        
        # Add sites processed
        if sites_processed:
            message += f"\n<b>Sites Scanned:</b>\n"
            for site in sites_processed:
                message += f"• {site}\n"
        
        # Add statistics
        message += f"\n<b>Total Entities:</b> {total_entities}\n"
        
        # Highlight new entities with emoji based on count
        if new_entities > 0:
            message += f"<b>New Entities:</b> 🚨 {new_entities} 🚨\n"
        else:
            message += f"<b>New Entities:</b> 0 (No new entities found)\n"
        
        # Add a status indicator
        if new_entities > 0:
            message += f"\n✅ <i>New entities were discovered and notifications sent</i>"
        else:
            message += f"\n✅ <i>Scan completed successfully with no new entities</i>"
        
        # Send the message
        success = send_telegram_message(message)
        
        if success:
            logger.info("Scan completion notification sent successfully")
        else:
            logger.error("Failed to send scan completion notification")
        
        # Create a dummy entity for logging purposes
        dummy_entity = {'id': 'scan_summary', 'domain': 'scan_summary'}
        log_notification(dummy_entity, message, success)
        
        return success
    except Exception as e:
        logger.error(f"Error in send_scan_completion_notification: {e}")
        return False
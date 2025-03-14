# browser/tor_browser.py
import time
import os
import datetime
import json
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.common.exceptions import TimeoutException, WebDriverException
from tracker.utils.logging_utils import logger

# Configuration cache to store current settings
_browser_config = None
_proxy_config = None
_scraping_config = None

# Helper function to get values from environment variables
def get_env_config_value(env_name, default_value):
    """Get configuration value from environment variable if available"""
    env_value = os.environ.get(env_name)
    if env_value is not None:
        # Convert to appropriate type
        if isinstance(default_value, bool):
            return env_value.lower() == "true"
        elif isinstance(default_value, int):
            try:
                return int(env_value)
            except ValueError:
                return default_value
        elif isinstance(default_value, float):
            try:
                return float(env_value)
            except ValueError:
                return default_value
        else:
            return env_value
    return default_value

# Determine the configuration directory based on environment
def get_config_dir():
    # Check if we're running in GitHub Actions with a custom config path
    github_config = os.environ.get('GITHUB_CONFIG_PATH')
    if github_config:
        return github_config
    
    # Default to the project's config directory
    return os.path.join(Path(__file__).parent.parent.parent.absolute(), "config")

# Load configuration files
def load_browser_config():
    """Load browser configuration from config file"""
    global _browser_config
    
    # Use cached version if available
    if _browser_config is not None:
        return _browser_config
    
    # Load from standard location
    config_dir = get_config_dir()
    browser_config_path = os.path.join(config_dir, "code", "browser_config.json")
    
    try:
        if not os.path.exists(browser_config_path):
            logger.warning(f"Browser config file not found at {browser_config_path}. Using default values.")
            _browser_config = {
                "timing": {
                    "min_wait_time": 10,
                    "max_wait_time": 20,
                    "tor_check_wait_time": 3,
                    "page_load_timeout": 120
                },
                "anti_bot": {
                    "enabled": True,
                    "randomize_timing": True
                },
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"
            }
            return _browser_config
        
        with open(browser_config_path, 'r') as f:
            _browser_config = json.load(f)
            return _browser_config
    except Exception as e:
        logger.error(f"Error loading browser config: {e}. Using default values.")
        _browser_config = {
            "timing": {
                "min_wait_time": 10,
                "max_wait_time": 20,
                "tor_check_wait_time": 3,
                "page_load_timeout": 120
            },
            "anti_bot": {
                "enabled": True,
                "randomize_timing": True
            },
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"
        }
        return _browser_config

def load_proxy_config():
    """Load proxy configuration from config file"""
    global _proxy_config
    
    # Use cached version if available
    if _proxy_config is not None:
        return _proxy_config
    
    # Load from standard location
    config_dir = get_config_dir()
    proxy_config_path = os.path.join(config_dir, "code", "proxy_config.json")
    
    try:
        if not os.path.exists(proxy_config_path):
            logger.warning(f"Proxy config file not found at {proxy_config_path}. Using default values.")
            _proxy_config = {
                "proxy": {
                    "type": "socks",
                    "host": "127.0.0.1",
                    "port": 9050,
                    "remote_dns": True
                },
                "tor": {
                    "auto_start": False
                }
            }
            return _proxy_config
        
        with open(proxy_config_path, 'r') as f:
            _proxy_config = json.load(f)
            return _proxy_config
    except Exception as e:
        logger.error(f"Error loading proxy config: {e}. Using default values.")
        _proxy_config = {
            "proxy": {
                "type": "socks",
                "host": "127.0.0.1",
                "port": 9050,
                "remote_dns": True
            },
            "tor": {
                "auto_start": False
            }
        }
        return _proxy_config

def load_scraping_config():
    """Load scraping configuration from config file"""
    global _scraping_config
    
    # Use cached version if available
    if _scraping_config is not None:
        return _scraping_config
    
    # Load from standard location
    config_dir = get_config_dir()
    scraping_config_path = os.path.join(config_dir, "code", "scraping_config.json")
    
    try:
        if not os.path.exists(scraping_config_path):
            logger.warning(f"Scraping config file not found at {scraping_config_path}. Using default values.")
            _scraping_config = {
                "snapshots": {
                    "save_html": False,
                    "max_snapshots_per_site": 5,
                    "cleanup_old_snapshots": True
                }
            }
            return _scraping_config
        
        with open(scraping_config_path, 'r') as f:
            _scraping_config = json.load(f)
            return _scraping_config
    except Exception as e:
        logger.error(f"Error loading scraping config: {e}. Using default values.")
        _scraping_config = {
            "snapshots": {
                "save_html": False,
                "max_snapshots_per_site": 5,
                "cleanup_old_snapshots": True
            }
        }
        return _scraping_config

def setup_tor_browser(headless=False):
    """Configure Firefox to use Tor"""
    # Load configurations if needed
    browser_config = load_browser_config()
    proxy_config = load_proxy_config()
    
    options = Options()
    
    # Get proxy settings from config
    proxy = proxy_config.get("proxy", {})
    
    # Check for environment variable overrides
    proxy_host = get_env_config_value("PROXY_PROXY_HOST", proxy.get("host", "127.0.0.1"))
    proxy_port = get_env_config_value("PROXY_PROXY_PORT", proxy.get("port", 9050))
    remote_dns = get_env_config_value("PROXY_PROXY_REMOTE_DNS", proxy.get("remote_dns", True))
    
    # Set proxy preferences
    options.set_preference('network.proxy.type', 1)
    options.set_preference('network.proxy.socks', proxy_host)
    options.set_preference('network.proxy.socks_port', proxy_port)
    options.set_preference('network.proxy.socks_remote_dns', remote_dns)
    
    # Get user agent from config
    user_agent = browser_config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0")
    
    # Additional settings to make us look more like a normal browser
    options.set_preference('general.useragent.override', user_agent)
    options.set_preference('javascript.enabled', True)
    options.set_preference('dom.webnotifications.enabled', False)
    options.set_preference('app.shield.optoutstudies.enabled', False)
    
    # Prevent popup notifications that might interfere with scraping
    options.set_preference('dom.popup_allowed_events', '')
    
    # Headless mode for production
    if headless:
        options.add_argument("--headless")
    
    # Check for GitHub Actions environment
    in_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    
    # If we're in GitHub Actions and have a firefox binary path, use it
    firefox_binary = None
    if "firefox_binary" in browser_config:
        firefox_binary_path = browser_config.get("firefox_binary")
        if firefox_binary_path and os.path.exists(firefox_binary_path):
            firefox_binary = FirefoxBinary(firefox_binary_path)
            logger.info(f"Using Firefox binary at: {firefox_binary_path}")
    
    # Create the driver
    try:
        if firefox_binary:
            options.binary = firefox_binary
            driver = webdriver.Firefox(options=options)
        else:
            driver = webdriver.Firefox(options=options)
        
        # Set page load timeout from config
        page_load_timeout = browser_config.get("timing", {}).get("page_load_timeout", 120)
        driver.set_page_load_timeout(page_load_timeout)
        
        return driver
    except Exception as e:
        logger.error(f"Error setting up Firefox browser: {e}")
        # More detailed error information
        if in_github_actions:
            logger.error("This error occurred in GitHub Actions environment.")
            logger.error(f"Firefox binary path in config: {browser_config.get('firefox_binary', 'Not set')}")
            logger.error(f"Firefox path from which command: {os.popen('which firefox').read().strip()}")
            logger.error(f"Firefox version: {os.popen('firefox --version').read().strip()}")
            logger.error(f"Geckodriver version: {os.popen('geckodriver --version').read().strip()}")
        raise

def test_tor_connection(driver):
    """Test if we can connect through Tor"""
    # Load config if needed
    browser_config = load_browser_config()
    
    try:
        driver.get('https://check.torproject.org/')
        
        # Get wait time from config
        tor_check_wait_time = browser_config.get("timing", {}).get("tor_check_wait_time", 3)
        time.sleep(tor_check_wait_time)  # Give page time to load
        
        if "Congratulations" in driver.page_source:
            logger.info("Successfully connected to Tor!")
            return True
        else:
            logger.warning("Connected to the site, but not through Tor")
            return False
    except Exception as e:
        logger.error(f"Failed to connect to Tor: {e}")
        return False

def get_wait_time():
    """Get a wait time based on configuration settings"""
    # Load config if needed
    browser_config = load_browser_config()
    
    # First check environment variables for direct overrides
    env_min = os.environ.get("BROWSER_TIMING_MIN_WAIT_TIME")
    env_max = os.environ.get("BROWSER_TIMING_MAX_WAIT_TIME")
    
    if env_min is not None and env_max is not None:
        try:
            min_wait_time = int(env_min)
            max_wait_time = int(env_max)
            logger.info(f"⭐ Using wait times from environment variables: min={min_wait_time}, max={max_wait_time}")
        except (ValueError, TypeError):
            logger.warning(f"Invalid environment variable values: BROWSER_TIMING_MIN_WAIT_TIME={env_min}, BROWSER_TIMING_MAX_WAIT_TIME={env_max}")
            # Continue to load from config file
            min_wait_time = max_wait_time = None
    else:
        min_wait_time = max_wait_time = None
    
    # If not set via environment variables, load from config
    if min_wait_time is None or max_wait_time is None:
        timing_config = browser_config.get("timing", {})
        
        min_wait_time = timing_config.get("min_wait_time", 10)
        max_wait_time = timing_config.get("max_wait_time", 20)
        
        logger.info(f"📄 Using wait times from config file: min={min_wait_time}, max={max_wait_time}")
    
    # Get anti-bot settings
    anti_bot_config = browser_config.get("anti_bot", {})
    
    # Check for environment variable overrides
    anti_bot_enabled = get_env_config_value("BROWSER_ANTI_BOT_ENABLED", anti_bot_config.get("enabled", True))
    randomize_timing = get_env_config_value("BROWSER_ANTI_BOT_RANDOMIZE_TIMING", anti_bot_config.get("randomize_timing", True))
    
    if anti_bot_enabled and randomize_timing:
        wait_time = random.uniform(min_wait_time, max_wait_time)
        logger.info(f"Generated random wait time: {wait_time:.2f}s")
        return wait_time
    else:
        logger.info(f"Using fixed wait time: {min_wait_time}s")
        return min_wait_time

def browse_with_selenium(driver, url, site_config, wait_time=None):
    """Browse to a URL with Selenium, handling anti-bot measures"""
    site_name = site_config.get('site_name', 'Unknown')
    site_verification = site_config.get('site_verification', {})
    verification_type = site_verification.get('type', 'text')
    verification_value = site_verification.get('value', '')
    
    # Use configured wait time if not specified
    if wait_time is None:
        wait_time = get_wait_time()
    
    try:
        logger.info(f"Navigating to {url}...")
        driver.get(url)
        
        # Only wait if anti-bot measures are enabled
        browser_config = load_browser_config()
        
        # Check for anti-bot override from environment
        anti_bot_enabled = get_env_config_value("BROWSER_ANTI_BOT_ENABLED", browser_config.get("anti_bot", {}).get("enabled", True))
            
        if anti_bot_enabled:
            logger.info(f"Waiting {wait_time:.2f} seconds for anti-bot measures...")
            time.sleep(wait_time)
        
        # Check if the page has content we expect based on verification type
        if verification_type == 'text':
            if verification_value not in driver.page_source:
                logger.warning(f"Text '{verification_value}' not found in page for {site_name}, might not be the correct site")
                return None
        elif verification_type == 'class':
            if f'class="{verification_value}"' not in driver.page_source and f"class='{verification_value}'" not in driver.page_source:
                logger.warning(f"Class '{verification_value}' not found in page for {site_name}, might not be the correct site")
                return None
        elif verification_type == 'selector':
            from selenium.webdriver.common.by import By
            elements = driver.find_elements(By.CSS_SELECTOR, verification_value)
            if not elements:
                logger.warning(f"Selector '{verification_value}' not found in page for {site_name}, might not be the correct site")
                return None
        
        return driver.page_source
    
    except Exception as e:
        logger.error(f"Error visiting {url}: {e}")
        return None

def get_working_mirror(driver, site_config):
    """Try to connect to each mirror until finding one that works"""
    site_name = site_config.get('site_name', 'Unknown')
    mirrors = site_config.get('mirrors', [])
    
    for mirror in mirrors:
        url = f"http://{mirror}"
        logger.info(f"Trying {site_name} mirror: {mirror}")
        
        html_content = browse_with_selenium(driver, url, site_config)
        
        if html_content:
            logger.info(f"Successfully connected to {mirror}")
            return mirror, html_content
    
    logger.error(f"All {site_name} mirrors failed")
    return None, None

def save_html_snapshot(html_content, site_key, html_snapshots_dir):
    """Save HTML content to a timestamped file for analysis"""
    # Load config if needed
    scraping_config = load_scraping_config()
    
    # First check environment variable for save_html
    save_html = get_env_config_value("SCRAPING_SNAPSHOTS_SAVE_HTML", 
                                    scraping_config.get("snapshots", {}).get("save_html", False))
    
    # Check if saving snapshots is enabled
    if not save_html:
        logger.info("HTML snapshot saving is disabled in configuration. Skipping.")
        return None
    
    logger.info(f"⭐ HTML snapshot saving is enabled ({save_html})")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    site_snapshot_dir = os.path.join(html_snapshots_dir, site_key)
    os.makedirs(site_snapshot_dir, exist_ok=True)
    
    html_filename = os.path.join(site_snapshot_dir, f"{site_key}_snapshot_{timestamp}.html")
    
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    logger.info(f"Raw HTML saved to {html_filename}")
    
    # Cleanup old snapshots if enabled - check environment variable
    cleanup_old = get_env_config_value("SCRAPING_SNAPSHOTS_CLEANUP_OLD_SNAPSHOTS", 
                                      scraping_config.get("snapshots", {}).get("cleanup_old_snapshots", True))
    
    if cleanup_old:
        max_snapshots = get_env_config_value("SCRAPING_SNAPSHOTS_MAX_SNAPSHOTS_PER_SITE", 
                                            scraping_config.get("snapshots", {}).get("max_snapshots_per_site", 5))
        
        cleanup_old_snapshots(site_snapshot_dir, max_snapshots)
    
    return html_filename

def cleanup_old_snapshots(snapshot_dir, max_keep=5):
    """Delete older snapshots to maintain only a fixed number of recent ones"""
    try:
        # List all snapshot files in the directory
        snapshot_files = [f for f in os.listdir(snapshot_dir) if f.endswith('.html')]
        
        # If we have more files than the max to keep
        if len(snapshot_files) > max_keep:
            # Sort by modification time (oldest first)
            snapshot_files.sort(key=lambda f: os.path.getmtime(os.path.join(snapshot_dir, f)))
            
            # Remove the oldest files
            for old_file in snapshot_files[:-max_keep]:
                os.remove(os.path.join(snapshot_dir, old_file))
                logger.info(f"Removed old snapshot: {old_file}")
    except Exception as e:
        logger.error(f"Error cleaning up old snapshots: {e}")
# tracker/utils/tor_manager.py
import os
import json
import subprocess
import time
import signal
import atexit
import tempfile
from pathlib import Path
import shutil
from tracker.utils.logging_utils import logger

# Global variables
tor_process = None
temp_torrc_file = None

def load_proxy_config():
    """Load proxy configuration from config file"""
    PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
    PROXY_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "code", "proxy_config.json")
    
    try:
        if not os.path.exists(PROXY_CONFIG_PATH):
            logger.warning(f"Proxy config file not found at {PROXY_CONFIG_PATH}. Using default values.")
            return {
                "proxy": {
                    "type": "socks",
                    "host": "127.0.0.1",
                    "port": 9050,
                    "remote_dns": True
                },
                "tor": {
                    "auto_start": False,
                    "config": [
                        "SocksPort 9050",
                        "ControlPort 9051",
                        "CookieAuthentication 1",
                        "CircuitBuildTimeout 60",
                        "LearnCircuitBuildTimeout 0",
                        "HiddenServiceStatistics 0",
                        "OptimisticData 1"
                    ]
                }
            }
        
        with open(PROXY_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading proxy config: {e}. Using default values.")
        return {
            "proxy": {
                "type": "socks",
                "host": "127.0.0.1",
                "port": 9050,
                "remote_dns": True
            },
            "tor": {
                "auto_start": False,
                "config": [
                    "SocksPort 9050",
                    "ControlPort 9051",
                    "CookieAuthentication 1",
                    "CircuitBuildTimeout 60",
                    "LearnCircuitBuildTimeout 0",
                    "HiddenServiceStatistics 0",
                    "OptimisticData 1"
                ]
            }
        }

def create_temp_torrc():
    """Create a temporary torrc file with our configuration"""
    global temp_torrc_file
    
    # Load proxy configuration
    config = load_proxy_config()
    tor_config = config.get("tor", {})
    config_lines = tor_config.get("config", [
        "SocksPort 9050",
        "ControlPort 9051",
        "CookieAuthentication 1",
        "CircuitBuildTimeout 60",
        "LearnCircuitBuildTimeout 0",
        "HiddenServiceStatistics 0",
        "OptimisticData 1"
    ])
    
    try:
        # Create a temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.torrc', text=True)
        
        # Write config to the file
        with os.fdopen(fd, 'w') as f:
            for line in config_lines:
                f.write(f"{line}\n")
        
        logger.info(f"Temporary Tor configuration written to {temp_path}")
        temp_torrc_file = temp_path
        return temp_path
    except Exception as e:
        logger.error(f"Error creating temporary torrc file: {e}")
        return None

def cleanup_temp_file():
    """Clean up the temporary torrc file"""
    global temp_torrc_file
    
    if temp_torrc_file and os.path.exists(temp_torrc_file):
        try:
            os.remove(temp_torrc_file)
            logger.info(f"Removed temporary torrc file: {temp_torrc_file}")
            temp_torrc_file = None
        except Exception as e:
            logger.error(f"Error removing temporary torrc file: {e}")

def start_tor():
    """Start Tor with our configuration"""
    global tor_process
    
    # Load proxy configuration
    config = load_proxy_config()
    tor_config = config.get("tor", {})
    
    # Check if auto-start is enabled
    if not tor_config.get("auto_start", False):
        logger.info("Tor auto-start is disabled in configuration. Skipping.")
        return False
    
    # Check if Tor is installed
    if shutil.which("tor") is None:
        logger.error("Tor executable not found in PATH. Please install Tor.")
        return False
    
    # Create a temporary torrc file
    temp_config_path = create_temp_torrc()
    if not temp_config_path:
        logger.error("Failed to create temporary torrc file. Cannot start Tor.")
        return False
    
    try:
        # Start Tor process with the temporary config file
        start_command = f"tor -f {temp_config_path}"
        logger.info(f"Starting Tor with command: {start_command}")
        
        tor_process = subprocess.Popen(
            start_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )
        
        # Register cleanup functions to stop Tor and remove temp file when the script exits
        atexit.register(stop_tor)
        atexit.register(cleanup_temp_file)
        
        # Wait a bit for Tor to start
        time.sleep(5)
        
        # Check if process is still running
        if tor_process.poll() is None:
            logger.info("Tor process started successfully")
            return True
        else:
            stdout, stderr = tor_process.communicate()
            logger.error(f"Tor process failed to start: {stderr}")
            cleanup_temp_file()  # Clean up early on failure
            return False
        
    except Exception as e:
        logger.error(f"Error starting Tor: {e}")
        cleanup_temp_file()  # Clean up early on failure
        return False

def stop_tor():
    """Stop the Tor process if it's running"""
    global tor_process
    
    if tor_process is not None:
        logger.info("Stopping Tor process...")
        try:
            # Try to terminate gracefully
            tor_process.terminate()
            tor_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If it doesn't respond, force kill
            logger.warning("Tor process did not terminate gracefully, forcing kill")
            tor_process.kill()
        except Exception as e:
            logger.error(f"Error stopping Tor process: {e}")
        
        tor_process = None
        logger.info("Tor process stopped")

def is_tor_running():
    """Check if Tor is already running on the configured port"""
    config = load_proxy_config()
    port = config.get("proxy", {}).get("port", 9050)
    
    try:
        # Simple check using subprocess to see if the port is in use
        result = subprocess.run(
            f"lsof -i :{port} | grep LISTEN",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # If the command returned output, something is listening on the port
        if result.stdout.strip():
            logger.info(f"Tor appears to be already running on port {port}")
            return True
        else:
            logger.info(f"No process found listening on port {port}")
            return False
    except Exception as e:
        logger.error(f"Error checking if Tor is running: {e}")
        return False

def ensure_tor_running():
    """Ensure Tor is running, starting it if necessary"""
    # Check if we're running in Docker (common Docker environment variable)
    in_docker = os.environ.get('RUNNING_IN_DOCKER') == 'true' or os.path.exists('/.dockerenv')
    
    # Check if we're running in GitHub Actions
    in_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    
    if in_docker:
        logger.info("Running in Docker environment. Assuming Tor is managed by supervisord.")
        if is_tor_running():
            logger.info("Tor is running in Docker environment.")
            return True
        else:
            logger.error("Tor does not appear to be running in Docker environment.")
            logger.error("The Tor service should be managed by supervisord.")
            return False
    
    if in_github_actions:
        logger.info("Running in GitHub Actions environment. Checking if Tor is available...")
        if is_tor_running():
            return True
        else:
            logger.error("Tor does not appear to be running in GitHub Actions environment")
            return False
    
    # Normal flow for non-Docker, non-GitHub environments
    if is_tor_running():
        logger.info("Tor is already running.")
        return True
    
    # If Tor is not running, try to start it
    logger.info("Tor is not running. Attempting to start it...")
    return start_tor()
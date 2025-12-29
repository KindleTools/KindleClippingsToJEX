import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("KindleToJex.Config")

# Possible locations for config file
CONFIG_CANDIDATES = [
    'config.json',
    'config/config.json',
    '../config.json'
]

def load_config_from_file() -> Dict[str, Any]:
    """Load configuration from the config file."""
    config_path = None
    for candidate in CONFIG_CANDIDATES:
        if os.path.exists(candidate):
            config_path = candidate
            break
    
    if not config_path:
        logger.warning(f"Configuration file not found. Checked: {CONFIG_CANDIDATES}")
        return {}
    
    logger.info(f"Loading configuration from: {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing '{config_path}': {e}")
        return {}
    except Exception as e:
        logger.error(f"Error reading '{config_path}': {e}")
        return {}

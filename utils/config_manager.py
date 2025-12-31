import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("KindleToJex.Config")

class ConfigManager:
    """
    Manages application configuration, unifying CLI and GUI keys.
    Follows structure of config.sample.json.
    """
    DEFAULT_CONFIG = {
        "creator": "System",
        "location": [0.0, 0.0, 0],
        "notebook_title": "Kindle Imports",
        "input_file": "",
        "output_file": "import_clippings",
        "language": "auto"
    }

    def __init__(self, config_dir: str = "config", config_filename: str = "config.json"):
        self.config_dir = config_dir
        self.config_filename = config_filename
        self.config_path = os.path.join(self.config_dir, self.config_filename)
        self._config_data: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        
        # Determine project root for relative path resolution
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        self._load()

    def get_resource_path(self, filename: str) -> str:
        """Returns the absolute path to a resource file."""
        return os.path.join(self.project_root, 'resources', filename)

    def _ensure_dir(self):
        """Ensures the configuration directory exists."""
        if not os.path.exists(self.config_dir):
            try:
                os.makedirs(self.config_dir, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create config directory {self.config_dir}: {e}")

    def _load(self):
        """Loads configuration from file if it exists, otherwise uses defaults."""
        if not os.path.exists(self.config_path):
            logger.info("No config file found. Using defaults.")
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                # Merge defaults with loaded data to ensure all keys exist
                self._config_data.update(loaded_data)
                logger.info(f"Configuration loaded from {self.config_path}")
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading config file {self.config_path}: {e}")

    def save(self):
        """Saves the current configuration to file."""
        self._ensure_dir()
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=4, ensure_ascii=False)
            logger.info("Configuration saved.")
        except OSError as e:
            logger.error(f"Error saving config to {self.config_path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value."""
        return self._config_data.get(key, default)

    def set(self, key: str, value: Any):
        """Sets a configuration value and persists changes immediately."""
        self._config_data[key] = value
        self.save()

# Global singleton-like instance for easy access
_global_manager = None

def get_config_manager() -> ConfigManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = ConfigManager()
    return _global_manager

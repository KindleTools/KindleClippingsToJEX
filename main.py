import json
import os
import sys
import logging
from src.services.clippings_service import ClippingsService
from src.utils.logging_config import setup_logging

CONFIG_FILE = 'config.json'

# Setup Logger
logger = setup_logging()

def load_config():
    """Load configuration from the config file."""
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"Configuration file '{CONFIG_FILE}' not found.")
        print("Please copy 'config.sample.json' to 'config.json' and update it with your settings.")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing '{CONFIG_FILE}': {e}")
            sys.exit(1)

def main():
    logger.info("Application started.")
    config = load_config()
    
    try:
        input_file = config.get('input_file', 'files/My Clippings.txt')
        output_file = config.get('output_file', 'import_clippings')
        location = tuple(config.get('location', [0, 0, 0]))
        creator = config.get('creator', 'System')
        notebook_title = config.get('notebook_title', 'Kindle Imports')
        language = config.get('language', 'es')
        
        logger.info(f"Input: {input_file}")
        logger.info(f"Output Target: {output_file}")
        logger.info(f"Language: {language}")
        
        if not os.path.exists(input_file):
            logger.error(f"Input file '{input_file}' does not exist.")
            sys.exit(1)

        # Pass language to Service
        service = ClippingsService(language_code=language)
        service.process_clippings(
            input_file=input_file,
            output_file=output_file,
            root_notebook_name=notebook_title,
            location=location,
            creator_name=creator
        )
            
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()

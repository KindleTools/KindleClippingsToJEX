import sys
import os
import argparse
import logging
from services.clippings_service import ClippingsService
from utils.logging_config import setup_logging
from utils.config_manager import load_config_from_file

# Setup Logger
logger = setup_logging()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Convert Kindle Clippings to Joplin JEX format.")
    parser.add_argument('--input', '-i', help="Path to 'My Clippings.txt' file")
    parser.add_argument('--output', '-o', help="Output JEX filename (without extension)")
    parser.add_argument('--lang', '-l', help="Language code (e.g., 'es', 'en')")
    parser.add_argument('--notebook', '-n', help="Root notebook title in Joplin")
    parser.add_argument('--creator', '-c', help="Author name to use for created notes")
    return parser.parse_args()

def main():
    logger.info("Application started via CLI.")
    
    # Load config from file
    file_config = load_config_from_file()
    
    # Parse CLI args
    args = parse_args()
    
    # Determine effective configuration (CLI args > File Config > Defaults)
    input_file = args.input or file_config.get('input_file', 'data/My Clippings.txt')
    output_file = args.output or file_config.get('output_file', 'import_clippings')
    language = args.lang or file_config.get('language', 'es')
    notebook_title = args.notebook or file_config.get('notebook_title', 'Kindle Imports')
    creator = args.creator or file_config.get('creator', 'System')
    location = tuple(file_config.get('location', [0, 0, 0])) # Geo-location usually not a volatile arg
    
    logger.info(f"Input: {input_file}")
    logger.info(f"Output Target: {output_file}")
    logger.info(f"Language: {language}")
    
    # Validate Input
    if not os.path.exists(input_file):
        logger.error(f"Input file '{input_file}' does not exist.")
        sys.exit(1)
    
    try:
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

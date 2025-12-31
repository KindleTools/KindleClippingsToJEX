import sys
import os
import argparse
from services.clippings_service import ClippingsService
from utils.logging_config import setup_logging
from utils.config_manager import get_config_manager

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
    parser.add_argument('--no-clean', action='store_true', help="Disable smart deduplication and cleaning")
    return parser.parse_args()

def main():
    logger.info("Application started via CLI.")
    
    # Load config manager
    config = get_config_manager()
    
    # Parse CLI args
    args = parse_args()
    
    # Determine effective configuration (CLI args > File Config > Defaults)
    # Note: fallback strings here should match ConfigManager defaults for consistency
    input_file = args.input or config.get('input_file') or 'data/My Clippings.txt'
    output_file = args.output or config.get('output_file') or 'import_clippings'
    language = args.lang or config.get('language') or 'auto'
    notebook_title = args.notebook or config.get('notebook_title') or 'Kindle Imports'
    creator = args.creator or config.get('creator') or 'System'
    location = tuple(config.get('location', [0, 0, 0])) # Geo-location
    
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
            creator_name=creator,
            enable_deduplication=not args.no_clean
        )
            
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()

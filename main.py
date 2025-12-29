import json
import os
import sys
from src.services.clippings_service import ClippingsService

CONFIG_FILE = 'config.json'

def load_config():
    """Load configuration from the config file."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Configuration file '{CONFIG_FILE}' not found.")
        print("Please copy 'config.sample.json' to 'config.json' and update it with your settings.")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing '{CONFIG_FILE}': {e}")
            sys.exit(1)

def main():
    config = load_config()
    
    try:
        input_file = config.get('input_file', 'files/My Clippings.txt')
        output_file = config.get('output_file', 'import_clippings')
        location = tuple(config.get('location', [0, 0, 0]))
        creator = config.get('creator', 'System')
        notebook_title = config.get('notebook_title', 'Kindle Imports')
        
        print(f"Starting process...")
        print(f"Input: {input_file}")
        print(f"Output: {output_file}")
        
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' does not exist.")
            sys.exit(1)

        service = ClippingsService()
        service.process_clippings(
            input_file=input_file,
            output_file=output_file,
            root_notebook_name=notebook_title,
            location=location,
            creator_name=creator
        )
            
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

import json
import os
import sys
from process import kindle_process, ini_process

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
    
    # Extract configuration
    try:
        input_file = config.get('input_file', 'files/txt/My Clippings.txt')
        output_file = config.get('output_file', 'import_clippings')
        location = tuple(config.get('location', [0, 0, 0]))
        creator = config.get('creator', 'System')
        notebook_title = config.get('notebook_title', 'Kindle Imports')
        
        print(f"Starting process...")
        print(f"Input File: {input_file}")
        print(f"Target Notebook: {notebook_title}")
        print(f"Creator: {creator}")
        print(f"Location: {location}")
        
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' does not exist.")
            sys.exit(1)

        # Initialize the parent notebook
        parent_notebook = ini_process(notebook_title)
        
        # Run the kindle processing
        # This will process the highlights and export to the output file (JEX format)
        result = kindle_process(
            infile=input_file,
            location=location,
            creator=creator,
            parent=parent_notebook,
            outfile=output_file
        )
        
        if result:
            print(f"Successfully exported to '{output_file}.jex'")
        else:
            print("Process completed but no output file was generated (or return value was None).")
            
    except KeyError as e:
        print(f"Error: Missing configuration key: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        # Print stack trace for debugging
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

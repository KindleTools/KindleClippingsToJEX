# KindleClippingsToJEX

**KindleClippingsToJEX** is a robust tool designed to process your Kindle highlights (`My Clippings.txt`) and convert them into a **Joplin Export File (.jex)**. It preserves all metadata (author, book, date, page/location) and organizes them into a clean notebook structure ready for import into [Joplin](https://joplinapp.org/).

## Features

- **Dual Interface**: Use the command-line interface (CLI) for automation or the Graphical User Interface (GUI) for visual management.
- **Smart Parsing**: Automatically parses books, authors, and types (highlight vs. note).
- **Metadata Preservation**: Associates notes with their corresponding highlights and tags.
- **Multi-language Support**: Configurable parsing for Kindle devices set to English, Spanish, French, German, Italian, or Portuguese.
- **Modular Architecture**: Clean code structure designed for extensibility.
- **Security**: Configuration is externalized to avoid committing sensitive data.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/KindleClippingsToJEX.git
   cd KindleClippingsToJEX
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv .venv
   # Windows
   .\.venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. Install the package in editable mode (installs dependencies automatically):
   ```bash
   pip install -e .
   ```

## Configuration

Before running the tool, copy the sample configuration file and customize it:

1. Copy `config.sample.json` to `config.json` inside the `config` folder:
   ```bash
   # Windows
   copy config\config.sample.json config\config.json
   # Linux/Mac
   cp config/config.sample.json config/config.json
   ```

2. Edit `config/config.json` with your preferences:
   ```json
   {
       "creator": "Your Name",
       "location": [0.0, 0.0, 0],
       "notebook_title": "Kindle Imports",
       "input_file": "data/My Clippings.txt",
       "output_file": "my_import",
       "language": "en"
   }
   ```

   *Supported languages in `language` field: `en`, `es`, `fr`, `de`, `it`, `pt`.*

   You can place your `My Clippings.txt` in the `data/` folder for easy access.

## Usage

### Graphical User Interface (GUI)

The GUI allows you to preview, edit, and filter your highlights before exporting.

Run from the command line:
```bash
kindle-to-jex-gui
```
*Or alternatively:* `python gui.py`

1. Click **"Recargar subrayados"** (Reload Highlights) to load from the default file or select a file manually.
2. Edit text directly in the preview pane if needed.
3. Use the search bar to filter entries.
4. Click **"Generar archivo .jex"** to export.

### Command Line Interface (CLI)

Ideal for automated scripts or quick batch processing based on `config.json`.

Run from the command line:
```bash
kindle-to-jex
```
*Or alternatively:* `python cli.py`

The script will generate a `.jex` file (e.g., `import_clippings.jex`) which you can then import into Joplin via **File > Import > JEX - Joplin Export File**.

## Project Structure

This project follows a flat-layout structure for simplicity.

```
├── pyproject.toml                 # Project configuration and dependencies
├── cli.py                         # CLI entry point
├── gui.py                         # GUI entry point
├── config/                        # User configuration files
│   ├── config.json
│   └── config.sample.json
├── data/                          # Input data directory (e.g. My Clippings.txt)
├── logs/                          # Application logs
├── domain/                        # Data models
├── parsers/                       # Parsing logic
├── services/                      # Business logic orchestration
├── exporters/                     # JEX file generation
├── utils/                         # Utilities (logging, etc.)
├── resources/                     # Static resources (lines, i18n)
└── tests/                         # Unit tests
```

## Running Tests

To run the unit tests, use the following command:

```bash
python -m unittest discover tests
```

## Contributing

Contributions are welcome! Please check [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

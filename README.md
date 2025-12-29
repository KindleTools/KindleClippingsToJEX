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

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Before running the CLI tool, copy the sample configuration file and customize it:

1. Copy `config.sample.json` to `config.json`:
   ```bash
   cp config.sample.json config.json
   ```

2. Edit `config.json` with your preferences:
   ```json
   {
       "creator": "Your Name",
       "location": [0.0, 0.0, 0],
       "notebook_title": "Kindle Imports",
       "input_file": "files/My Clippings.txt",
       "output_file": "my_import",
       "language": "en"
   }
   ```

   *Supported languages in `language` field: `en`, `es`, `fr`, `de`, `it`, `pt`.*

## Usage

### Graphical User Interface (GUI)

The GUI allows you to preview, edit, and filter your highlights before exporting.

```bash
python gui_app.py
```

1. Click **"Recargar subrayados"** (Reload Highlights) to load from the default file or select a file manually.
2. Edit text directly in the preview pane if needed.
3. Use the search bar to filter entries.
4. Click **"Generar archivo .jex"** to export.

### Command Line Interface (CLI)

Ideal for automated scripts or quick batch processing based on `config.json`.

```bash
python main.py
```

The script will generate a `.jex` file (e.g., `import_clippings.jex`) which you can then import into Joplin via **File > Import > JEX - Joplin Export File**.

## Project Structure

```
├── gui_app.py           # Entry point for the GUI application
├── main.py              # Entry point for the CLI application
├── config.json          # User configuration (ignored by git)
├── languages.json       # I18n regex patterns
├── src/                 # Source code
│   ├── domain/          # Data models
│   ├── parsers/         # Parsing logic
│   ├── services/        # Business logic orchestration
│   ├── exporters/       # JEX file generation
│   └── utils/           # Utilities (logging, etc.)
└── tests/               # Unit tests
```

## Contributing

Contributions are welcome! Please check [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

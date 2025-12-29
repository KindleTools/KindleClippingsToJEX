# KindleClippingsToJEX

**KindleClippingsToJEX** is a robust, professional-grade tool designed to process your Kindle highlights (`My Clippings.txt`) and convert them into a **Joplin Export File (.jex)**. It preserves all critical metadata (author, book, date, page/location) and intelligently organizes them into a clean notebook structure ready for direct import into [Joplin](https://joplinapp.org/).

Whether you are a casual reader or a power user, this tool ensures your Kindle notes are never lost and always accessible in your favorite note-taking app.

## Features

### 🚀 Core Functionality
- **JEX Native Export**: Generates standard `.jex` files (tarball of markdown files + JSON metadata) that import flawlessly into Joplin, preserving creation dates and official titles.
- **Enhanced Metadata Extraction**: Intelligently extracts author names, book titles, locations, and page numbers. It even handles page numbers with zero-padding (e.g., `[0042]`) to ensure proper lexical sorting.
- **Smart Tagging**: Converts your Kindle notes into Joplin tags. Supports splitting multiple tags by comma, semicolon, or period (e.g., "productivity, psychology").
- **Deduplication Logic**: Prevents duplicate notes. If you re-import an updated clippings file, the system is designed to identify existing highlights based on content hash and metadata.
- **Multi-language Support**: Fully configurable parsing for Kindle devices set to English, Spanish, French, German, Italian, or Portuguese.

### 🎨 "Zen" Graphical User Interface (New)
The project features a completely redesigned, modern "Zen" interface focused on simplicity, focus, and efficiency.

#### Key GUI Features:
- **Instant Auto-Load**: Automatically detects and loads `data/My Clippings.txt` on startup. If not found, a friendly "Empty State" guides you.
- **Live Stats Dashboard**: The header updates in real-time to show exactly how many highlights are visible (e.g., *"Showing 12 of 521 highlights"*).
- **Clean Data Table**: A clutter-free table view focusing on what matters:
  - **Date**: Sortable by timestamp.
  - **Book**: Filterable title.
  - **Author**: Filterable author name.
  - **Content**: Smart preview that expands on double-click.
  - **Tags**: Editable tags column (comma-separated).
- **Smart Search**: Real-time filtering by text. Type "Harry" and instantly see only related notes. The export function respects this filter ("What You See Is What You Get").
- **Bidirectional Editing**: 
  - Edit text directly in the table cells.
  - OR use the spacious **Bottom Editor Pane** for long texts.
  - Changes are synced instantly between views.
- **Power Selection & Context Menu**: 
  - **Multi-select**: Use `Shift+Click` or `Ctrl+Click` to select multiple rows.
  - **Right-Click Menu**:
    - **Export Selected**: Create a mini .jex file containing ONLY the selected notes.
    - **Duplicate**: Clone a row (useful for splitting one long highlight into two distinct notes).
    - **Delete**: Remove unwanted highlights before exporting.

### 💻 Command Line Interface (CLI)
For power users and automation scripts, the CLI offers a headless experience.

- **Batch Processing**: Process huge files in seconds without opening the window.
- **Configurable**: Fully controlled via arguments or `config.json`.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/KindleClippingsToJEX.git
   cd KindleClippingsToJEX
   ```

2. **Create a virtual environment (Recommended):**
   ```bash
   python -m venv .venv
   # Windows
   .\.venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

## Configuration

The application uses a `config/config.json` file for default settings. You can copy `config/config.sample.json` to get started.

```json
{
    "creator": "Your Name",
    "location": [0.0, 0.0, 0],
    "notebook_title": "Kindle Imports",
    "input_file": "data/My Clippings.txt",
    "output_file": "my_import",
    "language": "es"
}
```

*Supported languages:* `en`, `es`, `fr`, `de`, `it`, `pt`.

## Usage

### Using the GUI

Run the main application entry point:
```bash
python main.py
```

**Workflow:**
1. **Load**: The app opens your default clippings file. If missing, click **"Open File"**.
2. **Curate**: 
   - Use the **Search Bar** to filter by book title or content.
   - Use **Ctrl+Click** to select specific notes.
   - Right-click and select **"Delete Row(s)"** to remove irrelevant highlights.
   - Edit the **Content** or **Tags** columns to fix typos or add context.
3. **Export**: 
   - **Export Visible**: Click the main **"Export to JEX"** button to export everything currently visible in the table.
   - **Export Selection**: Select specific rows, Right-Click > **"Export Selected"** to save just those notes.
4. **Import**: In Joplin, go to **File > Import > JEX - Joplin Export File** and select your generated file.

### Using the CLI

Run the CLI script:
```bash
python cli.py
```

**Options:**
- `--input`, `-i`: Path to source file (default: from config).
- `--output`, `-o`: Output filename (default: from config).
- `--lang`, `-l`: Force language parsing (e.g., `en`).

Example:
```bash
python cli.py --input "data/old_clippings.txt" --output "archive_2023" --lang en
```

## Project Structure

The project follows a modular hexagon-like architecture to separate UI, Business Logic, and Data Parsing:

```
├── main.py                        # GUI Entry Point
├── cli.py                         # CLI Entry Point
├── ui/                            # GUI Layer (PyQt5)
│   ├── main_window.py             # Main Window Orchestrator (Controllers & Signals)
│   └── widgets.py                 # Reusable UI Components (Table, Search, Delegates)
├── config/                        # Configuration Management
├── domain/                        # Core Data Models (Clipping, Note)
├── parsers/                       # Text Parsing Logic (Regex & State Machines)
├── services/                      # Application Business Logic (Import/Export Flow)
├── exporters/                     # JEX Generation Logic (Tarball packing)
├── utils/                         # Logging and Helpers
├── resources/                     # Static Assets
└── tests/                         # Unit Tests
```

## Running Tests

To run the test suite and ensure everything is working correctly:

```bash
python -m unittest discover tests
```

## Contributing

Contributions are welcome! Please check [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on code style (PEP 8) and pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

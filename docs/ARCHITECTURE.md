# Architecture & Design Decisions

## Overview
**KindleClippingsToJEX** is a robust tool designed to parse Kindle `My Clippings.txt` files and convert them into multiple export formats (JEX, CSV, Markdown, JSON). The core philosophy is **Data Integrity** and **Idempotency**—ensuring that re-importing the same file does not create duplicates in Joplin.

## Core Design Decisions

### 1. Deterministic Identity (The ID Problem)
**Challenge:** Kindle clippings do not have inherent unique IDs. Joplin generates random UUIDs for new notes. Importing the same file twice results in duplicate notes.

**Solution:** We implement a **Deterministic ID Strategy**.
- **Logic:** `SHA-256(Content | BookTitle | Author | Location)`
- **Exclusion:** Timestamps are deliberately excluded from the hash. This ensures that if you re-import the same file later (or from a different device clock), the ID remains identical.
- **Result:** The same highlight always generates the exact same ID. Joplin recognizes this ID and updates the existing note (or ignores it if identical) rather than creating a copy.
- **Reference:** [`identity_service.py`](../services/identity_service.py)

### 2. Smart Deduplication
Beyond ID-based deduplication, the `SmartDeduplicator` handles the "append-only" mess of `My Clippings.txt`:
- **Overlapping Highlights:** When the user re-highlights a longer passage, the shorter version is flagged as duplicate, keeping the most complete version.
- **Edited Notes:** When multiple notes exist at the same location, only the latest is kept.
- **Accidental Highlights:** Very short fragments (<75 chars) that lack punctuation or start with lowercase are flagged as potential accidents—unless the user has explicitly tagged them.
- **Tag Preservation:** When merging duplicates, tags from all versions are consolidated into the surviving highlight.
- **Reference:** [`deduplication_service.py`](../services/deduplication_service.py)

### 3. Domain-Driven Structure
The codebase follows a loose Hexagonal/Clean Architecture:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   ui/       │────▶│  services/   │────▶│   exporters/    │
│  (PyQt5)    │     │  (Business)  │     │  (JEX/CSV/MD/…) │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
                    ┌──────┴───────┐
                    │   parsers/   │
                    │  (Kindle)    │
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │   domain/    │
                    │ (Dataclasses)│
                    └──────────────┘
```

- **`domain/`**: Pure data classes (`Clipping`, `JoplinNote`, `JoplinTag`, etc.). No logic, just data structures with strict typing via Python Dataclasses and IntEnum.
- **`parsers/`**: Logic to interpret raw messy text from Kindle. Handles encoding hell (UTF-8 w/ BOM, CP1252, Latin-1) and multi-language regex patterns (6 languages).
- **`services/`**: Business logic orchestration.
  - `ClippingsService`: Main coordinator (parse → deduplicate → export).
  - `DeduplicationService`: Overlap detection and merge logic.
  - `IdentityService`: Deterministic ID generation and Jaccard similarity.
- **`exporters/`**: Output adapters using the **Strategy Pattern** (`BaseExporter` ABC) to switch between JEX, JSON, CSV, and Markdown. New formats are added by implementing a single `export()` method.
- **`ui/`**: Presentation layer (PyQt5). Threaded loading/export to keep the UI responsive.
- **`utils/`**: Cross-cutting concerns: `ConfigManager` (JSON-based config singleton), `TextCleaner` (NFC normalization, de-hyphenation, typesetting fixes), `TitleCleaner` (edition/extension removal), and logging configuration.

### 4. Resilience over Perfection
**Kindle formats are inconsistent.** Dates change format by language, separators vary, and file encodings differ.
- **Encoding Cascade:** The parser tries multiple encodings sequentially (`utf-8-sig` → `cp1252` → `latin-1`) before deciding.
- **Language Auto-Detection:** A score-based system matches clipping headers against known patterns for each language, selecting the best fit automatically.
- **Fallbacks:** If a date cannot be parsed, we keep the raw string metadata rather than crashing. Corrupted blocks are skipped with detailed reporting to the user.

### 5. Text Hygiene Pipeline
All text passes through a cleaning pipeline before export:
1. **Unicode NFC Normalization** – fixes accented characters for cross-platform search.
2. **BOM/Zero-Width Space Removal** – strips invisible corruption.
3. **De-hyphenation** – rejoins words broken by PDF line wraps.
4. **Space Normalization** – collapses multiple spaces, removes spaces before punctuation.
5. **Auto-Capitalization** – capitalizes sentence fragments (unless they start with `...`).
6. **Title Polishing** – removes edition markers, file extensions, and other metadata clutter from book titles.

### 6. Joplin JEX Format
We chose direct `.jex` generation (TAR archive of Markdown files + JSON metadata) instead of using the Joplin API.
- **Why?** Simpler, offline, faster, and allows setting internal IDs explicitly (which the API restricts in some endpoints).
- **Entities:** Notebooks, Notes, Tags, and Tag-Note Associations are all represented as typed dataclasses inheriting from `JoplinEntity`, ensuring structural correctness.

### 7. Configuration Management
A simple JSON-based config system (`config/config.json`) with:
- Merge-on-load semantics: missing keys fall back to sensible defaults.
- Global singleton pattern for easy access across all modules.
- Immediate persistence on changes (settings dialog saves instantly).
- Theme support (light/dark) via separate QSS stylesheets.

## Directory Structure

```text
├── domain/       # Data Models (Dataclasses, Enums)
├── parsers/      # Regex patterns & Text Parsing
├── services/     # Business Logic (Deduplication, Identity, Orchestration)
├── exporters/    # Output Formatters (Strategy Pattern)
├── ui/           # PyQt5 Interface (Threaded)
├── utils/        # Config, Logs, Text Cleaning
├── resources/    # Static assets (QSS, icons, language patterns)
├── tests/        # Unit & Integration Tests
└── config/       # User configuration (JSON)
```

## Future Considerations
- **SQLite Backend:** Transitioning to persistent storage for edit history and undo/redo support (see [Roadmap](../roadmap.md) Phase 2).
- **Joplin API Sync:** True 2-way sync would require Joplin API integration (see Roadmap Phase 5).
- **Streaming Parser:** For files >5MB, processing in chunks to avoid memory issues (see Roadmap Phase 3).

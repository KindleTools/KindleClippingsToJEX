# Architecture & Design Decisions

## Overview
**KindleClippingsToJEX** is a robust tool designed to parse Kindle `My Clippings.txt` files and convert them into Joplin Import Archives (`.jex`). The core philosophy is **Data Integrity** and **Idempotency**—ensuring that re-importing the same file does not create duplicates in Joplin.

## Core Design Decisions

### 1. Deterministic Identity (The ID Problem)
**Challenge:** Kindle clippings do not have inherent unique IDs. Joplin generates random UUIDs for new notes. Importing the same file twice results in duplicate notes.
**Solution:** We implement a **Deterministic ID Strategy**.
- **Logic:** `Hash(BookTitle + Location + ContentSnippet)`
- **Result:** The same highlight always generates the exact same ID. Joplin recognizes this ID and updates the existing note (or ignores it if identical) rather than creating a copy.
- **Reference:** `services.identity_service.IdentityService`

### 2. Domain-Driven Structure
The codebase follows a loose Hexagonal/Clean Architecture:
- **`domain/`**: Pure data classes (`Clipping`, `JoplinNote`). No logic, just data structures.
- **`parsers/`**: Logic to interpret raw messy text from Kindle. Handles encoding hell (UTF-8 w/ BOM, CP1252) and multi-language Regex.
- **`services/`**: Business logic. `DeduplicationService` and `ClippingsService` orchestrate the flow.
- **`exporters/`**: Adapters for output formats. Uses the **Strategy Pattern** (`BaseExporter`) to switch between JEX, JSON, CSV, MD easily.
- **`ui/`**: Presentation layer (PyQt5).

### 3. Resilience over Perfection
**Kindle formats are inconsistent.** Dates change format by language, separators vary, and file encodings differ.
- **Handling:** The `KindleClippingsParser` uses a "score-based" language detection logic and tries multiple encodings (`utf-8-sig`, `cp1252`, `latin-1`) sequentially.
- **Fallbacks:** If a date cannot be parsed, we keep the raw string metadata rather than crashing.

### 4. Joplin JEX Format
We chose direct `.jex` generation (TAR archive of Markdown files + JSON metadata) instead of using the Joplin API.
- **Why?** simpler, offline, faster, and allows setting internal IDs explicitly (which the API restricts in some endpoints).

## Directory Structure

```text
├── domain/       # Data Models (Dataclasses)
├── parsers/      # Regex patterns & Text Parsing
├── services/     # Business Logic (Deduplication, Identity)
├── exporters/    # Output Formatters (Polymorphism)
├── ui/           # PyQt5 Interface
├── utils/        # Config, Logs, Helpers
└── resources/    # Static assets (JSON, PNG, CSS)
```

## Future Considerations
- **Syncing:** Currently, this is a one-way import. True 2-way sync would require Joplin API integration.

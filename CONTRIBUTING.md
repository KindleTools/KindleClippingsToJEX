# Contributing to KindleClippingsToJEX

Thank you for your interest in contributing to KindleClippingsToJEX!

## Getting Started

1.  **Fork** the repository on GitHub.
2.  **Clone** your fork locally.
3.  Create a **virtual environment** and install dependencies:
    ```bash
    python -m venv .venv
    pip install -r requirements.txt
    ```

## Development Workflow
1.  Create a new **branch** for your feature or bugfix:
    ```bash
    git checkout -b feature/my-new-feature
    ```
2.  Make your changes. Please adhere to the existing code style and modular structure.
3.  **Validate** your changes. Run the quality suite to fix linting errors and run tests:
    ```bash
    # Fix style issues automatically
    ruff check --fix .
    ruff format .
    
    # Run tests
    python -m unittest discover tests
    ```
4.  Commit your changes with clear, descriptive messages.

## Pull Requests
1.  Push your branch to your fork.
2.  Open a **Pull Request** against the `main` branch.
3.  Describe your changes and the problem they solve.
4.  Ensure all checks (Quality & Build) pass on GitHub.

## Code Structure
-   **`domain/`**: Data classes (Clipping, Note) following DDD principles.
-   **`parsers/`**: Logic for reading and parsing Kindle text files.
-   **`services/`**: Application logic combining parsers and exporters.
-   **`exporters/`**: Logic for generating Joplin JEX files.
-   **`ui/`**: PyQt5 interfaces (Main Window, Dialogs).
-   **`config/`**: Configuration management. Use `config.sample.json` as a template.

## Languages

If you want to add support for a new language:
1.  Open `languages.json`.
2.  Add a new key with the language code (e.g., `ru`).
3.  Provide the regex patterns for `highlight`, `note`, `page`, `added`, and `location`.

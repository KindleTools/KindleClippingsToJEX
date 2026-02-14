# Contributing to KindleClippingsToJEX

First off, huge thanks for taking the time to contribute! 🙌

The following is a set of guidelines for contributing to KindleClippingsToJEX. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## 🛠️ Development Setup

This project uses modern Python packaging via `pyproject.toml`.

### 1. Requirements
- Python 3.10+
- Git

### 2. Setting up the Environment
We recommend using a virtual environment.

```bash
# Clone the repo
git clone https://github.com/KindleTools/KindleClippingsToJEX.git
cd KindleClippingsToJEX

# Create Virtual Env
python -m venv .venv

# Activate it
# Windows:
.\.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
```

### 3. Installing Dependencies

We distinguish between **Production** dependencies (needed to run the app) and **Development** dependencies (linting, testing, building).

**For Contributors (Install Everything):**
This command installs the package in editable mode along with dev tools (`ruff`, `pyinstaller`, `coverage`).
```bash
pip install -e .[dev]
```

**For Users (Minimal Install):**
```bash
pip install -r requirements.txt
```

---

## 🧪 Running Tests

We support `pytest` as the modern test runner (recommended).

```bash
# Run all tests (fast & pretty output)
pytest

# Check Coverage
coverage run -m pytest
coverage report -m
```

---

## 🛡️ Type Checking

We use [mypy](http://mypy-lang.org/) to prevent type errors. This is critical for keeping the codebase robust.

```bash
# Run type check
mypy .
```

---

## 🎨 Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting. It's fast and strict.

```bash
# Check for issues
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

Please ensure your code follows PEP 8 standards.

---

## 📦 Building Executables

To build the standalone `.exe` or binary for distribution:

```bash
# Windows
build_exe.bat

# Manual PyInstaller command (Cross-platform)
pyinstaller --name KindleToJex --onefile --windowed --add-data "resources;resources" --icon=resources/icon.ico main.py
```

---

## 🚀 Submitting Pull Requests

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/amazing-feature`.
3. Commit your changes.
4. Push to the branch: `git push origin feature/amazing-feature`.
5. Open a Pull Request.

Happy Coding! 🚀

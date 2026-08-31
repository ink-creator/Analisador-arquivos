# Project Analyzer

Desktop project analyzer built with Python + HTML/CSS/JavaScript + pywebview.

The application is intentionally read-only: it scans a selected folder, calculates project statistics and renders the result in a local desktop dashboard. It does **not** edit project files.

## Current features

- native folder picker through pywebview;
- maximized desktop window while keeping the normal title bar controls;
- file and directory counting;
- total byte size and average file size;
- physical line counting for text files;
- conservative binary-file detection;
- language detection by extension / special filename;
- language percentages by lines and by files;
- extension frequency;
- 10 largest files;
- maximum directory depth;
- empty-directory detection;
- recursive largest-directory calculation;
- nested project tree;
- **live search/filter for files and folders** in the tree;
- **Insights** page with empty files, large files, extension variety, unclassified files and scanner warnings;
- **TODO / FIXME / HACK detection in source-code comments**, including file path, line number and a short snippet;
- default ignored folders such as `node_modules`, `.git`, `.venv`, `dist`, and `build`;
- warnings for filesystem entries that could not be read;
- CLI mode for validating the analyzer without the GUI;
- automated tests.

## Structure

```text
analisador-projetos/
├── main.py
├── backend/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── scanner.py
│   ├── languages.py
│   ├── statistics.py
│   ├── content.py
│   └── config.py
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   ├── js/app.js
│   ├── js/charts.js
│   └── assets/
├── tests/
│   └── test_analyzer.py
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Run the analyzer without the interface

From the project directory:

```bash
python main.py --cli "C:\\Projects\\YourProject"
```

Full JSON output:

```bash
python main.py --cli "C:\\Projects\\YourProject" --json
```

This mode only uses the Python standard library.

## Run the desktop interface

Create and activate a virtual environment, then install the dependency:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The app opens maximized by default but is **not** exclusive fullscreen, so minimize, maximize/restore and close controls remain available.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Result contract

The backend returns a JSON-serializable dictionary with these top-level keys:

```text
project
summary
languages
extensions
largest_files
structure
markers
insights
tree
ignored
warnings
```

The frontend only renders this result; it contains no project-analysis logic.

### `markers`

Contains exact totals for source comment markers and a display list with path, line and snippet:

```json
{
  "counts": {"TODO": 3, "FIXME": 1, "HACK": 0},
  "total": 4,
  "files": 2,
  "items": []
}
```

Marker detection uses Python's tokenizer for Python comments and lightweight language-aware comment rules for supported source formats. This intentionally avoids treating ordinary documentation and most string literals as code markers.

### `insights`

Contains small project-health/organization signals such as:

- empty files;
- files at or above 512 KiB;
- files without a language classification;
- number of distinct extensions;
- filesystem scanner warnings.

## Design decisions

Language percentages use recognized source languages. `percent_by_lines` is based on readable physical lines and `percent_by_files` is based on recognized-language files. Binary files still count toward file count and total size, but not toward line totals.

Symlinked directories and files are skipped to avoid loops and accidentally scanning outside the selected project.

The file-tree search is performed entirely in JavaScript over the already returned tree, so searching does not re-scan the filesystem.

## Good next steps

1. Add a settings screen for ignored directories and custom exclusions.
2. Add JSON and Markdown report export.
3. Add progress/cancellation for very large repositories.
4. Add duplicate-file detection by hash.
5. Add an "Open in Explorer" action for selected files/folders.
6. Package the app with PyInstaller once the product behavior is stable.

## v1.2.1 startup fix

The desktop bridge exposes only the callable functions needed by JavaScript via `window.expose`.
It deliberately does not pass the native pywebview `Window` object through `js_api`, avoiding recursive serialization / `maximum recursion depth exceeded` errors on Windows/WebView2.

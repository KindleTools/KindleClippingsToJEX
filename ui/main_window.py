
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QSplitter, 
                            QTextEdit, QMessageBox, QStackedWidget, QAction, QProgressDialog, QFrame)
from PyQt5.QtCore import Qt, QTimer

from domain.models import Clipping
from parsers.kindle_parser import KindleClippingsParser
from services.clippings_service import ClippingsService
from ui.widgets import EmptyStateWidget, ClippingsTableWidget, SearchBar
from datetime import datetime

from ui.settings_dialog import SettingsDialog
from utils.config_manager import get_config_manager
from ui.threads import LoadFileThread, ExportThread
from PyQt5.QtCore import QFile, QTextStream

class MainWindow(QMainWindow):
    """
    The main application window for the Kindle Clippings Manager.
    
    Orchestrates the UI flow:
    - Empty state when no file is loaded.
    - Data view with Table + Editor when clippings are loaded.
    - Handles file loading (`My Clippings.txt`) and export (`.jex`).
    """
    def __init__(self):
        super().__init__()
        self.config = get_config_manager()
        self.setWindowTitle("Kindle Clippings Manager")
        self.resize(1200, 800)
        
        self.clippings = []
        
        # Set Window Icon
        from PyQt5.QtGui import QIcon
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, '..', 'resources', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setup_ui()
        self.apply_styles()

        # Enable Drag & Drop
        self.setAcceptDrops(True)
        
        # Connect Empty State Click
        self.empty_page.clicked.connect(self.load_file_dialog)
        
        # Defer auto-load check to allow UI to show up first
        QTimer.singleShot(100, self.check_autoload)

    def setup_ui(self):
        """Initializes all UI components (layouts, widgets, connections)."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(15)

        # Header Area
        self._setup_header()

        # Content Area (Stacked Widget to switch between Empty and Data views)
        self.stack = QStackedWidget()
        
        # Page 1: Empty State
        self.empty_page = EmptyStateWidget()
        self.stack.addWidget(self.empty_page)
        
        # Page 2: Data View
        self.data_page = QWidget()
        self.data_layout = QVBoxLayout(self.data_page)
        self.data_layout.setContentsMargins(0, 0, 0, 0)
        self.data_layout.setSpacing(10)
        
        # --- Stats Panel ---
        self.stats_panel = self._create_stats_panel()
        self.data_layout.addWidget(self.stats_panel)
        
        # --- Search Bar Area ---
        search_layout = QHBoxLayout()
        self.search_bar = SearchBar()
        self.search_bar.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_bar)
        self.data_layout.addLayout(search_layout)

        # --- Splitter (Table + Editor) ---
        self.splitter = QSplitter(Qt.Vertical)
        
        self.table = ClippingsTableWidget()
        self.table.row_selected.connect(self.on_table_row_selected)
        # Connect signal to update STATS label, not button
        self.table.rows_filtered.connect(self.update_stats_label)
        # Connect context menu export signal
        self.table.request_export_selection.connect(self.export_selection_handler)
        
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("Select a note to edit...")
        self.text_editor.setStyleSheet("font-family: 'Segoe UI', sans-serif; font-size: 14px; line-height: 1.5;")
        self.text_editor.textChanged.connect(self.sync_editor_to_table)
        
        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.text_editor)
        self.splitter.setSizes([500, 150])
        
        self.data_layout.addWidget(self.splitter)
        self.stack.addWidget(self.data_page)
        
        self.main_layout.addWidget(self.stack)

    def _create_stats_panel(self):
        """Creates the horizontal stats bar."""
        panel = QFrame()
        panel.setObjectName("statsPanel")
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Helper to create standardized labels
        def create_stat_label(default_text):
            lbl = QLabel(default_text)
            lbl.setObjectName("statValue")
            lbl.setAlignment(Qt.AlignCenter)
            return lbl

        self.lbl_stat_total = create_stat_label("0\nHighlights")
        self.lbl_stat_books = create_stat_label("0\nBooks")
        self.lbl_stat_authors = create_stat_label("0\nAuthors")
        self.lbl_stat_tags = create_stat_label("0\nTags")
        self.lbl_stat_time = create_stat_label("0\nDays")
        
        for lbl in [self.lbl_stat_total, self.lbl_stat_books, self.lbl_stat_authors, self.lbl_stat_tags, self.lbl_stat_time]:
            layout.addWidget(lbl)
            
        return panel

    def update_insight_stats(self, clippings):
        """Calculates and updates the stats panel."""
        total = len(clippings)
        unique_books = len(set(c.book_title for c in clippings))
        unique_authors = len(set(c.author for c in clippings))
        
        # Count unique non-empty tags
        all_tags = set()
        for c in clippings:
            for t in c.tags:
                clean = t.strip()
                if clean:
                    all_tags.add(clean)
        unique_tags = len(all_tags)
        
        # Calculate Time Span
        days_span = 0
        if clippings:
            dates = [c.date_time for c in clippings if c.date_time]
            if dates:
                min_date = min(dates)
                max_date = max(dates)
                days_span = (max_date - min_date).days

        # Update labels (Structure only, styling via QSS)
        def fmt(val, label):
             return f"<html><head/><body><p align='center'><span style='font-size:18px; font-weight:600;'>{val}</span><br/><span style='font-size:12px; opacity:0.75;'>{label}</span></p></body></html>"

        self.lbl_stat_total.setText(fmt(total, "Highlights"))
        self.lbl_stat_books.setText(fmt(unique_books, "Books"))
        self.lbl_stat_authors.setText(fmt(unique_authors, "Authors"))
        self.lbl_stat_tags.setText(fmt(unique_tags, "Tags"))
        self.lbl_stat_time.setText(fmt(days_span, "Days Span"))

    def _setup_header(self):
        """Constructs the top header with title and action buttons."""
        header = QHBoxLayout()
        
        title_box = QVBoxLayout()
        lbl_title = QLabel("Kindle ➜ Joplin")
        lbl_title.setObjectName("h1")
        
        # Stats Label (replaces static subtitle)
        self.lbl_stats = QLabel("No file loaded")
        self.lbl_stats.setObjectName("subtitle")
        
        title_box.addWidget(lbl_title)
        title_box.addWidget(self.lbl_stats)
        
        header.addLayout(title_box)
        header.addStretch()
        
        # Buttons
        self.btn_load = QPushButton("Open File")
        self.btn_load.clicked.connect(self.load_file_dialog)
        self.btn_load.setCursor(Qt.PointingHandCursor)
        
        self.btn_export = QPushButton("Export to JEX")
        self.btn_export.clicked.connect(self.export_jex)
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setEnabled(False)
        self.btn_export.setObjectName("primaryBtn")
        
        self.btn_theme = QPushButton("🌗")
        self.btn_theme.setFixedSize(40, 36)
        self.btn_theme.setToolTip("Toggle Dark Mode")
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.btn_theme.setCursor(Qt.PointingHandCursor)

        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setFixedSize(40, 36) # Squaresh
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        
        header.addWidget(self.btn_load)
        header.addWidget(self.btn_export)
        header.addWidget(self.btn_theme)
        header.addWidget(self.btn_settings)
        
        self.main_layout.addLayout(header)

    def toggle_theme(self):
        """Switches between light and dark mode."""
        current = self.config.get("theme", "light") # Default to light
        new_theme = "dark" if current == "light" else "light"
        self.config.set("theme", new_theme)
        self.apply_styles()

    def open_settings(self):
        """Opens the Settings Dialog."""
        old_lang = self.config.get("language", "auto")
        dlg = SettingsDialog(self)
        if dlg.exec_():
            new_lang = self.config.get("language", "auto")
            if old_lang != new_lang and self.clippings:
                 reply = QMessageBox.question(self, "Language Changed", 
                                            "You changed the language setting. Do you want to reload the current file?",
                                            QMessageBox.Yes | QMessageBox.No)
                 if reply == QMessageBox.Yes:
                     self.load_file(self.config.get('input_file'))

    def check_autoload(self):
        """Checks for configured input file or connected Kindle."""
        input_file = self.config.get('input_file', "")
        if input_file and os.path.exists(input_file):
            self.load_file(input_file)
            return

        # Fallback to hardcoded default if config not set
        default_path = os.path.join("data", "My Clippings.txt")
        if os.path.exists(default_path):
            self.load_file(default_path)
            return

        # Try to detect Kindle
        kindle_path = self.detect_kindle()
        if kindle_path:
            self.empty_page.set_kindle_mode(kindle_path)
            # Override local function to just load this file if clicked
            self.empty_page.clicked.disconnect()
            self.empty_page.clicked.connect(lambda: self.load_file(kindle_path))

    def detect_kindle(self):
        """Scans connected drives for Kindle's My Clippings.txt."""
        import string
        drives = [f"{d}:\\" for d in string.ascii_uppercase if d not in "ABC"]
        for drive in drives:
            # Check widely common paths
            candidates = [
                os.path.join(drive, "documents", "My Clippings.txt"),
                os.path.join(drive, "Kindle", "documents", "My Clippings.txt") 
            ]
            for c in candidates:
                if os.path.exists(c):
                    return c
        return None

    def load_file_dialog(self):
        """Opens a file dialog for the user to select the clippings file."""
        current_input = self.config.get('input_file', "")
        start_dir = os.path.dirname(current_input) if current_input else ""
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", start_dir, "Text Files (*.txt)")
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        """Parses the file and updates the UI using a background thread."""
        self.progress = QProgressDialog("Loading highlights...", None, 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setMinimumDuration(0)
        self.progress.setCancelButton(None)
        self.progress.show()
        
        self.config.set('input_file', file_path)
        lang = self.config.get('language', 'auto')
        
        self.loader_thread = LoadFileThread(file_path, lang)
        self.loader_thread.finished.connect(self.on_load_finished)
        self.loader_thread.error.connect(self.on_load_error)
        self.loader_thread.start()

    def on_load_finished(self, clippings):
        self.progress.close()
        self.clippings = clippings
        self.table.populate(self.clippings)
        self.stack.setCurrentWidget(self.data_page)
        self.btn_export.setEnabled(True)
        self.update_stats_label(len(clippings))
        self.update_insight_stats(clippings)

    def on_load_error(self, error_msg):
        self.progress.close()
        QMessageBox.critical(self, "Error", f"Error reading file:\n{error_msg}")

    def update_stats_label(self, visible_count):
        """Updates the subtitle label with the count of visible/total items."""
        total = self.table.rowCount()
        self.lbl_stats.setText(f"Showing {visible_count} of {total} highlights")

    def on_table_row_selected(self, content):
        """Updates the bottom text editor when a table row is selected."""
        self.text_editor.blockSignals(True)
        self.text_editor.setText(content)
        self.text_editor.blockSignals(False)

    def sync_editor_to_table(self):
        """Syncs changes from the text editor back to the table model."""
        current_row = self.table.currentRow()
        new_text = self.text_editor.toPlainText()
        self.table.update_content_from_editor(current_row, new_text)

    def on_search(self, text):
        """Filters the table based on search query."""
        self.table.filter_rows(text)

    def export_selection_handler(self, rows):
        """Handler for 'Export Selected' context menu action."""
        if rows:
            self.perform_export(rows, f"Export Selected ({len(rows)})")

    def export_jex(self):
        """Handler for the main 'Export to JEX' button (exports visible rows)."""
        rows = []
        for r in range(self.table.rowCount()):
            if not self.table.isRowHidden(r):
                rows.append(r)
        
        self.perform_export(rows, "Export Visible")

    def perform_export(self, rows_indices, title="Export"):
        """
        Executes the export logic for a given list of row indices.
        """
        if not rows_indices:
            return

        default_output = self.config.get("output_file", "import_clippings")
        if not default_output.endswith('.jex'):
             default_output += ".jex"

        file_path, _ = QFileDialog.getSaveFileName(self, title, default_output, "Joplin Export (*.jex)")
        if not file_path:
            return
            
        # Prepare data in main thread (fast) to avoid thread safety issues with UI widgets
        try:
            export_list = self.table.get_clippings_from_rows(rows_indices)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to prepare data: {e}")
            return

        # Start Export Thread
        self.progress = QProgressDialog("Exporting...", None, 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setMinimumDuration(0)
        self.progress.setCancelButton(None)
        self.progress.show()

        service = ClippingsService(language_code=self.config.get('language', 'auto'))
        
        self.export_thread = ExportThread(
            service=service,
            clippings=export_list,
            output_file=file_path,
            root_notebook=self.config.get('notebook_title', 'Kindle Imports'),
            location=tuple(self.config.get('location', [0,0,0])),
            creator=self.config.get('creator', 'System')
        )
        self.export_thread.finished.connect(self.on_export_finished)
        self.export_thread.error.connect(self.on_export_error)
        self.export_thread.start()

    def on_export_finished(self, count):
        self.progress.close()
        self.statusBar().showMessage(f"Successfully exported {count} notes.", 5000)
        # Optional: Flash the export button or something similar if desired, 
        # but status bar is standard for "zen" apps.

    def on_export_error(self, msg):
        self.progress.close()
        QMessageBox.critical(self, "Error", msg)

    def dragEnterEvent(self, event):
        """Handle file drag enter events."""
        if event.mimeData().hasUrls():
            # Accept if at least one file is a text file
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.txt'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        """Handle file drop events."""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.exists(file_path) and file_path.lower().endswith('.txt'):
                self.load_file(file_path)
                break

    def apply_styles(self):
        """Applies global CSS styles based on current theme."""
        import os
        theme = self.config.get("theme", "light")
        filename = "styles_dark.qss" if theme == "dark" else "styles.qss"
        
        # Relative path to resources
        current_dir = os.path.dirname(os.path.abspath(__file__))
        style_path = os.path.join(current_dir, '..', 'resources', filename)
        
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        else:
             print(f"Warning: Stylesheet not found at {style_path}")

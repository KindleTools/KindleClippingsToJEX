
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QSplitter, 
                            QTextEdit, QMessageBox, QStackedWidget, QAction, QProgressDialog)
from PyQt5.QtCore import Qt, QTimer

from domain.models import Clipping
from parsers.kindle_parser import KindleClippingsParser
from services.clippings_service import ClippingsService
from ui.widgets import EmptyStateWidget, ClippingsTableWidget, SearchBar
from datetime import datetime

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
        self.setWindowTitle("Kindle Clippings Manager")
        self.resize(1200, 800)
        
        self.clippings = []
        
        self.setup_ui()
        self.apply_styles()
        
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
        
        header.addWidget(self.btn_load)
        header.addWidget(self.btn_export)
        
        self.main_layout.addLayout(header)

    def check_autoload(self):
        """Checks for 'data/My Clippings.txt' and loads it if exists."""
        default_path = os.path.join("data", "My Clippings.txt")
        if os.path.exists(default_path):
            self.load_file(default_path)

    def load_file_dialog(self):
        """Opens a file dialog for the user to select the clippings file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Text Files (*.txt)")
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        """Parses the file and updates the UI."""
        progress = QProgressDialog("Loading highlights...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        # Force UI update
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            # TODO: Make language configurable via settings
            parser = KindleClippingsParser(language_code='es')
            self.clippings = parser.parse_file(file_path)
            
            self.table.populate(self.clippings)
            self.stack.setCurrentWidget(self.data_page)
            self.btn_export.setEnabled(True)
            
            # Initial stat update happens via signal from populate()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reading file:\n{str(e)}")
        finally:
            progress.close()

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
        Generates the list of Clipping enumerations and calls the service.
        """
        if not rows_indices:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, title, "", "Joplin Export (*.jex)")
        if not file_path:
            return
            
        # Loading indicator for export too
        progress = QProgressDialog("Exporting...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            export_list = []
            for r in rows_indices:
                # Retrieve data from table columns
                d_str = self.table.item(r, 0).text()
                try:
                    dt = datetime.strptime(d_str, '%Y-%m-%d %H:%M')
                except:
                    dt = datetime.now()
                
                # Use UserRole for full content
                content = self.table.item(r, 3).data(Qt.UserRole)
                tags_str = self.table.item(r, 5).text()
                tags_list = [t.strip() for t in tags_str.split(',') if t.strip()]
                
                c = Clipping(
                    content=content,
                    book_title=self.table.item(r, 1).text(),
                    author=self.table.item(r, 2).text(),
                    page=self.table.item(r, 4).text(),
                    date_time=dt,
                    tags=tags_list
                )
                export_list.append(c)

            service = ClippingsService(language_code='es')
            service.process_clippings_from_list(
                clippings=export_list,
                output_file=file_path,
                root_notebook_name="Kindle Imports",
                location=(0,0,0),
                creator_name="KindleManager"
            )
            progress.close()
            QMessageBox.information(self, "Export Complete", f"Successfully exported {len(export_list)} notes.")
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", str(e))

    def apply_styles(self):
        """Applies global CSS styles to the window components."""
        self.setStyleSheet("""
            QMainWindow { background-color: #f8f9fa; }
            QLabel#h1 { font-size: 22px; font-weight: bold; color: #2c3e50; }
            QLabel#subtitle { font-size: 14px; color: #666; margin-top: 4px; }
            QPushButton {
                background-color: white;
                border: 1px solid #dcdcdc;
                padding: 8px 16px;
                border-radius: 4px;
                color: #333;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #f0f0f0; border-color: #bbb; }
            QPushButton#primaryBtn {
                background-color: #007bff;
                color: white;
                border: 1px solid #0056b3;
            }
            QPushButton#primaryBtn:hover { background-color: #0069d9; }
            QPushButton:disabled { background-color: #e9ecef; color: #adb5bd; border-color: #e9ecef; }
            QTextEdit { border: 1px solid #ddd; background: white; padding: 10px; border-radius: 4px; }
            QSplitter::handle { background-color: #e0e0e0; height: 1px; }
        """)

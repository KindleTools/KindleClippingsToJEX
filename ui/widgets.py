
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QAbstractItemView, QLineEdit, QStyledItemDelegate, 
                            QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QItemSelectionModel

class EmptyStateWidget(QWidget):
    """
    Widget displayed when no clippings are loaded.
    Shows a welcoming icon and instruction to load a file.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.icon_label = QLabel()
        import os
        from PyQt5.QtGui import QPixmap
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, '..', 'resources', 'icon.png')
        if os.path.exists(icon_path):
             pixmap = QPixmap(icon_path).scaled(84, 84, Qt.KeepAspectRatio, Qt.SmoothTransformation)
             self.icon_label.setPixmap(pixmap)
        else:
             self.icon_label.setText("📚")
             self.icon_label.setStyleSheet("font-size: 64px; margin-bottom: 20px;")
             
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        self.msg_label = QLabel("Your Kindle library is waiting")
        self.msg_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        self.msg_label.setAlignment(Qt.AlignCenter)
        
        self.sub_label = QLabel("Load your 'My Clippings.txt' file to start organizing your notes.")
        self.sub_label.setStyleSheet("font-size: 14px; color: #666; margin-top: 10px;")
        self.sub_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.msg_label)
        layout.addWidget(self.sub_label)

class SearchBar(QLineEdit):
    """
    Styled QLineEdit for searching/filtering the table.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("🔍 Search your notes...")
        self.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)

class ContentDelegate(QStyledItemDelegate):
    """
    Delegate for the Content column (Index 3).
    - When viewing: Displays truncated text "..."
    - When editing: Displays FULL text stored in Qt.UserRole.
    """
    def setEditorData(self, editor, index):
        full_text = index.data(Qt.UserRole)
        if full_text:
            editor.setText(full_text)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        new_text = editor.text()
        # Save full text to UserRole
        model.setData(index, new_text, Qt.UserRole)
        # Create preview for DisplayRole
        preview = new_text[:100].replace('\n', ' ') + "..." if len(new_text) > 100 else new_text
        model.setData(index, preview, Qt.DisplayRole)

class ClippingsTableWidget(QTableWidget):
    """
    Custom TableWidget to display clippings.
    Features:
    - Custom editing delegate for long content.
    - Sorting and Filtering.
    - Context Menu (Delete/Duplicate/Export Selected).
    - Signals for row selection and filter updates.
    """
    row_selected = pyqtSignal(str) 
    rows_filtered = pyqtSignal(int)
    request_export_selection = pyqtSignal(list) # Emits list of row indices to export

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Sets up columns, headers, selection behavior, and delegates."""
        columns = ["Date", "Book", "Author", "Content", "Page", "Tags"]
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Date
        header.setSectionResizeMode(1, QHeaderView.Interactive)      # Book
        header.setSectionResizeMode(2, QHeaderView.Interactive)      # Author
        header.setSectionResizeMode(3, QHeaderView.Stretch)          # Content
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Page
        header.setSectionResizeMode(5, QHeaderView.Interactive)      # Tags
        
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.itemSelectionChanged.connect(self._on_selection_change)
        
        # Apply delegate to 'Content' column
        self.setItemDelegateForColumn(3, ContentDelegate(self))
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        self.itemChanged.connect(self._on_item_changed)
        
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #000;
            }
        """)
        
        self._is_updating = False

    def _on_selection_change(self):
        """Emits signal with content of the last selected row for the editor."""
        if self.currentRow() >= 0:
            item = self.item(self.currentRow(), 3)
            if item:
                full_text = item.data(Qt.UserRole)
                if not full_text: 
                    full_text = item.text()
                self.row_selected.emit(full_text)

    def _on_item_changed(self, item):
        """Handle inline edits. Updates editor if current row changed."""
        if self._is_updating: 
            return
            
        if item.column() == 3:
            if self.currentRow() == item.row():
                full_text = item.data(Qt.UserRole)
                self.row_selected.emit(full_text)

    def update_content_from_editor(self, row, new_text):
        """Updates the table model (UserRole + DisplayPreview) from external editor."""
        if row < 0 or row >= self.rowCount():
            return
            
        self._is_updating = True 
        item = self.item(row, 3) 
        if item:
            preview = new_text[:100].replace('\n', ' ') + "..." if len(new_text) > 100 else new_text
            item.setText(preview)
            item.setData(Qt.UserRole, new_text)
        self._is_updating = False

    def populate(self, clippings):
        """Fills the table with Clipping objects."""
        self._is_updating = True
        self.setSortingEnabled(False)
        self.setRowCount(len(clippings))
        
        for row, clip in enumerate(clippings):
            date_str = clip.date_time.strftime('%Y-%m-%d %H:%M') if clip.date_time else ""
            date_item = QTableWidgetItem(date_str)
            # Store full object for robust retrieval
            date_item.setData(Qt.UserRole, clip)
            self.setItem(row, 0, date_item)
            
            self.setItem(row, 1, QTableWidgetItem(clip.book_title))
            self.setItem(row, 2, QTableWidgetItem(clip.author))
            
            # Content: full in UserRole, truncated in Text
            preview = clip.content[:100].replace('\n', ' ') + "..." if len(clip.content) > 100 else clip.content
            item_text = QTableWidgetItem(preview)
            item_text.setToolTip(clip.content)
            item_text.setData(Qt.UserRole, clip.content)
            self.setItem(row, 3, item_text)
            
            self.setItem(row, 4, QTableWidgetItem(str(clip.page)))
            
            tags_str = ", ".join(clip.tags)
            self.setItem(row, 5, QTableWidgetItem(tags_str))
            
        self.setSortingEnabled(True)
        self._is_updating = False
        self.rows_filtered.emit(len(clippings))

    def filter_rows(self, text):
        """Filters rows by loose match in ANY visible column."""
        text = text.lower()
        visible_count = 0
        for row in range(self.rowCount()):
            show = False
            book = self.item(row, 1).text().lower()
            author = self.item(row, 2).text().lower()
            content_item = self.item(row, 3)
            content = content_item.data(Qt.UserRole).lower() if content_item else ""
            tags = self.item(row, 5).text().lower()
            
            if text in book or text in author or text in content or text in tags:
                show = True
                visible_count += 1
                
            self.setRowHidden(row, not show)
        
        self.rows_filtered.emit(visible_count)

    def show_context_menu(self, position):
        """Shows context menu for Delete, Duplicate, and Export Selected."""
        menu = QMenu()
        
        rows = sorted(set(item.row() for item in self.selectedItems()))
        # Filter hidden rows (just in case)
        rows = [r for r in rows if not self.isRowHidden(r)]
        
        if not rows:
            return

        export_action = QAction(f"Export Selected ({len(rows)})", self)
        # Emit signal to parent to handle export, as MainWindow holds the Service/File Dialog logic
        export_action.triggered.connect(lambda: self.request_export_selection.emit(rows))
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        dupe_action = QAction("Duplicate Row(s)", self)
        dupe_action.triggered.connect(lambda: self.duplicate_rows(rows))
        menu.addAction(dupe_action)
        
        del_action = QAction(f"Delete Row(s)", self)
        del_action.triggered.connect(lambda: self.delete_rows(rows))
        menu.addAction(del_action)
        
        menu.exec_(self.viewport().mapToGlobal(position))

    def delete_rows(self, rows):
        """Deletes specified rows from the table."""
        self._is_updating = True 
        for row in sorted(rows, reverse=True):
            self.removeRow(row)
        self._is_updating = False
        
        # Recalculate stats
        visible = 0
        for r in range(self.rowCount()):
            if not self.isRowHidden(r):
                visible += 1
        self.rows_filtered.emit(visible)

    def duplicate_rows(self, rows):
        """Duplicates specified rows and appends them to the end."""
        self._is_updating = True
        self.setSortingEnabled(False)
        try:
            for row in rows:
                new_row = self.rowCount()
                self.insertRow(new_row)
                for col in range(self.columnCount()):
                    item = self.item(row, col)
                    if item:
                        new_item = QTableWidgetItem(item)
                        self.setItem(new_row, col, new_item)
                        # Deep copy UserRole for content
                        if col == 3:
                           new_item.setData(Qt.UserRole, item.data(Qt.UserRole))
        finally:
            self.setSortingEnabled(True)
            self._is_updating = False
            
        # Recalculate stats
        visible = 0
        for r in range(self.rowCount()):
            if not self.isRowHidden(r):
                visible += 1
        self.rows_filtered.emit(visible)

    def get_clippings_from_rows(self, row_indices):
        """
        Extracts Clipping objects for the specified rows.
        Applies any pending edits found in the 'Content' column.
        """
        from dataclasses import replace
        clippings = []
        for r in row_indices:
            # Retrieve full object from 1st column UserRole
            item_0 = self.item(r, 0)
            if not item_0: continue
            
            original_clip = item_0.data(Qt.UserRole)
            if not original_clip: continue
            
            # Retrieve potentially edited content from Content column UserRole
            item_content = self.item(r, 3)
            edited_content = item_content.data(Qt.UserRole) if item_content else None
            
            if edited_content is not None:
                # Create final object with edited content
                final_clip = replace(original_clip, content=edited_content)
                clippings.append(final_clip)
            else:
                clippings.append(original_clip)
                
        return clippings

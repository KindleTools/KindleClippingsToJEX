
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QAbstractItemView, QLineEdit, QStyledItemDelegate, 
                            QMenu, QAction, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
import os
import json
import csv
import io

class EmptyStateWidget(QWidget):
    """
    Widget displayed when no clippings are loaded.
    Shows a welcoming icon and instruction to load a file.
    """
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter) # type: ignore
        
        self.icon_label = QLabel()
        from utils.config_manager import get_config_manager
        from PyQt5.QtGui import QPixmap
        
        icon_path = get_config_manager().get_resource_path('icon.png')
        if os.path.exists(icon_path):
             pixmap = QPixmap(icon_path).scaled(84, 84, Qt.KeepAspectRatio, Qt.SmoothTransformation) # type: ignore
             self.icon_label.setPixmap(pixmap)
        else:
             self.icon_label.setText("📚")
             self.icon_label.setStyleSheet("font-size: 64px; margin-bottom: 20px;")
             
        self.icon_label.setAlignment(Qt.AlignCenter) # type: ignore
        
        self.msg_label = QLabel("Your Kindle library is waiting")
        self.msg_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        self.msg_label.setAlignment(Qt.AlignCenter) # type: ignore
        
        self.sub_label = QLabel("Load your 'My Clippings.txt' file to start organizing your notes.")
        self.sub_label.setStyleSheet("font-size: 14px; color: #666; margin-top: 10px;")
        self.sub_label.setAlignment(Qt.AlignCenter) # type: ignore
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.msg_label)
        layout.addWidget(self.sub_label)
        
        # Make it look clickable
        self.setCursor(Qt.PointingHandCursor) # type: ignore

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: # type: ignore
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_kindle_mode(self, path):
        """Updates the UI to show a detected Kindle."""
        self.msg_label.setText("Kindle Detected!")
        self.sub_label.setText(f"Found 'My Clippings.txt' at:\n{path}\n\nClick anywhere to load it.")


class SearchBar(QLineEdit):
    """
    Styled QLineEdit for searching/filtering the table.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("🔍 Search your notes...")
        # Inline styles removed to clearer global QSS usage


class CustomEditorDelegate(QStyledItemDelegate):
    """
    Base delegate to customize the edition widget (QLineEdit/QTextEdit).
    Provides better spacing, font size, and visual comfort.
    """
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            # Enforce some padding and minimum height for comfort
            # Enforce some padding and minimum height for comfort
            # Style is now handled globally in .qss files via QLineEdit selector
            pass
        return editor

    def updateEditorGeometry(self, editor, option, index):
        # Allow the editor to be slightly larger than the cell if needed, or just fill it properly
        rect = option.rect
        editor.setGeometry(rect)

class ContentDelegate(CustomEditorDelegate):
    """
    Delegate for the Content column (Index 3).
    - When viewing: Displays truncated text "..."
    - When editing: Displays FULL text stored in Qt.UserRole.
    """
    def setEditorData(self, editor, index):
        full_text = index.data(Qt.UserRole) # type: ignore
        if full_text:
            editor.setText(full_text)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        new_text = editor.text()
        # Save full text to UserRole
        model.setData(index, new_text, Qt.UserRole) # type: ignore
        # Create preview for DisplayRole
        preview = new_text[:100].replace('\n', ' ') + "..." if len(new_text) > 100 else new_text
        model.setData(index, preview, Qt.DisplayRole) # type: ignore

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
    status_message = pyqtSignal(str, int) # message, duration_ms

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Sets up columns, headers, selection behavior, and delegates."""
        columns = ["Date", "Book", "Author", "Content", "Page", "Tags"]
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        header = self.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # type: ignore
            header.setSectionResizeMode(1, QHeaderView.Interactive)      # type: ignore
            header.setSectionResizeMode(2, QHeaderView.Interactive)      # type: ignore
            header.setSectionResizeMode(3, QHeaderView.Stretch)          # type: ignore
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # type: ignore
            header.setSectionResizeMode(5, QHeaderView.Interactive)      # type: ignore
        
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.itemSelectionChanged.connect(self._on_selection_change)
        
        # Apply delegates
        # Content (Col 3) gets special handling
        self.setItemDelegateForColumn(3, ContentDelegate(self))
        
        # Book(1), Author(2), Tags(5) get the styled editor
        styled_delegate = CustomEditorDelegate(self)
        self.setItemDelegateForColumn(1, styled_delegate)
        self.setItemDelegateForColumn(2, styled_delegate)
        self.setItemDelegateForColumn(5, styled_delegate)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu) # type: ignore
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
                full_text = item.data(Qt.UserRole) # type: ignore
                if not full_text: 
                    full_text = item.text()
                self.row_selected.emit(full_text)

    def _on_item_changed(self, item):
        """Handle inline edits. Updates editor if current row changed."""
        if self._is_updating: 
            return
            
        col = item.column()
        
        # Metadata Columns (Book=1, Author=2)
        if col in [1, 2]:
            old_val = item.data(Qt.UserRole) # type: ignore
            new_val = item.text().strip()
            
            # If changed and valid
            if old_val and new_val and old_val != new_val:
                from PyQt5.QtWidgets import QMessageBox
                count = 0
                # Check how many others match
                for r in range(self.rowCount()):
                    if r == item.row(): continue
                    other_item = self.item(r, col)
                    if other_item and other_item.data(Qt.UserRole) == old_val: # type: ignore
                        count += 1
                
                if count > 0:
                    field = "Book Title" if col == 1 else "Author"
                    reply = QMessageBox.question(
                        self, 
                        f"Bulk Update {field}",
                        f"You changed '{old_val}' to '{new_val}'.\n\nDo you want to update this for the other {count} notes?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        self._is_updating = True # Block signals
                        for r in range(self.rowCount()):
                            target_item = self.item(r, col)
                            if target_item and target_item.data(Qt.UserRole) == old_val: # type: ignore
                                target_item.setText(new_val)
                                target_item.setData(Qt.UserRole, new_val) # type: ignore
                        self._is_updating = False

            # Update current item's UserRole to accept the change
            item.setData(Qt.UserRole, new_val) # type: ignore

        # Content Column (3)
        if col == 3:
            if self.currentRow() == item.row():
                full_text = item.data(Qt.UserRole) # type: ignore
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
            item.setData(Qt.UserRole, new_text) # type: ignore
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
            date_item.setData(Qt.UserRole, clip) # type: ignore
            self.setItem(row, 0, date_item)
            
            # Store plain text in UserRole for Bulk Edit detection
            book_item = QTableWidgetItem(clip.book_title)
            book_item.setData(Qt.UserRole, clip.book_title) # type: ignore
            self.setItem(row, 1, book_item)
            
            author_item = QTableWidgetItem(clip.author)
            author_item.setData(Qt.UserRole, clip.author) # type: ignore
            self.setItem(row, 2, author_item)
            
            # Content: full in UserRole, truncated in Text
            preview = clip.content[:100].replace('\n', ' ') + "..." if len(clip.content) > 100 else clip.content
            item_text = QTableWidgetItem(preview)
            item_text.setToolTip(clip.content)
            item_text.setData(Qt.UserRole, clip.content) # type: ignore
            self.setItem(row, 3, item_text)
            
            self.setItem(row, 4, QTableWidgetItem(str(clip.page)))
            
            tags_str = ", ".join(clip.tags)
            self.setItem(row, 5, QTableWidgetItem(tags_str))

            # Apply visual style for Duplicates
            if clip.is_duplicate:
                from PyQt5.QtGui import QColor
                for col in range(self.columnCount()):
                    item = self.item(row, col)
                    if item:
                        # Dim color
                        item.setForeground(QColor("#A0A0A0")) # Mid-grey
                        # Strikeout
                        font = item.font()
                        font.setStrikeOut(True)
                        item.setFont(font)
                        # Tooltip explanation
                        item.setToolTip("Marked as duplicate (subset or older edit).")
            
        self.setSortingEnabled(True)
        self._is_updating = False
        self.rows_filtered.emit(len(clippings))

    def filter_rows(self, text):
        """Filters rows by loose match in ANY visible column."""
        text = text.lower()
        visible_count = 0
        for row in range(self.rowCount()):
            show = False
            item_book = self.item(row, 1)
            book = item_book.text().lower() if item_book else ""
            
            item_author = self.item(row, 2)
            author = item_author.text().lower() if item_author else ""
            
            content_item = self.item(row, 3)
            content = ""
            if content_item:
                content_data = content_item.data(Qt.UserRole) # type: ignore
                content = content_data.lower() if content_data else ""
                
            item_tags = self.item(row, 5)
            tags = item_tags.text().lower() if item_tags else ""
            
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
        
        del_action = QAction("Delete Row(s)", self)
        del_action.triggered.connect(lambda: self.delete_rows(rows))
        menu.addAction(del_action)
        
        # Copy Actions
        menu.addSeparator()
        
        copy_csv_action = QAction("Copy as CSV", self)
        copy_csv_action.triggered.connect(lambda: self.copy_to_clipboard_csv(rows))
        menu.addAction(copy_csv_action)
        
        copy_json_action = QAction("Copy as JSON", self)
        copy_json_action.triggered.connect(lambda: self.copy_to_clipboard_json(rows))
        menu.addAction(copy_json_action)
        
        md_label = "Copy as Markdown"
        copy_md_action = QAction(md_label, self)
        copy_md_action.triggered.connect(lambda: self.copy_to_clipboard_md(rows))
        menu.addAction(copy_md_action)

        # Removed 'Clean Up' as requested per user feedback (redundant with main button)
        
        vp = self.viewport()
        if vp:
            menu.exec_(vp.mapToGlobal(position))

    def copy_to_clipboard_csv(self, rows):
        """Copies selected rows to clipboard as CSV string (Consistent with Export)."""
        clippings = self.get_clippings_from_rows(rows)
        if not clippings: return
        
        # Use Exporter logic
        from exporters.csv_exporter import CsvExporter
        exporter = CsvExporter()
        output_str = exporter.create_csv_string(clippings)
            
        cb = QApplication.clipboard()
        if cb:
            cb.setText(output_str)
        self.status_message.emit(f"✅ Copied {len(clippings)} rows as CSV", 3000)

    def copy_to_clipboard_json(self, rows):
        """Copies selected rows to clipboard as JSON string (Consistent with Export)."""
        clippings = self.get_clippings_from_rows(rows)
        if not clippings: return
        
        # Use Exporter logic
        from exporters.json_exporter import JsonExporter
        # We can pass context locally if we knew it, or just partial defaults
        exporter = JsonExporter()
        output_str = exporter.create_json_string(clippings, context={"creator": "GUI Clipboard"})
            
        cb = QApplication.clipboard()
        if cb:
            cb.setText(output_str)
        self.status_message.emit(f"✅ Copied {len(clippings)} rows as JSON", 3000)

    def copy_to_clipboard_md(self, rows):
        """Copies selected rows to clipboard as Markdown text."""
        clippings = self.get_clippings_from_rows(rows)
        if not clippings: return
        
        # Use Exporter logic
        from exporters.markdown_exporter import MarkdownExporter
        exporter = MarkdownExporter()
        output_str = exporter.create_clipboard_markdown(clippings)
            
        cb = QApplication.clipboard()
        if cb:
            cb.setText(output_str)
        self.status_message.emit(f"✅ Copied {len(clippings)} rows as Markdown", 3000)

    def delete_all_duplicates(self, silent_if_none=False):
        """Removes all rows visually marked as duplicate. Returns count deleted."""
        rows_to_delete = []
        for r in range(self.rowCount()):
            # Check UserRole of column 0 to check the object
            item = self.item(r, 0)
            if item:
                clip = item.data(Qt.UserRole) # type: ignore
                if clip.is_duplicate:
                    rows_to_delete.append(r)
        
        if rows_to_delete:
            from PyQt5.QtWidgets import QMessageBox
            
            # Prepare detail report
            details_list = []
            for r in rows_to_delete:
                clip = self.item(r, 0).data(Qt.UserRole) # type: ignore
                snippet = clip.content[:300].replace('\n', ' ') + "..." if len(clip.content) > 300 else clip.content
                details_list.append(f"[{clip.entry_type.upper()}] {clip.book_title}\n{snippet}\n")
            
            detailed_text = "--- ITEMS TO BE REMOVED ---\n\n" + "\n".join(details_list)

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Cleanup Confirmation")
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setText(f"Found {len(rows_to_delete)} duplicate or redundant items.\n\n"
                            "These are either exact duplicates, subsets of other highlights, or empty noise.\n"
                            "Do you want to delete them all?")
            msg_box.setDetailedText(detailed_text)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.Yes)
            
            reply = msg_box.exec_()
            
            if reply == QMessageBox.Yes:
                self.delete_rows(rows_to_delete)
                return len(rows_to_delete)
        elif not silent_if_none:
             from PyQt5.QtWidgets import QMessageBox
             QMessageBox.information(self, "Cleanup", "No duplicates found to delete.")
        
        return 0

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
                           new_item.setData(Qt.UserRole, item.data(Qt.UserRole)) # type: ignore
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
            
            original_clip = item_0.data(Qt.UserRole) # type: ignore
            if not original_clip: continue
            
            # Retrieve potentially edited content
            # Column 1: Book Title
            item_book = self.item(r, 1)
            new_book = item_book.text().strip() if item_book else original_clip.book_title
            
            # Column 2: Author
            item_author = self.item(r, 2)
            new_author = item_author.text().strip() if item_author else original_clip.author

            # Column 3: Content (UserRole has full text)
            item_content = self.item(r, 3)
            new_content = None
            if item_content:
                new_content = item_content.data(Qt.UserRole) # type: ignore
            if not new_content:
                new_content = item_content.text() if item_content else original_clip.content
            
            # Column 5: Tags
            item_tags = self.item(r, 5)
            new_tags_str = item_tags.text().strip() if item_tags else ""
            # Parse tags back to set - Support comma and semicolon as separators in UI
            import re
            new_tags = list(set(t.strip() for t in re.split(r'[,;]', new_tags_str) if t.strip()))

            # Create final object with ALL edited fields
            final_clip = replace(original_clip, 
                               book_title=new_book,
                               author=new_author,
                               content=new_content,
                               tags=new_tags)
            
            clippings.append(final_clip)
                
        return clippings

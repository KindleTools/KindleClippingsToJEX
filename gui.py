import sys
import os
import copy
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
                            QPushButton, QVBoxLayout, QWidget, QFileDialog, QHeaderView, 
                            QMessageBox, QTextEdit, QHBoxLayout, QLabel, QSplitter,
                            QProgressDialog, QMenu, QAction, QLineEdit, QToolBar,
                            QStyledItemDelegate, QStyleOptionViewItem, QToolTip, QStyle)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QEvent
from PyQt5.QtGui import QIcon, QKeySequence

# Add parent dir to path to allow imports from src
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from domain.models import Clipping
from parsers.kindle_parser import KindleClippingsParser
from services.clippings_service import ClippingsService
from utils.logging_config import setup_logging

# Setup logging
logger = setup_logging()

class TextPreviewDelegate(QStyledItemDelegate):
    """Delegate personalizado para mostrar el texto con un formato específico"""
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter, option, index):
        """Personaliza la forma en que se pinta el texto"""
        text = index.model().data(index, Qt.DisplayRole)
        
        # Si la columna es la de texto (columna 2)
        if index.column() == 2:
            # Si el texto es muy largo, truncarlo y añadir "..."
            if text and len(text) > 100:
                text = text[:97] + "..."
        
        # Configurar la opción para pintar
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = text
        
        # Pintar usando el estilo del widget
        opt.widget.style().drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)
    
    def helpEvent(self, event, view, option, index):
        """Muestra un tooltip con el texto completo al pasar el ratón"""
        if event.type() == QEvent.ToolTip:
            text = index.model().data(index, Qt.DisplayRole)
            if text and len(text) > 100:
                QToolTip.showText(event.globalPos(), text, view)
                return True
        
        return super().helpEvent(event, view, option, index)

class KindleHighlightsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Procesador de Subrayados Kindle")
        self.setGeometry(100, 100, 1200, 800)
        
        self.clippings = [] # List of Clipping objects
        self.filtered_indexes = []  # Para guardar los índices filtrados al buscar
        
        # Widget y layout central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Crear layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Barra superior con botón de carga
        top_bar = QHBoxLayout()
        self.load_button = QPushButton("Recargar subrayados")
        self.load_button.clicked.connect(self.load_highlights)
        self.status_label = QLabel("Cargando subrayados...")
        top_bar.addWidget(self.load_button)
        top_bar.addWidget(self.status_label)
        
        # Añadir botón para agregar fila vacía
        self.add_row_button = QPushButton("Añadir fila")
        self.add_row_button.clicked.connect(self.add_empty_row)
        top_bar.addWidget(self.add_row_button)
        
        top_bar.addStretch()
        main_layout.addLayout(top_bar)
        
        # Añadir barra de búsqueda
        search_bar = QHBoxLayout()
        search_label = QLabel("Buscar:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Escriba para filtrar resultados...")
        self.search_input.textChanged.connect(self.filter_table)
        
        # Botón para resetear la búsqueda
        self.reset_search_button = QPushButton("Limpiar")
        self.reset_search_button.clicked.connect(self.reset_search)
        
        search_bar.addWidget(search_label)
        search_bar.addWidget(self.search_input)
        search_bar.addWidget(self.reset_search_button)
        main_layout.addLayout(search_bar)
        
        # Splitter para dividir la tabla y el editor de texto
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter, 1)
        
        # Tabla para mostrar y editar los highlights
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Título", "Fecha", "Texto", "Autor", "Libro", "Página", "Etiquetas"])
        
        # Ajustar anchos de columna según el tipo de contenido
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)  # Título
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Fecha
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Texto
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)  # Autor
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)  # Libro
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Página
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Interactive)  # Etiquetas
        
        # Establecer anchos iniciales para las columnas con tamaño fijo
        self.table.setColumnWidth(0, 150)  # Título
        self.table.setColumnWidth(3, 120)  # Autor
        self.table.setColumnWidth(4, 150)  # Libro
        self.table.setColumnWidth(6, 100)  # Etiquetas
        
        # Habilitar ordenación de columnas
        self.table.setSortingEnabled(True)
        
        # Aplicar el delegado personalizado para el texto
        self.text_delegate = TextPreviewDelegate(self.table)
        self.table.setItemDelegateForColumn(2, self.text_delegate)
        
        # Habilitar menú contextual para la tabla
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Capturar tecla Delete para eliminar filas
        self.table.keyPressEvent = self.table_key_press_event
        
        splitter.addWidget(self.table)
        
        # Editor para previsualizar/editar el texto completo
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        
        editor_label = QLabel("Editor de texto para el campo seleccionado:")
        editor_layout.addWidget(editor_label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Seleccione un subrayado en la tabla para editarlo aquí")
        self.text_edit.setMinimumHeight(200)  # Altura mínima para ver más contenido
        editor_layout.addWidget(self.text_edit)
        
        splitter.addWidget(editor_container)
        
        # Ajustar las proporciones iniciales del splitter (70% tabla, 30% editor)
        splitter.setSizes([700, 300])
        
        # Conectar la selección de la tabla con el editor de texto
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        # Conectar la edición en el editor de texto con la actualización de la tabla
        self.text_edit.textChanged.connect(self.update_table_from_editor)
        
        # Botón para procesar los highlights y crear el archivo .jex
        self.process_button = QPushButton("Generar archivo .jex")
        self.process_button.clicked.connect(self.process_highlights)
        self.process_button.setEnabled(False)  # Deshabilitado hasta que se carguen datos
        main_layout.addWidget(self.process_button)
        
        # Variables para seguimiento
        self.current_row = -1
        self.current_col = -1
    
    def load_highlights(self):
        """Carga los subrayados usando KindleClippingsParser"""
        progress = QProgressDialog("Cargando subrayados...", "Cancelar", 0, 0, self)
        progress.setWindowTitle("Procesando")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.setLabelText("Procesando subrayados Kindle...")
        progress.setCancelButton(None)
        progress.show()
        
        QApplication.processEvents()
        
        try:
            # Detect language or set default
            # For now default to 'es' or 'en' as per config.json? 
            # We can read config here or just hardcode 'es' for now as in parser default
            parser = KindleClippingsParser(language_code='es')
            
            # Default path or ask?
            file_path = "data/My Clippings.txt"
            if not os.path.exists(file_path):
                file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo My Clippings.txt", "", "Text Files (*.txt)")
            
            if file_path:
                self.clippings = parser.parse_file(file_path)
                self.display_highlights()
                self.status_label.setText(f"Subrayados cargados: {len(self.clippings)} encontrados")
                self.process_button.setEnabled(True)
            else:
                 self.status_label.setText("Carga cancelada o archivo no encontrado")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar los subrayados: {str(e)}")
            self.status_label.setText("Error al cargar los subrayados")
            logger.error(f"GUI Load Error: {e}", exc_info=True)
        finally:
            progress.close()
    
    def display_highlights(self):
        """Muestra los highlights en la tabla"""
        # Guardar el estado de ordenación
        sort_column = self.table.horizontalHeader().sortIndicatorSection()
        sort_order = self.table.horizontalHeader().sortIndicatorOrder()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.clippings))
        
        for row, clip in enumerate(self.clippings):
            # Mapping Clipping object to columns
            # 0: Title (Snippet), 1: Date, 2: Text (Full), 3: Author, 4: Book, 5: Page, 6: Tags
            
            title_snippet = clip.content[:50].replace('\n', ' ')
            date_str = clip.date_time.strftime('%Y-%m-%d %H:%M:%S') if clip.date_time else ''
            tags_str = ', '.join(clip.tags)
            
            self.table.setItem(row, 0, QTableWidgetItem(title_snippet))
            self.table.setItem(row, 1, QTableWidgetItem(date_str))
            self.table.setItem(row, 2, QTableWidgetItem(clip.content))
            self.table.setItem(row, 3, QTableWidgetItem(clip.author))
            self.table.setItem(row, 4, QTableWidgetItem(clip.book_title))
            self.table.setItem(row, 5, QTableWidgetItem(clip.page))
            self.table.setItem(row, 6, QTableWidgetItem(tags_str))
        
        self.table.setSortingEnabled(True)
        if sort_column >= 0:
            self.table.horizontalHeader().setSortIndicator(sort_column, sort_order)
    
    def on_selection_changed(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            self.current_row = selected_items[0].row()
            self.current_col = selected_items[0].column()
            item = self.table.item(self.current_row, self.current_col)
            if item:
                self.text_edit.setText(item.text())
    
    def update_table_from_editor(self):
        if self.current_row >= 0 and self.current_col >= 0:
            item = self.table.item(self.current_row, self.current_col)
            if item:
                new_text = self.text_edit.toPlainText()
                item.setText(new_text)
                
                # Update underlying Clipping object if we are editing specific columns?
                # This is tricky because table might be sorted/filtered.
                # We need to map back to self.clippings index.
                # If filtered, we need self.filtered_indexes mapping logic.
                
                # Simplified: Just update table item for visual. 
                # Ideally we update the object so export is correct.
                # Let's rely on get_table_data reconstruction for export.
                pass
    
    def reset_search(self):
        self.search_input.clear()
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        self.filtered_indexes = []
        
        if not search_text:
            # Show all
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
            return
        
        for row in range(self.table.rowCount()):
            show_row = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            
            self.table.setRowHidden(row, not show_row)
            if show_row:
                self.filtered_indexes.append(row)
    
    def show_context_menu(self, position):
        menu = QMenu()
        delete_action = QAction("Eliminar fila", self)
        delete_action.triggered.connect(self.delete_selected_rows)
        menu.addAction(delete_action)
        
        duplicate_action = QAction("Duplicar fila", self)
        duplicate_action.triggered.connect(self.duplicate_selected_row)
        menu.addAction(duplicate_action)
        
        menu.exec_(self.table.mapToGlobal(position))
    
    def table_key_press_event(self, event):
        if event.key() == Qt.Key_Delete:
            self.delete_selected_rows()
        else:
            QTableWidget.keyPressEvent(self.table, event)
    
    def delete_selected_rows(self):
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            return
        
        reply = QMessageBox.question(
            self, 'Confirmación',
            f"¿Está seguro de eliminar {len(selected_rows)} fila(s)?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # We need to delete from the underlying list too.
        # But sorting makes this hard because row index != list index.
        # Simple approach for now:
        # 1. Reconstruct list from current table state (excluding deleted rows)
        # 2. Reload table
        
        # Actually, let's just remove from table widget and rebuild list on export
        # But wait, duplication needs list.
        
        # Better: Since we don't have IDs mapping rows to objects easily with sorting enabled,
        # disabling sorting while editing might be safer, or implementing a custom model.
        # For this refactor, I will assume row order in table matches display.
        
        # If sorted, the visual row corresponds to some index. QTableWidget handles this via visualIndex?
        # No, item(row, col) accesses the model row.
        
        rows_to_delete = sorted(list(selected_rows), reverse=True)
        for row in rows_to_delete:
             self.table.removeRow(row)
        
        # We also need to update self.clippings to match table state?
        # Or just rebuild self.clippings from table before any operation that needs it.
        # Let's rebuild self.clippings now to keep sync
        self.clippings = self.get_clippings_from_table()
        self.status_label.setText(f"Subrayados: {len(self.clippings)}")

    def duplicate_selected_row(self):
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if len(selected_rows) != 1:
            QMessageBox.information(self, "Información", "Seleccione una fila.")
            return
        
        row = list(selected_rows)[0]
        
        # Get data from row
        title = self.table.item(row, 0).text()
        date_str = self.table.item(row, 1).text()
        content = self.table.item(row, 2).text()
        author = self.table.item(row, 3).text()
        book = self.table.item(row, 4).text()
        page = self.table.item(row, 5).text()
        tags_str = self.table.item(row, 6).text()
        
        # Create new Clipping
        try:
             dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except:
             dt = datetime.now()
             
        new_clip = Clipping(
            content=content,
            book_title=book,
            author=author,
            date_time=dt,
            page=page,
            tags=[t.strip() for t in tags_str.split(',') if t.strip()]
        )
        
        self.clippings.append(new_clip)
        self.display_highlights() # Refresh
        self.table.selectRow(self.table.rowCount() - 1)
    
    def get_clippings_from_table(self):
        """Reconstructs Clipping objects from current table data"""
        new_list = []
        for row in range(self.table.rowCount()):
             if self.table.isRowHidden(row):
                 continue # Should hidden rows be excluded? Original logic: filtered_indexes handled it.
                 # If we are exporting, we usually want what is visible OR everything?
                 # GUI implies "what you see is what you get" usually.
                 # Let's take everything that is in the model (ignoring hidden state for now? 
                 # or if table.removeRow was used, they are gone).
                 pass

             # Actually, table.removeRow removes it from model.
             # Filtering just hides it.
             # So we should iterate all model rows.
             
             date_str = self.table.item(row, 1).text()
             try:
                 dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
             except:
                 dt = datetime.now()

             c = Clipping(
                content=self.table.item(row, 2).text(),
                book_title=self.table.item(row, 4).text(),
                author=self.table.item(row, 3).text(),
                date_time=dt,
                page=self.table.item(row, 5).text(),
                tags=[t.strip() for t in self.table.item(row, 6).text().split(',') if t.strip()]
             )
             # Add title? Title in clipping object is not stored, it's derived from content.
             # So we don't need to read column 0.
             new_list.append(c)
        return new_list

    def process_highlights(self):
        if self.table.rowCount() == 0:
            return
        
        # Get updated data
        updated_clippings = self.get_clippings_from_table()
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar exportación", "", "Joplin Export Files (*.jex)")
        
        if file_path:
            try:
                service = ClippingsService(language_code='es') # Default
                # We need location?
                # Default location
                loc = (0.0, 0.0, 0)
                
                service.process_clippings_from_list(
                    clippings=updated_clippings,
                    output_file=file_path,
                    root_notebook_name="Kindle Imports",
                    location=loc,
                    creator_name="System"
                )
                QMessageBox.information(self, "Éxito", f"Exportado a {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                logger.error(f"Export Error: {e}", exc_info=True)

    def add_empty_row(self):
        c = Clipping(
            content="Nuevo texto",
            book_title="Sin título",
            author="Desconocido",
            date_time=datetime.now()
        )
        self.clippings.append(c)
        self.display_highlights()
        self.table.selectRow(self.table.rowCount()-1)

def main():
    app = QApplication(sys.argv)
    window = KindleHighlightsApp()
    window.show()
    QTimer.singleShot(100, window.load_highlights)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

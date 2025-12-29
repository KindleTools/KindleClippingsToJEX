
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from PyQt5.QtCore import Qt
from ui.widgets import ClippingsTableWidget
from domain.models import Clipping
from datetime import datetime

# Graphical tests require a QApplication instance
app = QApplication(sys.argv)

class TestClippingsTableWidget(unittest.TestCase):
    def setUp(self):
        self.widget = ClippingsTableWidget()
        self.clippings = [
            Clipping(
                book_title="Test Book",
                author="Test Author",
                content="Test Content",
                page=1,
                location="100",
                date_time=datetime.now(),
                type="highlight",
                tags={"tag1"}
            ),
            Clipping(
                book_title="Test Book", # Same book for bulk edit test
                author="Test Author",
                content="Another Content",
                page=2,
                location="101",
                date_time=datetime.now(),
                type="highlight",
                tags={"tag2"}
            )
        ]
        self.widget.populate(self.clippings)

    def test_populate(self):
        self.assertEqual(self.widget.rowCount(), 2)
        self.assertEqual(self.widget.item(0, 1).text(), "Test Book")
        # Check UserRole storage
        self.assertEqual(self.widget.item(0, 1).data(Qt.UserRole), "Test Book")

    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_bulk_edit_trigger(self, mock_question):
        # Configure mock to say YES
        from PyQt5.QtWidgets import QMessageBox
        mock_question.return_value = QMessageBox.Yes
        
        # Simulate editing the first row's book title
        item = self.widget.item(0, 1)
        item.setText("New Title")
        
        # Trigger the change event manually or rely on signal if possible, 
        # but itemChanged is emitted by QTableWidget when setText is called? 
        # Actually setText emits itemChanged.
        
        # However, our logic relies on comparing against UserRole. 
        # UserRole is "Test Book", Text is "New Title".
        # The signal _on_item_changed should catch this.
        
        # Note: In a unit test environment without an event loop running, signals might not propagate 
        # cleanly or immediately. We might need to call the handler directly for robustness.
        self.widget._on_item_changed(item)
        
        # Check if the SECOND row was updated
        item_row_2 = self.widget.item(1, 1)
        self.assertEqual(item_row_2.text(), "New Title")
        self.assertEqual(item_row_2.data(Qt.UserRole), "New Title")

if __name__ == '__main__':
    unittest.main()

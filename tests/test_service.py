import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from services.clippings_service import ClippingsService
from domain.models import Clipping

class TestClippingsService(unittest.TestCase):
    def setUp(self):
        self.service = ClippingsService()
        # Mock internal components to isolate service logic
        self.service.parser = MagicMock()
        self.service.exporter = MagicMock()

    def test_process_clippings_from_list(self):
        # Prepare data
        clip = Clipping(
            book_title="Test Book",
            author="Author Name",
            content="Some highlight content",
            type="highlight",
            date_time=datetime(2023, 1, 1),
            page="10",
            location="100-110",
            tags={"tag1"}
        )
        clippings_list = [clip]

        # Call method
        self.service.process_clippings_from_list(
            clippings=clippings_list,
            output_file="out.jex",
            root_notebook_name="Kindle Notes",
            location=(0.0, 0.0, 0),
            creator_name="Tester"
        )

        # Verification
        # 1. Check generated entities in memory
        entities = self.service.entities_to_export
        self.assertTrue(len(entities) > 0)
        
        # We expect: Root NB, Author NB, Book NB, Note, Tag, Tag Association
        types = [e.get('type_') for e in entities]
        self.assertIn(2, types) # Folder
        self.assertIn(1, types) # Note
        self.assertIn(5, types) # Tag (since we had tags)
        
        # 2. Check exporter call
        self.service.exporter.create_jex.assert_called_once()
        args, _ = self.service.exporter.create_jex.call_args
        self.assertEqual(args[0], "out.jex")
        self.assertEqual(args[1], entities)

    @patch('services.clippings_service.KindleClippingsParser')
    def test_process_clippings_file(self, MockParser):
        # Setup mock return
        mock_instance = MockParser.return_value
        clip = Clipping(
            book_title="B", author="A", content="C", type="h", 
            date_time=datetime.now(), page="1", location="1"
        )
        mock_instance.parse_file.return_value = [clip]
        
        # Re-init service to use patched class
        service = ClippingsService()
        service.exporter = MagicMock()
        
        service.process_clippings("in.txt", "out.jex", "Root", (0,0,0), "Me")
        
        # Check parser was called
        mock_instance.parse_file.assert_called_with("in.txt")
        service.exporter.create_jex.assert_called()

if __name__ == '__main__':
    unittest.main()

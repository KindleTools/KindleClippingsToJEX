import unittest
import os
import json
from datetime import datetime
from domain.models import Clipping
from exporters.json_exporter import JsonExporter

class TestJsonExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = JsonExporter()
        self.test_file = "test_export.json"
        self.context = {"creator": "Test User"}
        self.clippings = [
            Clipping(
                content="Json content",
                book_title="Test Book",
                author="Test Author",
                date_time=datetime(2023, 1, 1, 12, 0, 0),
                location="100",
                page="10",
                tags=["tag1"],
                entry_type="highlight"
            )
        ]

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_export_creates_json_file(self):
        self.exporter.export(self.clippings, self.test_file, self.context)
        self.assertTrue(os.path.exists(self.test_file))

    def test_json_content_structure(self):
        self.exporter.export(self.clippings, self.test_file, self.context)
        
        with open(self.test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Check Meta
            self.assertEqual(data['meta']['count'], 1)
            self.assertEqual(data['meta']['creator'], "Test User")
            self.assertEqual(data['meta']['source'], "KindleClippingsToJEX")
            
            # Check List
            self.assertIsInstance(data['clippings'], list)
            item = data['clippings'][0]
            self.assertEqual(item['content'], "Json content")
            self.assertEqual(item['book_title'], "Test Book")
            self.assertEqual(item['tags'], ["tag1"])

if __name__ == '__main__':
    unittest.main()

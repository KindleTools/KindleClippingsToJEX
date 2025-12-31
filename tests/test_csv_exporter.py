import unittest
import os
import csv
from datetime import datetime
from domain.models import Clipping
from exporters.csv_exporter import CsvExporter


class TestCsvExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = CsvExporter()
        self.test_file = "test_export.csv"
        self.clippings = [
            Clipping(
                content="Test content",
                book_title="Test Book",
                author="Test Author",
                date_time=datetime(2023, 1, 1, 12, 0, 0),
                location="100-200",
                page="10",
                tags=["tag1", "tag2"],
            )
        ]

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_export_clippings_creates_file(self):
        self.exporter.export_clippings(self.clippings, self.test_file)
        self.assertTrue(os.path.exists(self.test_file))

    def test_export_content_is_correct(self):
        self.exporter.export_clippings(self.clippings, self.test_file)

        with open(self.test_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["book_title"], "Test Book")
            self.assertEqual(row["author"], "Test Author")
            self.assertEqual(row["content"], "Test content")
            self.assertEqual(row["location"], "100-200")
            self.assertEqual(row["page"], "10")
            self.assertEqual(row["tags"], "tag1, tag2")


if __name__ == "__main__":
    unittest.main()

import unittest
import os
import zipfile
from datetime import datetime
from domain.models import Clipping
from domain.constants import GENERATOR_STRING
from exporters.markdown_exporter import MarkdownExporter


class TestMarkdownExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = MarkdownExporter()
        self.test_file = "test_export.zip"
        self.context = {}  # Context no longer used for YAML, but passed in method
        self.clippings = [
            Clipping(
                content="This is the quote content.",
                book_title="The Way of Kings",
                author="Brandon Sanderson",
                date_time=datetime(2023, 10, 27, 12, 0, 0),
                location="100-200",
                page="42",
                tags=["fantasy", "epic"],
                entry_type="highlight",
            )
        ]

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_export_structure_and_metadata(self):
        self.exporter.export_clippings(self.clippings, self.test_file, self.context)

        with zipfile.ZipFile(self.test_file, "r") as zipf:
            file_list = zipf.namelist()
            self.assertEqual(len(file_list), 1)

            # Check Folder Structure: AUTHOR / Book / ...
            expected_start = "BRANDON SANDERSON/The Way of Kings/"
            self.assertTrue(
                file_list[0].startswith(expected_start),
                f"Path {file_list[0]} does not match expected structure.",
            )

            # Check Content
            content = zipf.read(file_list[0]).decode("utf-8")

            # Verify YAML Fields
            self.assertIn('book: "The Way of Kings"', content)
            self.assertIn('author: "Brandon Sanderson"', content)
            self.assertIn("date: 2023-10-27T12:00:00", content)
            self.assertIn('source: "kindle"', content)
            self.assertIn(f'generator: "{GENERATOR_STRING}"', content)

            # Verify Removed Fields are ABSENT (Clean UX)
            self.assertNotIn("created:", content)
            self.assertNotIn("updated:", content)
            self.assertNotIn("location:", content)  # Technical field removed
            self.assertNotIn("type:", content)  # Technical field removed
            self.assertNotIn("creator:", content)
            self.assertNotIn("geo_lat:", content)
            self.assertNotIn("geo_lon:", content)


if __name__ == "__main__":
    unittest.main()

import unittest
import os
import shutil
import tempfile
from services.clippings_service import ClippingsService

class TestIntegration(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.test_dir, "My Clippings.txt")
        self.output_jex = os.path.join(self.test_dir, "export") # .jex added automatically
        
        # Create a sample clippings file
        with open(self.input_file, "w", encoding="utf-8-sig") as f:
            f.write("Book Title (Author Name)\n")
            f.write("- Your Highlight on page 10 | Location 100-120 | Added on Friday, October 27, 2023 12:00:00 PM\n\n")
            f.write("This is a sample highlight content.\n")
            f.write("==========\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_flow_jex_export(self):
        service = ClippingsService(language_code="en")
        
        # Run the full process
        service.process_clippings(
            input_file=self.input_file,
            output_file=self.output_jex,
            root_notebook_name="Integration Test",
            location=(0,0,0),
            creator_name="TestBot",
            enable_deduplication=True,
            export_format='jex'
        )
        
        # Verify Output
        expected_file = self.output_jex + ".jex"
        self.assertTrue(os.path.exists(expected_file), "JEX file was not created.")
        
        # Verify content (roughly, size > 0)
        self.assertGreater(os.path.getsize(expected_file), 0)

    def test_full_flow_csv_export(self):
        service = ClippingsService(language_code="en")
        output_csv = os.path.join(self.test_dir, "export_test.csv")
        
        service.process_clippings(
            input_file=self.input_file,
            output_file=output_csv,
            root_notebook_name="Integration Test",
            location=(0,0,0),
            creator_name="TestBot",
            enable_deduplication=False, # Test without dedupe path too
            export_format='csv'
        )
        
        self.assertTrue(os.path.exists(output_csv))
        with open(output_csv, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            self.assertIn("Book Title", content)
            self.assertIn("sample highlight", content)

    def test_deduplication_integration(self):
        """Verify that deduplication logic is actually invoked and working."""
        # Write duplicate content
        with open(self.input_file, "a", encoding="utf-8-sig") as f:
             f.write("Book Title (Author Name)\n")
             f.write("- Your Highlight on page 10 | Location 100-120 | Added on Friday, October 27, 2023 12:01:00 PM\n\n")
             f.write("This is a sample highlight content.\n") # Same content, slightly different time
             f.write("==========\n")

        service = ClippingsService(language_code="en")
        
        # We need to spy on the internal list processing to verify count
        # But for integration, checking the 'is_duplicate' flag in JSON export is easier
        output_json = os.path.join(self.test_dir, "dupe_test.json")
        
        service.process_clippings(
            input_file=self.input_file,
            output_file=output_json,
            root_notebook_name="Integration Test",
            location=(0,0,0),
            creator_name="TestBot",
            enable_deduplication=True,
            export_format='json'
        )
        
        import json
        with open(output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            clippings = data['clippings']
            # Should have 2 clippings
            self.assertEqual(len(clippings), 2)
            # One should be marked as duplicate (or handled by the deduplicator)
            # actually SmartDeduplicator marks them property 'is_duplicate'
            
            # Count duplicates
            dupes = [c for c in clippings if c.get('is_duplicate')]
            self.assertTrue(len(dupes) > 0, "Deduplication failed to mark duplicate.")

if __name__ == '__main__':
    unittest.main()

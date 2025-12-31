import unittest
from datetime import datetime
from services.identity_service import IdentityService
from utils.title_cleaner import TitleCleaner
from domain.models import Clipping
from parsers.kindle_parser import KindleClippingsParser


class TestNewFeatures(unittest.TestCase):
    def test_identity_service_deterministic(self):
        """Test that IdentityService generates the same ID for the same content regardless of date."""
        clip1 = Clipping(
            content="This is a test highlight.",
            book_title="Test Book",
            author="Test Author",
            date_time=datetime(2023, 1, 1, 12, 0, 0),
            location="100-200",
            page="10",
        )

        clip2 = Clipping(
            content="This is a test highlight.",
            book_title="Test Book",
            author="Test Author",
            date_time=datetime(2025, 12, 31, 15, 30, 0),  # Different date
            location="100-200",
            page="10",
        )

        id1 = IdentityService.generate_id(clip1)
        id2 = IdentityService.generate_id(clip2)

        self.assertEqual(id1, id2, "IDs should be identical despite different dates")
        self.assertTrue(len(id1) > 0)

    def test_identity_service_duplicates(self):
        """Test strict and fuzzy duplicate detection."""
        clip1 = Clipping(
            content="Foo bar", book_title="B", author="A", date_time=datetime.now(), location="10"
        )
        clip2 = Clipping(
            content="Foo bar", book_title="B", author="A", date_time=datetime.now(), location="10"
        )

        self.assertTrue(
            IdentityService.is_duplicate(clip1, clip2), "Identical clips should be duplicates"
        )

        # Fuzzy test (location matches, content slightly different)
        clip3 = Clipping(
            content="Foo bar.", book_title="B", author="A", date_time=datetime.now(), location="10"
        )
        self.assertTrue(
            IdentityService.is_duplicate(clip1, clip3),
            "Similar content at same location should be duplicate",
        )

    def test_title_cleaner(self):
        """Test title cleaning logic."""
        cases = [
            ("My Book (Spanish Edition)", "My Book"),
            ("Another Book.mobi", "Another Book"),
            ("Clean Book", "Clean Book"),
            (" Harry Potter   (English Edition)  ", "Harry Potter"),
        ]

        for input_title, expected in cases:
            cleaned = TitleCleaner.clean_title(input_title)
            self.assertEqual(cleaned, expected, f"Failed to clean '{input_title}'")

    def test_parser_integration(self):
        """Test that the parser actually uses these services."""
        # Create a dummy file content
        content = """My Book (Spanish Edition) (Unknown Author)
- Your Highlight on Location 100-200 | Added on Monday, January 1, 2024 12:00:00 PM

This is a test content.
==========
"""
        # We need a temporary file for the parser
        import os

        filename = "temp_test_clippings.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        parser = KindleClippingsParser(language_code="en")
        clippings = parser.parse_file(filename)

        os.remove(filename)

        self.assertEqual(len(clippings), 1)
        clip = clippings[0]

        # Check Title Cleaner worked
        self.assertEqual(clip.book_title, "My Book", "Parser did not clean title")

        # Check Identity Service worked (uid should be set)
        self.assertTrue(clip.uid, "Parser did not assign UID")
        self.assertNotEqual(clip.uid, "", "UID should not be empty")


if __name__ == "__main__":
    unittest.main()

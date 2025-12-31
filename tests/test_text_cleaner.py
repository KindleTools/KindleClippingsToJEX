import unittest
from utils.text_cleaner import TextCleaner


class TestTextCleaner(unittest.TestCase):
    def test_basic_cleaning(self):
        # Double spaces
        self.assertEqual(TextCleaner.clean_text("Hello  World"), "Hello World")
        # Trailing/Leading spaces
        self.assertEqual(TextCleaner.clean_text(" Hello World "), "Hello World")

    def test_punctuation_cleaning(self):
        # Space before dot
        self.assertEqual(TextCleaner.clean_text("Hello World ."), "Hello World.")
        # Space before comma
        self.assertEqual(TextCleaner.clean_text("Hello , World"), "Hello, World")

    def test_capitalization(self):
        # Lowercase start
        self.assertEqual(TextCleaner.clean_text("hello world"), "Hello world")
        # Already capitalized
        # Dots/ellipsis should be ignored/preserved?
        # The logic says: if starts with ... don't capitalize
        self.assertEqual(TextCleaner.clean_text("...and then"), "...and then")

    def test_invisible_chars(self):
        # Zero width space
        self.assertEqual(TextCleaner.clean_text("H\u200bello"), "Hello")

    def test_unicode_normalization(self):
        # NFD (Decomposed: n + ~) should become NFC (Composed: ñ) AND be capitalized
        nfd_str = "n\u0303"  # n + combining tilde = ñ (lowercase)
        nfc_str_capitalized = "\u00d1"  # Ñ (Capitalized NFC)

        cleaned = TextCleaner.clean_text(nfd_str)

        # It should match the Capitalized NFC version
        self.assertEqual(cleaned, nfc_str_capitalized)

        # Verify basic normalization logic (lowercase match)
        self.assertEqual(cleaned.lower(), "\u00f1")

    def test_empty(self):
        self.assertEqual(TextCleaner.clean_text(None), "")
        self.assertEqual(TextCleaner.clean_text(""), "")


if __name__ == "__main__":
    unittest.main()

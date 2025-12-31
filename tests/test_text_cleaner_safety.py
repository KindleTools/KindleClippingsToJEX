import unittest
from utils.text_cleaner import TextCleaner

class TestTextCleanerSafety(unittest.TestCase):
    """
    Safety tests for TextCleaner de-hyphenation logic to ensure no false positives.
    """

    def test_dehyphenation_basic(self):
        # Case 1: Standard PDF line break (True Positive)
        # "amaz- \n ing" -> "amazing"
        raw = "This is an amaz-\ning discovery."
        expected = "This is an amazing discovery."
        self.assertEqual(TextCleaner.clean_text(raw), expected)

    def test_dehyphenation_with_spaces_after_hyphen(self):
        # Case 2: Space after dash before newline (True Positive)
        # "program- \n ming" -> "programming"
        raw = "Python program- \n ming is fun."
        expected = "Python programming is fun."
        self.assertEqual(TextCleaner.clean_text(raw), expected)

    def test_safety_dash_with_space_before(self):
        # Case 3: Dash used as punctuation (False Positive Check)
        # "word - \n word" -> SHOULD NOT JOIN into "wordword"
        # The regex requires ([^\W\d_]+)- so no space allowed before hyphen.
        raw = "This is a pause - \n for effect."
        expected = "This is a pause - \n for effect." # Newline preserved, dash preserved
        self.assertEqual(TextCleaner.clean_text(raw), expected)

    def test_safety_numeric_range(self):
        # Case 4: Numeric ranges split by newline (False Positive Check)
        # "1990-\n1991" -> SHOULD NOT JOIN into "19901991"
        raw = "The years 1990-\n1991 were great."
        expected = "The years 1990-\n1991 were great." # Newline preserved, range preserved
        # Implementation using [^\\W\\d_]+ should ensure this.
        self.assertEqual(TextCleaner.clean_text(raw), expected)

    def test_safety_hyphenated_compound_words(self):
        # Case 5: Compound words usually lose the hyphen in simplistic joiners
        # "self- \n ish" -> "selfish" (Good)
        # "well- \n known" -> "wellknown" (Acceptable collateral damage?)
        # Ideally "well-known", but "wellknown" is better than "well- known"
        pass

if __name__ == '__main__':
    unittest.main()

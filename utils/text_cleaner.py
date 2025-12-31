import re
import unicodedata

class TextCleaner:
    """
    Utility for cleaning and normalizing text content from Kindle clippings.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Main entry point for text cleaning.
        Applies a series of cleaning rules to produce professional-looking text.
        """
        if not text:
            return ""

        # 0. Unicode Normalization (NFC) - Standard for cross-platform compatibility
        # This fixes issues with accents (e.g., 'ñ' vs 'n'+'~') affecting Search/Obsidian/Joplin
        text = unicodedata.normalize('NFC', text)

        # 1. Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 2. Remove invisible characters (BOM, zero-width spaces, etc.) already done partly in parser, 
        # but good to have a second pass for things inside the text.
        # \u200b is zero-width space
        text = text.replace('\ufeff', '').replace('\u200b', '')

        # 3. Collapse multiple spaces into one
        text = re.sub(r' +', ' ', text)

        # 4. Remove spaces before punctuation (common OCD trigger)
        # "Word ." -> "Word."
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)

        # 5. Fix "dash" spacing or broken words (simple heuristics)
        # Sometimes PDF highlights break words like "amaz- ing" -> "amazing"
        # This is risky, let's stick to safe hyphenation:
        # "word - word" -> "word - word" (keep)
        # "word- word" -> "word - word" (standardize)
        
        # 6. Trim leading/trailing whitespace
        text = text.strip()

        # 7. Capitalize first letter if it's a sentence fragment (optional but nice)
        if text and text[0].islower() and text[0].isalpha():
             # Check if it looks like a continuation (starts with "...")
             if not text.startswith("..."):
                 text = text[0].upper() + text[1:]

        return text

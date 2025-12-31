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

        # 2.5 De-hyphenation (PDF line breaks)
        # Aggressive cleaning: "word- \n suffix" -> "wordsuffix"
        # We look for: Word character (LETTERS ONLY), hyphen, optional space, newline, optional space, word character
        # Regex [^\W\d_] matches Unicode letters (alphanumeric minus digits and underscore)
        text = re.sub(r'([^\W\d_]+)-\s*\n\s*([^\W\d_]+)', r'\1\2', text)
        
        # 3. Collapse multiple spaces into one
        text = re.sub(r' +', ' ', text)

        # 4. Remove spaces before punctuation (common OCD trigger)
        # "Word ." -> "Word."
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)

        # 5. Fix "dash" spacing or broken words (simple heuristics)
        # "word - word" -> "word - word" (standardize En-dash / Em-dash potentially)
        # For now, just ensuring single spaces around hyphens that are NOT inside words
        # (This is tricky to regex safely without NLP, so we'll stick to just cleaning spaces)
        
        # 6. Trim leading/trailing whitespace
        text = text.strip()

        # 7. Capitalize first letter if it's a sentence fragment (optional but nice)
        if text and text[0].islower() and text[0].isalpha():
             # Check if it looks like a continuation (starts with "...")
             if not text.startswith("..."):
                 text = text[0].upper() + text[1:]

        return text

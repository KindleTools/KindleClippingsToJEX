import re
import logging

logger = logging.getLogger("KindleToJex.TitleCleaner")

class TitleCleaner:
    """
    Utility to clean up Kindle book titles by removing common noise
    like file extensions, edition parentheticals, and other metadata clutter.
    """
    
    # Patterns to strip out (case insensitive)
    PATTERNS = [
        # File extensions
        r'\.mobi$', r'\.azw3?$', r'\.txt$', r'\.pdf$', r'\.epub$',
        
        # Edition markers
        r'\s*\(Spanish Edition\)', r'\s*\(English Edition\)',
        r'\s*\(Edición española\)', r'\s*\(Edición en español\)',
        r'\s*\(French Edition\)', r'\s*\(Edition française\)', r'\s*\(Version française\)',
        r'\s*\(German Edition\)', r'\s*\(Deutsche Ausgabe\)',
        r'\s*\(Italian Edition\)', r'\s*\(Edizione italiana\)',
        r'\s*\(Portuguese Edition\)', r'\s*\(Edição portuguesa\)',
        r'\s*\(Kindle Edition\)', r'\s*\[Print Replica\]', r'\s*\[eBook\]',
        r'\s*\(Edition \d+\)',
        
        # Leading numbers (e.g. "01 Book Title")
        r'^\d+\s+',
        
        # Series/Vol markers that look too technical (optional, kept conservative for now)
        # r'\s*Vol\. \d+',
    ]
    
    @staticmethod
    def clean_title(title: str) -> str:
        """
        Cleans the book title by removing known garbage patterns.
        """
        if not title:
            return "Unknown Book"
            
        clean = title.strip()
        original = clean
        
        for pattern in TitleCleaner.PATTERNS:
            clean = re.sub(pattern, '', clean, flags=re.IGNORECASE)
            
        # Remove trailing parentheses if they are empty or just whitespace (side effect of removals)
        clean = re.sub(r'\s*\(\s*\)$', '', clean)
        clean = re.sub(r'\s*\[\s*\]$', '', clean)
        
        clean = clean.strip()
        
        if clean != original:
            logger.debug(f"Cleaned title: '{original}' -> '{clean}'")
            
        return clean

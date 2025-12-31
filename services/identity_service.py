import hashlib
import logging
from typing import List, Dict, Any
from domain.models import Clipping

logger = logging.getLogger("KindleToJex.IdentityService")

class IdentityService:
    """
    Service for generating deterministic IDs and detecting duplicates.
    Based on 'Enterprise' architecture principles:
    - IDs are content-based (SHA-256), ignoring dates.
    - Robust to minor import variations.
    """

    @staticmethod
    def generate_id(clipping: Clipping) -> str:
        """
        Generates a deterministic unique ID for a clipping.
        
        The hash key is formed by:
        - Content (text)
        - Book Title
        - Author
        - Location/Page (Location preferred as it's more stable on Kindle)
        
        Crucially, we EXCLUDE the timestamp. This ensures that if you re-import 
        the same file later (or from a different device clock), the ID remains identical.
        """
        # specialized cleaning for ID generation to be robust against minor whitespace
        clean_content = clipping.content.strip()
        clean_title = clipping.book_title.strip()
        clean_author = clipping.author.strip()
        
        # Use location as primary differentiator, page as secondary
        # Some clippings have only one, or neither.
        loc_marker = clipping.location.strip() or clipping.page.strip() or "unknown_loc"
        
        # We construct a pipe-delimited string of the invariant parts
        # Format: CONTENT|TITLE|AUTHOR|LOCATION
        unique_string = f"{clean_content}|{clean_title}|{clean_author}|{loc_marker}"
        
        return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()

    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """
        Calculates Jaccard similarity coefficient between two specific texts.
        Useful for "Fuzzy Deduplication" later.
        """
        if not text1 or not text2:
            return 0.0
            
        # simple punctuation removal map
        import string
        translator = str.maketrans('', '', string.punctuation)
        
        set1 = set(text1.lower().translate(translator).split())
        set2 = set(text2.lower().translate(translator).split())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    @staticmethod
    def is_duplicate(clip1: Clipping, clip2: Clipping, threshold: float = 0.9) -> bool:
        """
        Determines if two clippings are duplicates using strict or fuzzy logic.
        """
        # 1. Strict ID Check (Fastest)
        id1 = IdentityService.generate_id(clip1)
        id2 = IdentityService.generate_id(clip2)
        if id1 == id2:
            return True
            
        # 2. Heuristic Check: Same Book + Same Location
        # (Kindle sometimes changes the exact text selection by a char or two)
        if (clip1.book_title == clip2.book_title and 
            clip1.location and clip2.location and 
            clip1.location == clip2.location):
            # If location matches exactly, check content similarity
            # If content is >80% similar, it's the same highlight
            similarity = IdentityService.calculate_similarity(clip1.content, clip2.content)
            if similarity > 0.8:
                return True
                
        return False

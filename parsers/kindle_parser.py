import re
import dateparser
import json
import os
import logging
from typing import List, Dict, Optional, Tuple
from domain.models import Clipping
from parsers.patterns import DEFAULT_PATTERNS
from utils.text_cleaner import TextCleaner

logger = logging.getLogger("KindleToJex.Parser")

class KindleClippingsParser:
    """
    Parses 'My Clippings.txt' files from Kindle devices.
    
    Supports:
    - Multi-language detection (English, Spanish, etc. via languages.json).
    - Separation of Highlights and Notes.
    - Association of Notes to Highlights based on location ranges.
    - Robust date and location parsing.
    """
    def __init__(self, separator="==========", language_code="es"):
        self.separator = separator
        self.language_code = language_code
        self._load_language_patterns()

    def _load_language_patterns(self):
        """Loads regex patterns from languages.json based on configured language."""
        # Locate languages.json relative to this file
        # Locate languages.json using ConfigManager
        from utils.config_manager import get_config_manager
        lang_file = get_config_manager().get_resource_path('languages.json')
        
        # Default fallback patterns (Spanish)
        # Use imported constant as default
        self.default_patterns = DEFAULT_PATTERNS
        self.patterns = self.default_patterns

        self.available_languages = {}
        if os.path.exists(lang_file):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.available_languages = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.error(f"Error loading languages.json: {e}")
        else:
             logger.warning(f"languages.json not found at {os.path.abspath(lang_file)}.")

        if self.language_code != 'auto':
            if self.language_code in self.available_languages:
                self.patterns = self.available_languages[self.language_code]
                logger.info(f"Loaded patterns for language: {self.language_code}")
            else:
                logger.warning(f"Language '{self.language_code}' not found. Using defaults.")

    def _detect_language(self, content: str) -> str:
        """Attempts to detect language by checking patterns against file content."""
        logger.info("Attempting auto-detection of language...")
        sample = content[:5000] # Check first 5000 chars
        
        for lang_code, patterns in self.available_languages.items():
            # Check for 'highlight' keyword presence
            # We use the raw string from json which might contain regex like "subrayado|Subrayado"
            # simpler check: just seeing if the regex finds a match in the sample
            try:
                if re.search(patterns['added'], sample) or re.search(patterns['highlight'], sample):
                    logger.info(f"Language detected: {lang_code}")
                    return lang_code
            except re.error:
                continue
                
        logger.warning("Auto-detection failed. Falling back to 'es'.")
        return 'es'

    def parse_file(self, file_path: str, encoding: str = None) -> List[Clipping]:
        """
        Parses parsing with robust encoding handling.
        """
        logger.info(f"Parsing file: {file_path}")
        
        if not os.path.exists(file_path):
             logger.error(f"File not found: {file_path}")
             return []

        # List of encodings to try in order of likelihood
        encodings_to_try = ['utf-8-sig', 'utf-8', 'cp1252', 'latin-1']
        if encoding:
            # If user provided specific encoding, try it first
            encodings_to_try.insert(0, encoding)
            
        content = None
        used_encoding = None

        for enc in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                used_encoding = enc
                logger.info(f"Successfully read file using encoding: {enc}")
                break
            except UnicodeDecodeError:
                continue
            except OSError as e:
                logger.error(f"Error reading file {file_path}: {e}")
                return []
        
        if content is None:
            logger.error(f"Failed to decode file {file_path}. Tried encodings: {encodings_to_try}")
            return []

        # Explicit BOM removal (even if handled by encoding, this is a safety net)
        if content.startswith('\ufeff'):
            content = content[1:]
            logger.debug("BOM detected and removed explicitly.")
        
        raw_clippings = content.split(self.separator)
        
        # Auto-detect language if requested
        if self.language_code == 'auto':
            detected_lang = self._detect_language(content)
            if detected_lang in self.available_languages:
                self.patterns = self.available_languages[detected_lang]
            else:
                 self.patterns = self.default_patterns # Fallback

        parsed_clippings: List[Clipping] = []
        notes_data: List[Dict] = []
        
        # Pass 1: Collect Highlights and Notes separately
        for raw in raw_clippings:
            if not raw.strip():
                continue
            
            data = self._parse_single_clipping(raw)
            if not data:
                continue

            if data['type'] == 'highlight':
                clipping = Clipping(
                    content=data['content'],
                    book_title=data['book'],
                    author=data['author'],
                    date_time=data['date_time'],
                    location=data['location'],
                    page=data['page'],
                    type='highlight'
                )
                parsed_clippings.append(clipping)
            
            elif data['type'] == 'note':
                notes_data.append(data)

        # Pass 2: Link Notes to Highlights
        # Heuristic: Note location must start within Highlight range (or equal to).
        # Optimization: Group by Book Title first to reduce search space.
        
        # Helper to parse location range
        def parse_loc_range(loc_str: str) -> Tuple[int, int]:
            # "100-200" -> (100, 200); "100" -> (100, 100)
            parts = loc_str.split('-')
            try:
                s = int(parts[0])
                e = int(parts[1]) if len(parts) > 1 else s
                return s, e
            except:
                return -1, -1

        # Build index by book title for fast lookup
        highlights_by_book = {}
        for clip in parsed_clippings:
            if clip.book_title not in highlights_by_book:
                highlights_by_book[clip.book_title] = []
            highlights_by_book[clip.book_title].append(clip)

        for note in notes_data:
            book_key = note['book']
            if book_key in highlights_by_book:
                candidates = highlights_by_book[book_key]
                note_start, _ = parse_loc_range(note['location'])
                
                # Find the best candidate
                # A note matches if its location is inside the highlight range.
                best_match = None
                
                for h in candidates:
                    h_start, h_end = parse_loc_range(h.location)
                    # Relaxed check: valid if note is within range
                    # Often notes are at the END, e.g. range 10-20, note at 20.
                    # Sometimes user adds note later, but location remains attached to anchor.
                    if h_start <= note_start <= h_end:
                         best_match = h
                         # If we find one, usually that's it. But what if multiple overlap?
                         # Usually we want the smallest enclosing one? Or the most recent?
                         # For now, finding ANY match is better than exact match failure.
                         break 
                
                if best_match:
                    # Append tags
                    raw_tags = re.split(r'[.,;\n\r]', note['content'])
                    for raw_tag in raw_tags:
                        tag_text = raw_tag.strip()
                        if not tag_text: continue
                        if not tag_text[0].isalnum(): tag_text = tag_text[1:].strip()
                        
                        if tag_text and tag_text not in best_match.tags:
                            best_match.tags.append(tag_text)
                else:
                    logger.debug(f"Orphaned note at {note['location']} for book '{book_key}'. No matching highlight coverage.")

        logger.info(f"Successfully parsed {len(parsed_clippings)} clippings.")
        return parsed_clippings

    def _parse_single_clipping(self, raw_text: str) -> Optional[Dict]:
        lines = [l for l in raw_text.splitlines() if l.strip()]
        if len(lines) < 3:
            return None

        # Line 1: Book Title
        match_book = re.match(r'(?P<title>.*)\((?P<author>.*)\)', lines[0])
        if match_book:
            title = match_book.group('title').strip()
            author = match_book.group('author').strip()
        else:
            title = lines[0].strip()
            author = "Unknown"

        # Line 2: Metadata
        meta_line = lines[1]
        
        # Type detection using loaded patterns
        if re.search(self.patterns['highlight'], meta_line):
            c_type = 'highlight'
        elif re.search(self.patterns['note'], meta_line):
            c_type = 'note'
        else:
            return None 

        # Location
        loc_match = re.search(r'(' + self.patterns['location'] + r') (?P<location>[0-9,-]+)', meta_line)
        location = loc_match.group('location') if loc_match else ""

        # Page
        page_match = re.search(r'(' + self.patterns['page'] + r') (?P<page>[0-9,-]+)', meta_line)
        page = page_match.group('page') if page_match else ""

        # Date
        # Robust date parsing needs the date string part
        # Pattern: "Added on [Date part]"
        date_part_match = re.search(r"(" + self.patterns['added'] + r") (?P<date_str>.*)$", meta_line)
        if date_part_match:
            date_str = date_part_match.group('date_str')
            date_obj = dateparser.parse(date_str)
        else:
            # Fallback if specific pattern fails, try parsing the whole line end or just give up gracefully
            date_obj = None

        content = "\n".join(lines[2:])
        
        # Apply strict cleaning to the content
        content = TextCleaner.clean_text(content)

        return {
            'book': title,
            'author': author,
            'type': c_type,
            'location': location,
            'page': page,
            'date_time': date_obj,
            'content': content
        }

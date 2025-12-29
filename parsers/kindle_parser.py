import re
import dateparser
import json
import os
import logging
from typing import List, Dict, Optional
from domain.models import Clipping

logger = logging.getLogger("KindleToJex.Parser")

class KindleClippingsParser:
    def __init__(self, separator="==========", language_code="es"):
        self.separator = separator
        self.language_code = language_code
        self._load_language_patterns()

    def _load_language_patterns(self):
        """Loads regex patterns from languages.json based on configured language."""
        # Locate languages.json relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        lang_file = os.path.join(current_dir, '..', 'resources', 'languages.json')
        
        # Default fallback patterns (Spanish) if file load fails
        self.patterns = {
            "highlight": "subrayado|Subrayado",
            "note": "nota|Nota",
            "page": "página",
            "added": "Añadid. el",
            "location": "posición|Pos\."
        }

        if os.path.exists(lang_file):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    langs = json.load(f)
                    if self.language_code in langs:
                        self.patterns = langs[self.language_code]
                        logger.info(f"Loaded patterns for language: {self.language_code}")
                    else:
                        logger.warning(f"Language '{self.language_code}' not found in {lang_file}. Using defaults.")
            except Exception as e:
                logger.error(f"Error loading languages.json: {e}")
        else:
             logger.warning(f"languages.json not found at {os.path.abspath(lang_file)}. Using internal defaults.")

    def parse_file(self, file_path: str, encoding: str = "utf-8-sig") -> List[Clipping]:
        logger.info(f"Parsing file: {file_path}")
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return []
        
        raw_clippings = content.split(self.separator)
        location_map: Dict[str, Clipping] = {} 
        parsed_clippings: List[Clipping] = []

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
                
                loc_id = data['location'].split('-')[-1] 
                location_map[loc_id] = clipping
                parsed_clippings.append(clipping)
            
            elif data['type'] == 'note':
                loc_id = data['location'].split('-')[-1]
                if loc_id in location_map:
                    parent_clipping = location_map[loc_id]
                    tag_text = data['content'].replace('.', ',').strip()
                    if tag_text and not tag_text[0].isalpha():
                        tag_text = tag_text[1:].strip()
                    parent_clipping.tags.append(tag_text)
                else:
                    logger.debug(f"Orphaned note found at location {loc_id}, skipping.")

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

        return {
            'book': title,
            'author': author,
            'type': c_type,
            'location': location,
            'page': page,
            'date_time': date_obj,
            'content': content
        }

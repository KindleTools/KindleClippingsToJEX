import re
import dateparser
from typing import List, Dict, Optional
from src.domain.models import Clipping

class KindleClippingsParser:
    def __init__(self, separator="=========="):
        self.separator = separator
        # Regex per language could be loaded here. Defaulting to Spanish as in original.
        self.highl_kws = 'subrayado|Subrayado'
        self.note_kws = 'nota|Nota'
        self.page_kws = 'página'
        self.added_kws = 'Añadid. el'
        self.locs_kws = 'posición|Pos\.'

    def parse_file(self, file_path: str, encoding: str = "utf-8-sig") -> List[Clipping]:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        raw_clippings = content.split(self.separator)
        clippings_map: Dict[str, Clipping] = {} # Keyed by date mainly to associate notes
        
        # Temporary storage to link notes to highlights. 
        # Original logic: Highlights and Notes share location/time context? 
        # Original code mapped Notes to Highlights by matching location? 
        # Actually in original `kindle.py`: 
        #   Highlight -> saves to `location[loc] = date` AND `csv[date] = ...`
        #   Note -> finds date via `location[loc]`, then updates `csv[date]["tags"]`
        
        location_map: Dict[str, str] = {} # Location -> Date (iso format or object)
        parsed_clippings: List[Clipping] = []

        for raw in raw_clippings:
            if not raw.strip():
                continue
            
            data = self._parse_single_clipping(raw)
            if not data:
                continue

            if data['type'] == 'highlight':
                # Create Clipping object
                clipping = Clipping(
                    content=data['content'],
                    book_title=data['book'],
                    author=data['author'],
                    date_time=data['date_time'],
                    location=data['location'],
                    page=data['page'],
                    type='highlight'
                )
                
                # Store for lookup
                # Keying by Location ID (range start)
                loc_id = data['location'].split('-')[-1] # Usually the end range? Original used split('-')[-1]
                location_map[loc_id] = clipping
                parsed_clippings.append(clipping)
            
            elif data['type'] == 'note':
                # It's a note, try to find the highlight
                loc_id = data['location'].split('-')[-1]
                if loc_id in location_map:
                    parent_clipping = location_map[loc_id]
                    # Process tag
                    tag_text = data['content'].replace('.', ',').strip()
                    if tag_text and not tag_text[0].isalpha():
                        tag_text = tag_text[1:].strip()
                    parent_clipping.tags.append(tag_text)
                else:
                    # Orphaned note or logic mismatch
                    # For now we ignore or log? Original printed "Cannot find this location"
                    pass

        return parsed_clippings

    def _parse_single_clipping(self, raw_text: str) -> Optional[Dict]:
        lines = [l for l in raw_text.splitlines() if l.strip()]
        if len(lines) < 3:
            return None

        # Line 1: Book Title (Author)
        # Using regex to separate title and author more robustly?
        # Expecting: "Title (Author)"
        # Sometimes: "Title (Subtitle) (Author)" - The last parentheses is usually author
        match_book = re.match(r'(?P<title>.*)\((?P<author>.*)\)', lines[0])
        if match_book:
            title = match_book.group('title').strip()
            author = match_book.group('author').strip()
        else:
            title = lines[0].strip()
            author = "Unknown"

        # Line 2: Metadata (Type, Location, Date)
        meta_line = lines[1]
        
        # Type
        if re.search(self.highl_kws, meta_line):
            c_type = 'highlight'
        elif re.search(self.note_kws, meta_line):
            c_type = 'note'
        else:
            return None # Bookmark?

        # Location
        loc_match = re.search(r'(' + self.locs_kws + r') (?P<location>[0-9,-]+)', meta_line)
        location = loc_match.group('location') if loc_match else ""

        # Page
        page_match = re.search(r'(' + self.page_kws + r') (?P<page>[0-9,-]+)', meta_line)
        page = page_match.group('page') if page_match else ""

        # Date
        # Original: Añadid. el viernes, 24 de agosto de 2018 19:15:36
        # Using dateparser is robust
        # We need to extract the date part after "Añadid. el "
        date_part_match = re.search(r"(" + self.added_kws + r") (?P<date_str>.*)$", meta_line)
        if date_part_match:
            date_str = date_part_match.group('date_str')
            date_obj = dateparser.parse(date_str)
        else:
            date_obj = None

        # Content (Line 3 onwards)
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

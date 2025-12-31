import re
import dateparser
import json
import os
import logging
from typing import List, Dict, Optional, Tuple, Any
from domain.models import Clipping
from parsers.patterns import DEFAULT_PATTERNS
from utils.text_cleaner import TextCleaner
from utils.title_cleaner import TitleCleaner
from services.identity_service import IdentityService

logger = logging.getLogger("KindleToJex.Parser")


class KindleClippingsParser:
    """
    Parses 'My Clippings.txt' files from Kindle devices.
    """

    def __init__(self, separator="==========", language_code="es", language_file=None):
        self.separator = separator
        self.language_code = language_code
        self.language_file = language_file
        self._load_language_patterns()
        self.stats: Dict[str, Any] = {
            "total": 0,
            "parsed": 0,
            "skipped": 0,
            "failed_blocks": [],
            "titles_cleaned": 0,
            "title_changes": [],
        }

    def _load_language_patterns(self):
        """Loads regex patterns from languages.json based on configured language."""
        if self.language_file:
            lang_file = self.language_file
        else:
            # Fallback if no file provided (try resources/languages.json)
            # We assume 'resources' is at the project root level relative to execution or package
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            lang_file = os.path.join(base_dir, "resources", "languages.json")

        # Default fallback patterns (Spanish)
        # Use imported constant as default
        self.default_patterns = DEFAULT_PATTERNS
        self.patterns = self.default_patterns

        self.available_languages = {}
        if os.path.exists(lang_file):
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    self.available_languages = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.error(f"Error loading languages.json: {e}")
        else:
            logger.warning(f"languages.json not found at {os.path.abspath(lang_file)}.")

        if self.language_code != "auto":
            if self.language_code in self.available_languages:
                self.patterns = self.available_languages[self.language_code]
                logger.info(f"Loaded patterns for language: {self.language_code}")
            else:
                logger.warning(f"Language '{self.language_code}' not found. Using defaults.")

    def _detect_language(self, content: str) -> str:
        """Attempts to detect language by checking patterns against file content."""
        logger.info("Attempting robust auto-detection of language...")
        sample = content[:5000]  # Check first 5000 chars

        scores = {}

        for lang_code, patterns in self.available_languages.items():
            score = 0
            # Check for multiple keywords to be sure
            keywords = [
                patterns.get("highlight"),
                patterns.get("note"),
                patterns.get("location"),
                patterns.get("added"),
            ]
            for kw in keywords:
                if kw and re.search(kw, sample, re.IGNORECASE):
                    score += 1

            if score > 0:
                scores[lang_code] = score

        if scores:
            # Pick the language with the most keyword matches
            best_lang = max(scores, key=lambda k: scores[k])
            logger.info(f"Language detected: {best_lang} (Score: {scores[best_lang]})")
            return best_lang

        logger.warning("Auto-detection failed. Falling back to 'es'.")
        return "es"

    def get_stats(self):
        return self.stats

    def parse_file(self, file_path: str, encoding: Optional[str] = None) -> List[Clipping]:
        """
        Parses parsing with robust encoding handling.
        """
        logger.info(f"Parsing file: {file_path}")
        self.stats = {
            "total": 0,
            "parsed": 0,
            "skipped": 0,
            "failed_blocks": [],
            "titles_cleaned": 0,
            "title_changes": [],
            "pdfs_cleaned": 0,
        }

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []

        # List of encodings to try in order of likelihood
        encodings_to_try = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
        if encoding:
            encodings_to_try.insert(0, encoding)

        content = None
        for enc in encodings_to_try:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
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

        if content.startswith("\ufeff"):
            content = content[1:]

        raw_clippings = content.split(self.separator)

        # Auto-detect language if requested
        if self.language_code == "auto":
            detected_lang = self._detect_language(content)
            if detected_lang in self.available_languages:
                self.patterns = self.available_languages[detected_lang]
            else:
                self.patterns = self.default_patterns

        parsed_clippings: List[Clipping] = []
        notes_data: List[Dict] = []

        # Pass 1: Collect Highlights and Notes separately
        for raw in raw_clippings:
            if not raw.strip():
                continue

            self.stats["total"] += 1
            data = self._parse_single_clipping(raw)

            if not data:
                self.stats["skipped"] += 1
                # Store first 50 chars of failed block for debugging
                snippet = raw.strip().replace("\n", " ")[:500]
                self.stats["failed_blocks"].append(snippet)
                continue

            self.stats["parsed"] += 1

            if data["type"] == "highlight":
                clipping = Clipping(
                    content=data["content"],
                    book_title=data["book"],
                    author=data["author"],
                    date_time=data["date_time"],
                    location=data["location"],
                    page=data["page"],
                    entry_type="highlight",
                )

                # Generate Deterministic ID
                clipping.uid = IdentityService.generate_id(clipping)

                parsed_clippings.append(clipping)

            elif data["type"] == "note":
                notes_data.append(data)

        # Pass 2: Link Notes to Highlights (Logic remains same)
        self._link_notes_to_highlights(parsed_clippings, notes_data)

        logger.info(f"Parsing Stats: {self.stats}")
        return parsed_clippings

    def _link_notes_to_highlights(self, highlights, notes):
        # Helper extracted from original monolithic function
        def parse_loc_range(loc_str: str) -> Tuple[int, int]:
            parts = loc_str.split("-")
            try:
                s = int(parts[0])
                e = int(parts[1]) if len(parts) > 1 else s
                return s, e
            except Exception:
                return -1, -1

        highlights_by_book: Dict[str, List[Clipping]] = {}
        for clip in highlights:
            if clip.book_title not in highlights_by_book:
                highlights_by_book[clip.book_title] = []
            highlights_by_book[clip.book_title].append(clip)

        for note in notes:
            book_key = note["book"]
            if book_key in highlights_by_book:
                candidates = highlights_by_book[book_key]
                note_start, _ = parse_loc_range(note["location"])

                best_match = None
                for h in candidates:
                    h_start, h_end = parse_loc_range(h.location)
                    if h_start <= note_start <= h_end:
                        best_match = h
                        break

                if best_match:
                    raw_tags = re.split(r"[.,;\n\r]", note["content"])
                    for raw_tag in raw_tags:
                        tag_text = raw_tag.strip()
                        if not tag_text:
                            continue
                        if not tag_text[0].isalnum():
                            tag_text = tag_text[1:].strip()
                        if tag_text and tag_text not in best_match.tags:
                            best_match.tags.append(tag_text)

    def _parse_single_clipping(self, raw_text: str) -> Optional[Dict]:
        lines = [line_str for line_str in raw_text.splitlines() if line_str.strip()]
        if len(lines) < 3:
            return None

        # Robust Header Parsing:
        # Sometimes the title/author line is split across multiple lines or is just very long.
        # We search for the "Metadata Line" (starts with "- Your Highlight...", "- La nota...", etc.)
        # and treat everything before it as the Header.

        meta_index = -1
        c_type = ""

        for i in range(1, len(lines)):  # Start checking from 2nd line
            line = lines[i]
            if re.search(self.patterns["highlight"], line):
                c_type = "highlight"
                meta_index = i
                break
            elif re.search(self.patterns["note"], line):
                c_type = "note"
                meta_index = i
                break

        if meta_index == -1:
            # Metadata pattern not found, might be a corrupted block
            return None

        # Header is everything before meta_index
        header_lines = lines[:meta_index]
        full_header = " ".join(header_lines).replace("\n", " ").strip()

        # Line 1: Book Title Parsing using the combined header
        match_book = re.match(r"(?P<title>.*)\((?P<author>.*)\)", full_header)
        if match_book:
            title = match_book.group("title").strip()
            author = match_book.group("author").strip()
        else:
            title = full_header.strip()
            author = "Unknown"

        # Apply title hygiene
        original_title = title
        title = TitleCleaner.clean_title(title)
        if title != original_title:
            self.stats["titles_cleaned"] = self.stats.get("titles_cleaned", 0) + 1
            change = (original_title, title)
            if change not in self.stats["title_changes"]:
                self.stats["title_changes"].append(change)

        # Line 2: Metadata
        meta_line = lines[meta_index]

        # Location
        loc_match = re.search(
            r"(" + self.patterns["location"] + r") (?P<location>[0-9,-]+)", meta_line
        )
        location = loc_match.group("location") if loc_match else ""

        # Page
        page_match = re.search(r"(" + self.patterns["page"] + r") (?P<page>[0-9,-]+)", meta_line)
        page = page_match.group("page") if page_match else ""

        # Date
        # Robust date parsing needs the date string part
        # Pattern: "Added on [Date part]"
        date_part_match = re.search(
            r"(" + self.patterns["added"] + r") (?P<date_str>.*)$", meta_line
        )
        if date_part_match:
            date_str = date_part_match.group("date_str")
            date_obj = dateparser.parse(date_str)
        else:
            # Fallback if specific pattern fails, try parsing the whole line end or just give up gracefully
            date_obj = None

        content = "\n".join(lines[meta_index + 1 :])

        # Apply strict cleaning to the content
        original_content = content
        content = TextCleaner.clean_text(content)

        # Heuristic: If length got shorter by removing "- " pattern, it was likely de-hyphenated
        # This is a bit rough, but 'clean_text' does more than just de-hyphenate.
        # A simpler check is if "letter-\n" existed in original but is gone.
        if re.search(r"[^\W\d_]+-\s*\n\s*[^\W\d_]+", original_content) and not re.search(
            r"[^\W\d_]+-\s*\n\s*[^\W\d_]+", content
        ):
            self.stats["pdfs_cleaned"] = self.stats.get("pdfs_cleaned", 0) + 1

        return {
            "book": title,
            "author": author,
            "type": c_type,
            "location": location,
            "page": page,
            "date_time": date_obj,
            "content": content,
        }

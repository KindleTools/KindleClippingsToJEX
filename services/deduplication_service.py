from datetime import datetime
from typing import List, Tuple, Dict, TypedDict
from domain.models import Clipping
import logging

logger = logging.getLogger("KindleToJex.Deduplicator")

class EnhancedClip(TypedDict):
    clip: Clipping
    start: int
    end: int
    len: int

class SmartDeduplicator:
    """
    Intelligent logic to clean up the 'append-only' mess of My Clippings.txt.
    Handles:
    1. Overlapping highlights (keeping the longest/most complete version).
    2. Duplicate notes (keeping the latest version).
    """

    OVERLAP_TOLERANCE_CHARS = 5

    def deduplicate(self, clippings: List[Clipping]) -> List[Clipping]:
        if not clippings:
            return []

        # 1. Group by Book & Author (We process each book independently)
        books: Dict[str, List[Clipping]] = {}
        for clip in clippings:
            # Reset flag initially (in case of re-run)
            clip.is_duplicate = False
            
            key = clip.title_hash # author + title
            if key not in books:
                books[key] = []
            books[key].append(clip)

        # 2. Process each book
        for key, book_clippings in books.items():
            # Separate Notes and Highlights
            highlights = [c for c in book_clippings if c.entry_type == 'highlight']
            notes = [c for c in book_clippings if c.entry_type == 'note']

            # Process Highlights (Overlap Logic)
            self._flag_duplicates_highlights(highlights)
            
            # Process Notes (Latest by Location Logic)
            self._flag_duplicates_notes(notes)

        # Return ALL clippings (some are now flagged)
        # Restore chronological order if shuffled by grouping
        clippings.sort(key=lambda x: x.date_time if x.date_time else datetime.min)
        
        return clippings

    def _merge_tags(self, source: Clipping, target: Clipping):
        """Merges tags from source to target, avoiding duplicates."""
        if source.tags:
            existing_tags = set(target.tags)
            for tag in source.tags:
                if tag not in existing_tags:
                    target.tags.append(tag)
                    existing_tags.add(tag)

    def _flag_duplicates_highlights(self, highlights: List[Clipping]):
        """
        Marks highlights that are subsets of other highlights as duplicates.
        Also flags very short highlights as potential accidents.
        """
        # Helper to parse location
        def parse_loc(loc_str: str) -> Tuple[int, int]:
            try:
                parts = loc_str.split('-')
                start = int(parts[0])
                end = int(parts[1]) if len(parts) > 1 else start
                return start, end
            except (ValueError, IndexError):
                return 0, 0

        # Attach parsed locs for sorting
        enhanced: List[EnhancedClip] = []
        for h in highlights:
            # Heuristics for "Accidental" vs "Short but valid"
            # SKIP if the user has explicitly tagged/noted this highlight.
            if not h.tags:
                text = h.content.strip()
                length = len(text)
                
                is_garbage = length < 5
                is_fragment = length < 75 and (text and text[0].islower())
                is_incomplete = length < 75 and (text and text[-1] not in {'.', '!', '?', '"', '”', ')'})
                
                if is_garbage or is_fragment or is_incomplete:
                     h.is_duplicate = True
            
            s, e = parse_loc(h.location)
            enhanced.append({
                'clip': h,
                'start': s,
                'end': e,
                'len': len(h.content)
            })

        # Sort primarily by Start Location
        enhanced.sort(key=lambda x: int(x['start']))

        if not enhanced:
            return

        # We keep track of the "active" highlight we are comparing against
        # This is the "survivor" so far in the chain
        survivor = enhanced[0]

        for current in enhanced[1:]:
            # Check overlap between 'current' and the last 'survivor'
            is_overlapping = (current['start'] >= survivor['start']) and (current['start'] <= survivor['end'] + self.OVERLAP_TOLERANCE_CHARS)
            
            if is_overlapping:
                # Decide which one is the duplicate
                if survivor['clip'].content in current['clip'].content:
                    # Survivor is a SUBSET -> Survivor is duplicate
                    self._merge_tags(survivor['clip'], current['clip']) # Rescue tags
                    survivor['clip'].is_duplicate = True
                    survivor = current # Current becomes the new survivor
                elif current['clip'].content in survivor['clip'].content:
                    # Current is a SUBSET -> Current is duplicate
                    self._merge_tags(current['clip'], survivor['clip']) # Rescue tags
                    current['clip'].is_duplicate = True
                    # Survivor stays the same
                else:
                    # Partial overlap (fuzzy logic)
                    overlap_amount = min(survivor['end'], current['end']) - max(survivor['start'], current['start'])
                    span = max(survivor['end'], current['end']) - min(survivor['start'], current['start'])
                    
                    if span > 0 and (overlap_amount / span) > 0.5:
                        # Significant overlap -> Keep longest
                        if current['len'] > survivor['len']:
                             self._merge_tags(survivor['clip'], current['clip'])
                             survivor['clip'].is_duplicate = True
                             survivor = current
                        else:
                             self._merge_tags(current['clip'], survivor['clip'])
                             current['clip'].is_duplicate = True
            else:
                # No overlap -> Current becomes the new survivor for the next block
                survivor = current

    def _flag_duplicates_notes(self, notes: List[Clipping]):
        """
        Marks older notes at the same location as duplicates.
        """
        # Map location_id -> List of notes at that location
        notes_by_loc: Dict[str, List[Clipping]] = {}

        for n in notes:
            if n.location not in notes_by_loc:
                notes_by_loc[n.location] = []
            notes_by_loc[n.location].append(n)
            
        for loc, group in notes_by_loc.items():
            if len(group) > 1:
                # Sort by date descending (Newest first)
                group.sort(key=lambda x: x.date_time if x.date_time else datetime.min, reverse=True)
                
                # The first one is the keeper, all others are dupes
                keeper = group[0]
                for old_note in group[1:]:
                    self._merge_tags(old_note, keeper)
                    old_note.is_duplicate = True

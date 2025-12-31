import tarfile
import io
import logging
import hashlib
from uuid import uuid4
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from domain.models import Clipping
from domain.joplin import (
    JoplinNotebook, JoplinNote, JoplinTag, 
    JoplinTagAssociation, JoplinEntityType
)
from exporters.base import BaseExporter

logger = logging.getLogger("KindleToJex.JoplinExporter")

class JoplinEntityBuilder:
    """
    Helper to create Dictionary-like objects representing Joplin entities.
    Now uses strict Dataclasses from domain.joplin.
    """
    
    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    @staticmethod
    def _generate_id(key: str = None) -> str:
        """
        Generates a 32-char hex ID.
        If 'key' is provided, returns a deterministic MD5 hash of the key.
        If 'key' is None, returns a random UUID.
        """
        if key:
            # MD5 is used here for deterministic ID generation, not security.
            # We want "Title" -> Always same ID.
            return hashlib.md5(key.encode('utf-8')).hexdigest()
        return uuid4().hex

    @staticmethod
    def create_notebook(title: str, parent_id: str = "") -> JoplinNotebook:
        now = JoplinEntityBuilder._now()
        # ID is based on TITLE ONLY to allow moving notebook without changing ID
        # This enables potential future "move" instead of "duplicate" behavior
        id_seed = f"notebook:{title}"
        return JoplinNotebook(
            id=JoplinEntityBuilder._generate_id(id_seed),
            parent_id=parent_id,
            title=title,
            created_time=now,
            updated_time=now,
            user_created_time=now,
            user_updated_time=now
        )

    @staticmethod
    def create_note(title: str, body: str, parent_id: str, 
                   created_time: datetime = None, 
                   latitude=0.0, longitude=0.0, altitude=0.0, author="",
                   clipping_ref: Clipping = None) -> JoplinNote:
        
        now = created_time.isoformat(timespec='milliseconds') if created_time else JoplinEntityBuilder._now()
        
        # Deterministic ID strategy for Notes:
        # We want to allow content edits without changing ID (so Joplin updates the note),
        # BUT we need uniqueness.
        # Strategy: Book + Location is the most stable "Identity" of a highlight.
        if clipping_ref:
            # key: "note:BookTitle:Location:Page" 
            # (Adding page to be extra safe against location formatting changes)
            id_seed = f"note:{clipping_ref.book_title}:{clipping_ref.location}:{clipping_ref.page}"
        else:
            # Fallback for manual notes or unknown origin
            id_seed = None 

        return JoplinNote(
            id=JoplinEntityBuilder._generate_id(id_seed),
            parent_id=parent_id,
            title=title,
            body=body,
            created_time=now,
            updated_time=now,
            user_created_time=now,
            user_updated_time=now,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            author=author,
            source='kindle-to-jex',
            source_application='KindleClippingsToJEX v0.2.0',
            is_todo=0,
            markup_language=1
        )

    @staticmethod
    def create_tag(title: str) -> JoplinTag:
        now = JoplinEntityBuilder._now()
        id_seed = f"tag:{title.lower().strip()}" # Tags should be case-insensitive id-wise
        return JoplinTag(
            id=JoplinEntityBuilder._generate_id(id_seed),
            title=title,
            parent_id='',
            created_time=now,
            updated_time=now,
            user_created_time=now,
            user_updated_time=now
        )

    @staticmethod
    def create_tag_association(tag_id: str, note_id: str) -> JoplinTagAssociation:
        now = JoplinEntityBuilder._now()
        # Association ID should also be deterministic to avoid duplicate links
        id_seed = f"assoc:{note_id}:{tag_id}"
        return JoplinTagAssociation(
            id=JoplinEntityBuilder._generate_id(id_seed),
            note_id=note_id,
            tag_id=tag_id,
            created_time=now,
            updated_time=now,
            user_created_time=now,
            user_updated_time=now
        )

class JoplinExporter(BaseExporter):
    """
    Handles the creation of JEX (Joplin Export) files, including 
    the logic for organizing clippings into notebooks.
    """
    def __init__(self):
        self.entities_to_export: List[Any] = []
        self.authors_cache: Dict[str, str] = {}
        self.books_cache: Dict[str, str] = {}
        self.tags_cache: Dict[str, str] = {}
        self.builder = JoplinEntityBuilder()

    def export(self, clippings: List[Clipping], output_file: str, context: Dict[str, Any] = None):
        """
        Main entry point for JEX export.
        """
        # 1. Reset Internal State
        self.entities_to_export = []
        self.authors_cache = {}
        self.books_cache = {}
        self.tags_cache = {}
        
        # 2. Extract Context
        context = context or {}
        root_notebook_name = context.get('root_notebook', 'Kindle Imports')
        creator = context.get('creator', 'System')
        location = context.get('location', (0.0, 0.0, 0)) # lat, lon, alt
        
        # 3. Create Root Notebook
        root_nb = self.builder.create_notebook(root_notebook_name)
        self.entities_to_export.append(root_nb)
        root_id = root_nb.id
        
        # 4. Process Clippings
        skipped_dupes = 0
        for clip in clippings:
            if clip.is_duplicate:
                skipped_dupes += 1
                continue
            self._process_single_clipping(clip, root_id, location, creator)
            
        if skipped_dupes > 0:
            logger.info(f"Skipped {skipped_dupes} duplicate items during JEX export.")

        logger.info(f"Exporting JEX archive to: {output_file}")

        # 5. Write JAR
        self._write_jex_file(output_file, self.entities_to_export)
    
    def _process_single_clipping(self, clip: Clipping, root_id: str, 
                                location: Tuple[float, float, int], creator: str):
        
        # Author Notebook - Uppercase per user requirement
        author_name = clip.author.upper()
        if author_name not in self.authors_cache:
            author_nb = self.builder.create_notebook(author_name, parent_id=root_id)
            self.entities_to_export.append(author_nb)
            self.authors_cache[author_name] = author_nb.id
        author_id = self.authors_cache[author_name]

        # Book Notebook
        book_title = clip.book_title
        book_cache_key = f"{author_name}__{book_title}"
        if book_cache_key not in self.books_cache:
            book_nb = self.builder.create_notebook(book_title, parent_id=author_id)
            self.entities_to_export.append(book_nb)
            self.books_cache[book_cache_key] = book_nb.id
        book_id = self.books_cache[book_cache_key]

        # Create Note
        note_title = self._format_title(clip)
        note_body = self._format_body(clip)
        
        note = self.builder.create_note(
            title=note_title,
            body=note_body,
            parent_id=book_id,
            created_time=clip.date_time,
            latitude=location[0],
            longitude=location[1],
            altitude=location[2],
            author=creator,
            clipping_ref=clip
        )
        self.entities_to_export.append(note)
        
        # Handle Tags
        for tag_str in clip.tags:
            if tag_str not in self.tags_cache:
                tag_obj = self.builder.create_tag(tag_str)
                self.entities_to_export.append(tag_obj)
                self.tags_cache[tag_str] = tag_obj.id
            
            tag_id = self.tags_cache[tag_str]
            assoc = self.builder.create_tag_association(tag_id=tag_id, note_id=note.id)
            self.entities_to_export.append(assoc)

    def _write_jex_file(self, output_filename: str, entites: List[Any]):
        """
        Writes the entity list to a .jex tarball.
        """
        if not output_filename.endswith('.jex'):
            output_filename += '.jex'
            
        with tarfile.open(output_filename, "w:") as tar:
            tar.format = tarfile.USTAR_FORMAT
            
            for entity_obj in entites:
                # Convert Dataclass to Dict for serialization
                entity = entity_obj.to_dict()
                
                file_name = f"{entity['id']}.md"
                content = self._create_entity_content(entity)
                
                # Create a file object in memory
                file_obj = io.BytesIO(content.encode('utf-8'))
                
                # Create tar info
                tar_info = tarfile.TarInfo(name=file_name)
                tar_info.size = len(file_obj.getvalue())
                tar_info.mtime = int(datetime.now().timestamp())
                
                tar.addfile(tar_info, file_obj)

    def _create_entity_content(self, entity: Dict[str, Any]) -> str:
        # Standard Joplin RAW Format:
        # Line 1: Title
        # Line 2: Empty
        # Line 3+: Body (if note)
        # ... Empty Line ...
        # Line N: Properties
        
        parts = []
        
        # 1. Title (Header) - Universal for Notes, Tags, etc.
        # The user confirmed: "Tag name up top".
        parts.append(entity.get('title', ''))
        parts.append("") # Blank separator
        
        # 2. Body (If present)
        if entity.get('body'):
            parts.append(entity['body'])
            parts.append("") # Blank separator
            
        # 3. Properties
        special_keys = {'title', 'body', 'type_'}
        
        # Helper for value normalization
        def normalize_val(v):
            return v.value if hasattr(v, 'value') else v

        # Add generic properties
        for key, value in entity.items():
            if key not in special_keys:
                parts.append(f"{key}: {normalize_val(value)}")
            
        # 4. Type (Last)
        if 'type_' in entity:
            parts.append(f"type_: {normalize_val(entity['type_'])}")
            
        # Join adds newlines between parts.
        # If parts=['Title', '', 'id: 1'] -> "Title\n\nid: 1" (Correct single blank line)
        # If parts=['Title', '', 'Body', '', 'id: 1'] -> "Title\n\nBody\n\nid: 1" (Correct)
        return "\n".join(parts)

    # Configurable Layout Constants
    KINDLE_LOCATION_RATIO = 16.69

    def _format_title(self, clip: Clipping) -> str:
        snippet = clip.content[:50].replace('\n', ' ')
        page_num = 0
        
        # Strategy 1: Real Page Number
        if clip.page:
            clean_page = clip.page.replace('-', '')
            if clean_page.isnumeric():
                try:
                    # If range "100-102", take 100
                    page_num = int(clip.page.split('-')[0])
                except ValueError:
                    page_num = 0
        
        # Strategy 2: Heuristic from Location
        # If no valid page found, try calculating from location
        # Standard heuristic: Location / RATIO approx = Page
        if page_num == 0 and clip.location:
             clean_loc = clip.location.replace('-', '')
             if clean_loc.isnumeric():
                 try:
                     l_val = int(clip.location.split('-')[0])
                     page_num = int(l_val / self.KINDLE_LOCATION_RATIO)
                     # Ensure at least page 1 if location exists
                     if page_num == 0: page_num = 1
                 except ValueError:
                     page_num = 0

        # Formatting
        if page_num > 0:
            # Clean [0042] format
            ref = f"[{page_num:04d}] "
        else:
            # Ultimate Fallback if neither page nor location are numbers (e.g. "ix" or empty)
            # Use original text or empty
            ref = f"[{clip.page}] " if clip.page else ""
            
        return f"{ref}{snippet}"

    def _format_body(self, clip: Clipping) -> str:
        meta = [
            f"- date: {clip.date_time}",
            f"- author: {clip.author}", # Original Case
            f"- book: {clip.book_title}",
            f"- page: {clip.page}" if clip.page else None,
            # location removed as per request (technical field)
            f"- tags: {', '.join(clip.tags)}" if clip.tags else None
        ]
        footer = "\n".join([m for m in meta if m])
        return f"{clip.content}\n\n\n-----\n{footer}\n-----\n"

# Maintain alias for backward compatibility if needed, though we will refactor usage.
JexExportService = JoplinExporter

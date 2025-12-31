import tarfile
import io
import logging
from enum import IntEnum
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List, Tuple
from domain.models import Clipping
from exporters.base import BaseExporter

logger = logging.getLogger("KindleToJex.JoplinExporter")

class JoplinEntityType(IntEnum):
    NOTE = 1
    FOLDER = 2
    SETTING = 3
    RESOURCE = 4
    TAG = 5
    NOTE_TAG = 6
    SEARCH = 7
    ALARM = 8
    MASTER_KEY = 9
    ITEM_CHANGE = 10
    NOTE_RESOURCE = 11
    RESOURCE_LOCAL_STATE = 12
    REVISION = 13
    MIGRATION = 14
    SMART_FILTER = 15

class JoplinEntityBuilder:
    """
    Helper to create dictionaries representing Joplin entities (Notes, Notebooks, Tags).
    """
    
    @staticmethod
    def _now():
        return datetime.now().isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    @staticmethod
    def _id():
        return uuid4().hex

    @staticmethod
    def create_notebook(title: str, parent_id: str = "") -> Dict[str, Any]:
        now = JoplinEntityBuilder._now()
        data = {
            'id': JoplinEntityBuilder._id(),
            'parent_id': parent_id,
            'title': title,
            'type_': JoplinEntityType.FOLDER,
            'created_time': now,
            'updated_time': now,
            'user_created_time': now,
            'user_updated_time': now,
            'encryption_applied': 0,
            'is_shared': 0
        }
        return data

    @staticmethod
    def create_note(title: str, body: str, parent_id: str, 
                   created_time: datetime = None, 
                   latitude=0.0, longitude=0.0, altitude=0.0, author="") -> Dict[str, Any]:
        
        now = created_time.isoformat(timespec='milliseconds') if created_time else JoplinEntityBuilder._now()
        data = {
            'id': JoplinEntityBuilder._id(),
            'parent_id': parent_id,
            'title': title,
            'body': body,
            'type_': JoplinEntityType.NOTE,
            'created_time': now,
            'updated_time': now,
            'user_created_time': now,
            'user_updated_time': now,
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
            'author': author,
            'source': 'kindle-to-jex',
            'source_application': 'kindle',
            'is_todo': 0,
            'encryption_applied': 0,
            'is_shared': 0,
            'order': 0,
            'markup_language': 1 # Markdown
        }
        return data

    @staticmethod
    def create_tag(title: str) -> Dict[str, Any]:
        now = JoplinEntityBuilder._now()
        data = {
            'id': JoplinEntityBuilder._id(),
            'title': title,
            'type_': JoplinEntityType.TAG,
            'parent_id': '',
            'created_time': now,
            'updated_time': now,
            'user_created_time': now,
            'user_updated_time': now,
            'encryption_applied': 0
        }
        return data

    @staticmethod
    def create_tag_association(tag_id: str, note_id: str) -> Dict[str, Any]:
        now = JoplinEntityBuilder._now()
        data = {
            'id': JoplinEntityBuilder._id(),
            'note_id': note_id,
            'tag_id': tag_id,
            'type_': JoplinEntityType.NOTE_TAG,
            'created_time': now,
            'updated_time': now,
            'user_created_time': now,
            'user_updated_time': now,
            'encryption_applied': 0
        }
        return data

class JoplinExporter(BaseExporter):
    """
    Handles the creation of JEX (Joplin Export) files, including 
    the logic for organizing clippings into notebooks.
    """
    def __init__(self):
        self.entities_to_export: List[Dict] = []
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
        root_id = root_nb['id']
        
        # 4. Process Clippings
        skipped_dupes = 0
        for clip in clippings:
            if clip.is_duplicate:
                skipped_dupes += 1
                continue
            self._process_single_clipping(clip, root_id, location, creator)
            
        if skipped_dupes > 0:
            logger.info(f"Skipped {skipped_dupes} duplicate items during JEX export.")

        # 5. Write JAR
        self._write_jex_file(output_file, self.entities_to_export)
    
    def _process_single_clipping(self, clip: Clipping, root_id: str, 
                                location: Tuple[float, float, int], creator: str):
        
        # Author Notebook
        author_name = clip.author
        if author_name not in self.authors_cache:
            author_nb = self.builder.create_notebook(author_name, parent_id=root_id)
            self.entities_to_export.append(author_nb)
            self.authors_cache[author_name] = author_nb['id']
        author_id = self.authors_cache[author_name]

        # Book Notebook
        book_title = clip.book_title
        book_cache_key = f"{author_name}__{book_title}"
        if book_cache_key not in self.books_cache:
            book_nb = self.builder.create_notebook(book_title, parent_id=author_id)
            self.entities_to_export.append(book_nb)
            self.books_cache[book_cache_key] = book_nb['id']
        book_id = self.books_cache[book_cache_key]

        # Create Note
        note_title = self._format_title(clip.content, clip.page)
        note_body = self._format_body(clip)
        
        note = self.builder.create_note(
            title=note_title,
            body=note_body,
            parent_id=book_id,
            created_time=clip.date_time,
            latitude=location[0],
            longitude=location[1],
            altitude=location[2],
            author=creator
        )
        self.entities_to_export.append(note)
        
        # Handle Tags
        for tag_str in clip.tags:
            if tag_str not in self.tags_cache:
                tag_obj = self.builder.create_tag(tag_str)
                self.entities_to_export.append(tag_obj)
                self.tags_cache[tag_str] = tag_obj['id']
            
            tag_id = self.tags_cache[tag_str]
            assoc = self.builder.create_tag_association(tag_id=tag_id, note_id=note['id'])
            self.entities_to_export.append(assoc)

    def _write_jex_file(self, output_filename: str, entites: List[Dict[str, Any]]):
        """
        Writes the entity list to a .jex tarball.
        """
        if not output_filename.endswith('.jex'):
            output_filename += '.jex'
            
        with tarfile.open(output_filename, "w:") as tar:
            tar.format = tarfile.USTAR_FORMAT
            
            for entity in entites:
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
        parts = []
        
        # 1. Title (Header)
        if 'title' in entity:
            parts.append(f"{entity['title']}\n\n")
        
        # 2. Body (Header)
        if 'body' in entity:
            parts.append(f"{entity['body']}\n\n")
            
        # 3. Properties
        special_keys = ['title', 'body', 'type_']
        for key, value in entity.items():
            if key in special_keys:
                continue
            parts.append(f"{key}: {value}\n")
            
        # 4. Type (Last)
        if 'type_' in entity:
            parts.append(f"type_: {entity['type_']}")
            
        return "".join(parts)

    def _format_title(self, text: str, page: str) -> str:
        snippet = text[:50].replace('\n', ' ')
        ref = ''
        if page and page.replace('-', '').isnumeric() and len(page) < 7:
             try:
                 p_val = int(page.split('-')[0]) 
                 ref = f"[{p_val:04d}] " 
             except:
                 ref = f"[{page}] "
        return f"{ref}{snippet}"

    def _format_body(self, clip: Clipping) -> str:
        meta = [
            f"- date: {clip.date_time}",
            f"- author: {clip.author}",
            f"- book: {clip.book_title}",
            f"- page: {clip.page}",
            f"- tags: {', '.join(clip.tags)}" if clip.tags else None
        ]
        footer = "\n".join([m for m in meta if m])
        return f"{clip.content}\n\n\n-----\n{footer}\n-----\n"

# Maintain alias for backward compatibility if needed, though we will refactor usage.
JexExportService = JoplinExporter

import os
import tarfile
import io
from enum import IntEnum
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List

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

class JexExportService:
    """
    Handles the creation of JEX (Joplin Export) files.
    """
    def __init__(self):
        pass

    def create_jex(self, output_filename: str, entites: List[Dict[str, Any]]):
        """
        Writes a list of entity dictionaries to a .jex file using in-memory buffering.
        """
        # Ensure output filename ends with .jex
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
                
                # Add to tar
                tar.addfile(tar_info, file_obj)

    def _create_entity_content(self, entity: Dict[str, Any]) -> str:
        """
        Generates the string content for a Joplin entity file.
        Matches legacy structure:
        Title
        <newline>
        Body
        <newline>
        Properties...
        type_: <type> (Last, no newline)
        """
        parts = []
        
        # 1. Title (Header)
        # Always put title in header if present
        if 'title' in entity:
            parts.append(f"{entity['title']}\n\n")
        
        # 2. Body (Header)
        if 'body' in entity:
            parts.append(f"{entity['body']}\n\n")
            
        # 3. Properties
        # Filter specific keys to ensure order/exclusion
        special_keys = ['title', 'body', 'type_']
        
        for key, value in entity.items():
            if key in special_keys:
                continue
            parts.append(f"{key}: {value}\n")
            
        # 4. Type (Last)
        if 'type_' in entity:
            parts.append(f"type_: {entity['type_']}")
            
        return "".join(parts)

class JoplinEntityBuilder:
    """
    Helper to create dictionaries representing Joplin entities (Notes, Notebooks, Tags).
    """
    
    @staticmethod
    def _now():
        return datetime.now().isoformat(timespec='milliseconds').replace('+00:00', 'Z') # Joplin likes Z or specific format but isoformat usually works

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
            'type_': JoplinEntityType.FOLDER, # Folder
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
            'type_': JoplinEntityType.NOTE, # Note
            'created_time': now,
            'updated_time': now,
            'user_created_time': now,
            'user_updated_time': now,
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
            'author': author,
            'longitude': longitude,
            'altitude': altitude,
            'author': author,
            'source': 'kindle-to-jex',
            'source_application': 'kindle', # Legacy compatibility
            'is_todo': 0,
            'encryption_applied': 0,
            'is_shared': 0,
            'order': 0, # Legacy: strict 0 default
            'markup_language': 1 # Markdown
        }
        return data

    @staticmethod
    def create_tag(title: str) -> Dict[str, Any]:
        now = JoplinEntityBuilder._now()
        data = {
            'id': JoplinEntityBuilder._id(),
            'title': title,
            'type_': JoplinEntityType.TAG, # Tag
            'parent_id': '', # Legacy compat
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
            'type_': JoplinEntityType.NOTE_TAG, # NoteTag
            'created_time': now,
            'updated_time': now,
            'user_created_time': now,
            'user_updated_time': now,
            'encryption_applied': 0
        }
        return data

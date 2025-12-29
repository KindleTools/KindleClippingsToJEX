import os
import tarfile
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List

class JexExportService:
    """
    Handles the creation of JEX (Joplin Export) files.
    """
    def __init__(self):
        pass

    def create_jex(self, output_filename: str, entites: List[Dict[str, Any]]):
        """
        Writes a list of entity dictionaries to a .jex file.
        """
        # Ensure output filename ends with .jex
        if not output_filename.endswith('.jex'):
            output_filename += '.jex'
            
        temp_files = []
        try:
            with tarfile.open(output_filename, "w:") as tar:
                tar.format = tarfile.USTAR_FORMAT
                
                for entity in entites:
                    file_name = f"{entity['id']}.md"
                    self._write_entity_file(file_name, entity)
                    tar.add(file_name)
                    temp_files.append(file_name)
        finally:
            # Cleanup temp files
            for f in temp_files:
                if os.path.exists(f):
                    os.remove(f)

    def _write_entity_file(self, filename: str, entity: Dict[str, Any]):
        """
        Writes a generic Joplin entity to a markdown file.
        """
        with open(filename, 'w', encoding='utf-8') as f:
            # Title
            if 'title' in entity:
                f.write(f"{entity['title']}\n\n")
            
            # Body
            if 'body' in entity:
                f.write(f"{entity['body']}\n\n")
                
            # Properties
            for key, value in entity.items():
                if key in ['title', 'body']:
                    continue
                f.write(f"{key}: {value}\n")

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
            'type_': 2, # Folder
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
            'type_': 1, # Note
            'created_time': now,
            'updated_time': now,
            'user_created_time': now,
            'user_updated_time': now,
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
            'author': author,
            'source': 'kindle-to-jex',
            'is_todo': 0,
            'encryption_applied': 0,
            'is_shared': 0,
            'markup_language': 1 # Markdown
        }
        return data

    @staticmethod
    def create_tag(title: str) -> Dict[str, Any]:
        now = JoplinEntityBuilder._now()
        data = {
            'id': JoplinEntityBuilder._id(),
            'title': title,
            'type_': 5, # Tag
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
            'type_': 6, # NoteTag
            'created_time': now,
            'updated_time': now,
            'user_created_time': now,
            'user_updated_time': now,
            'encryption_applied': 0
        }
        return data

from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import IntEnum
from datetime import datetime

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

@dataclass
class JoplinEntity:
    id: str = ""
    type_: JoplinEntityType = JoplinEntityType.NOTE
    created_time: str = ""
    updated_time: str = ""
    user_created_time: str = ""
    user_updated_time: str = ""
    encryption_applied: int = 0
    is_shared: int = 0

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class JoplinNotebook(JoplinEntity):
    title: str = ""
    parent_id: str = ""
    type_: JoplinEntityType = JoplinEntityType.FOLDER

@dataclass
class JoplinNote(JoplinEntity):
    title: str = ""
    body: str = ""
    parent_id: str = ""
    author: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float = 0.0
    source: str = "kindle-to-jex"
    source_application: str = "kindle"
    is_todo: int = 0
    order: int = 0
    markup_language: int = 1
    type_: JoplinEntityType = JoplinEntityType.NOTE

@dataclass
class JoplinTag(JoplinEntity):
    title: str = ""
    type_: JoplinEntityType = JoplinEntityType.TAG
    parent_id: str = ""

@dataclass
class JoplinTagAssociation(JoplinEntity):
    note_id: str = ""
    tag_id: str = ""
    type_: JoplinEntityType = JoplinEntityType.NOTE_TAG

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class Clipping:
    content: str
    book_title: str
    author: str
    page: str
    location: str
    date_time: datetime
    type: str  # 'highlight' or 'note'
    tags: List[str]

    def __init__(self, content: str, book_title: str, author: str, 
                 date_time: datetime, location: str = "", page: str = "", 
                 type: str = "highlight", tags: List[str] = None):
        self.content = content
        self.book_title = book_title
        self.author = author
        self.date_time = date_time
        self.location = location
        self.page = page
        self.type = type
        self.tags = tags if tags else []

    @property
    def title_hash(self):
        """Helper to identify unique books/authors."""
        return f"{self.book_title}_{self.author}"

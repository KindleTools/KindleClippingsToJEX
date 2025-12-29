from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class Clipping:
    content: str
    book_title: str
    author: str
    date_time: datetime
    location: str = ""
    page: str = ""
    type: str = "highlight" 
    tags: List[str] = field(default_factory=list)

    @property
    def title_hash(self):
        """Helper to identify unique books/authors."""
        return f"{self.book_title}_{self.author}"

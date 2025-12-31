from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Clipping:
    """
    Represents a single highlight or note extracted from the Kindle clippings file.

    Attributes:
        content (str): The actual text highlighted or the note content.
        book_title (str): Title of the book.
        author (str): Author of the book.
        date_time (datetime): When the clipping was created.
        location (str): Kindle location reference (e.g., "100-200").
        page (str): Page number (if available).
        type (str): 'highlight' or 'note'.
        tags (List[str]): List of tags associated with this clipping.
        is_duplicate (bool): Flag indicating if this is a duplicate/redundant entry.
        uid (str): Deterministic unique ID (SHA-256) based on content/metadata (no date).
    """

    content: str
    book_title: str
    author: str
    date_time: datetime
    location: str = ""
    page: str = ""
    entry_type: str = "highlight"
    tags: List[str] = field(default_factory=list)
    is_duplicate: bool = False  # Used for UI flagging
    uid: str = ""  # Deterministic ID

    @property
    def title_hash(self):
        """Helper to identify unique books/authors."""
        return f"{self.book_title}_{self.author}"

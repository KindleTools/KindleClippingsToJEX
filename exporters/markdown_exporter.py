import zipfile
import re
from typing import List, Dict, Any
from datetime import datetime
from domain.models import Clipping
from exporters.base import BaseExporter

class MarkdownExporter(BaseExporter):
    """
    Handles the export of clippings to a ZIP file containing Markdown files with Yaml frontmatter.
    Standard format for Obsidian and other PKM tools.
    """
    
    def export(self, clippings: List[Clipping], output_file: str, context: Dict[str, Any] = None):
        """
        Writes a list of Clipping objects to a ZIP file containing .md files organized by folders.
        Structure: Author/Book/Note.md
        """
        # Ensure output filename ends with .zip
        if not output_file.lower().endswith('.zip'):
            output_file += '.zip'
            
        try:
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for clipping in clippings:
                    # Clean paths
                    author_folder = self._sanitize_filename(clipping.author)
                    book_folder = self._sanitize_filename(clipping.book_title)
                    filename = self._generate_filename(clipping)
                    
                    # Construct full path inside ZIP
                    full_path = f"{author_folder}/{book_folder}/{filename}"
                    
                    content = self._generate_markdown_content(clipping)
                    zipf.writestr(full_path, content)
                    
        except Exception as e:
            raise IOError(f"Failed to create Markdown/ZIP archive: {e}")

    # Alias for legacy compatibility
    def export_clippings(self, clippings: List[Clipping], output_file: str, context: Dict[str, Any] = None):
        self.export(clippings, output_file, context)

    def _generate_filename(self, clipping: Clipping) -> str:
        """
        Generates a sanitized, unique filename for the note.
        """
        date_str = clipping.date_time.strftime("%Y%m%d%H%M%S") if clipping.date_time else "000000"
        
        prefix = "Note"
        if clipping.page:
             prefix = f"Page {clipping.page}"
        elif clipping.location:
             prefix = f"Loc {clipping.location}"
             
        content_hash = hash(clipping.content) % 10000
        
        sanitized_prefix = self._sanitize_filename(prefix)
        return f"{sanitized_prefix} - {date_str}_{content_hash:04d}.md"

    def _sanitize_filename(self, text: str) -> str:
        """Removes illegal characters for filenames."""
        return re.sub(r'[\\/*?:"<>|]', "", text).strip()

    def _generate_markdown_content(self, clipping: Clipping) -> str:
        """
        Generates the Markdown string with clean YAML Frontmatter.
        """
        # Escape quotes in YAML strings to prevent breaking the format
        author = clipping.author.replace('"', '\\"')
        title = clipping.book_title.replace('"', '\\"')
        page_val = clipping.page if clipping.page else ""
        date_iso = clipping.date_time.isoformat() if clipping.date_time else ""
        
        # Format tags as a YAML list: [tag1, tag2]
        tags_list = f"[{', '.join(clipping.tags)}]" if clipping.tags else "[]"
        
        yaml_block = f"""---
book: "{title}"
author: "{author}"
category: "{clipping.type}"
date: {date_iso}
page: "{page_val}"
tags: {tags_list}
source: "kindle"
---"""
        
        return f"{yaml_block}\n\n{clipping.content}\n"

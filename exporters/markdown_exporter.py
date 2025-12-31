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
    
    def create_clipboard_markdown(self, clippings: List[Clipping]) -> str:
        """
        Generates a simplified Markdown string for clipboard copy/paste.
        Format: > Content (Citation)
        """
        output = []
        for clip in clippings:
             # Citation format: — *Title* by **Author** (Page X / Loc Y)
            meta = []
            if clip.page: meta.append(f"p. {clip.page}")
            if clip.location: meta.append(f"loc. {clip.location}")
            meta_str = f" ({', '.join(meta)})" if meta else ""
            
            md = f"> {clip.content}\n\n— *{clip.book_title}* by **{clip.author}**{meta_str}"
            if clip.tags:
                md += f" #{' #'.join(clip.tags)}"
            output.append(md)
        
        return "\n\n---\n\n".join(output)

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
                    if clipping.is_duplicate:
                        continue

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
        """
        Sanitizes text to be a valid filename, especially for Windows.
        1. Removes illegal characters: < > : " / \ | ? *
        2. Stripes leading/trailing whitespace and dots.
        3. Truncates to 64 characters to prevent MAX_PATH issues.
        """
        # Remove illegal chars
        clean = re.sub(r'[\\/*?:"<>|]', "", text)
        # Remove control characters
        clean = "".join(c for c in clean if c.isprintable())
        # Strip dots and spaces from ends (Windows doesn't like folders ending in .)
        clean = clean.strip(". ")
        # Truncate to reasonable length (Windows path limit is 260 total)
        return clean[:64].strip()

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
date: {date_iso}
page: "{page_val}"
tags: {tags_list}
source: "kindle"
generator: "KindleClippingsToJEX v0.2.0"
---"""
        
        return f"{yaml_block}\n\n{clipping.content}\n"

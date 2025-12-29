from typing import Dict, List, Tuple
import logging
from src.domain.models import Clipping
from src.parsers.kindle_parser import KindleClippingsParser
from src.exporters.joplin_exporter import JexExportService, JoplinEntityBuilder

logger = logging.getLogger("KindleToJex.Service")

class ClippingsService:
    def __init__(self, language_code="es"):
        self.parser = KindleClippingsParser(language_code=language_code)
        self.exporter = JexExportService()
        self.builder = JoplinEntityBuilder()
        
        self.authors_cache: Dict[str, str] = {}
        self.books_cache: Dict[str, str] = {}
        self.tags_cache: Dict[str, str] = {}
        
        self.entities_to_export: List[Dict] = []

    def process_clippings(self, input_file: str, output_file: str, 
                         root_notebook_name: str, 
                         location: Tuple[float, float, int], 
                         creator_name: str):
        
        clippings = self.parser.parse_file(input_file)
        if not clippings:
            logger.warning("No clippings found to process.")
            return

        self._process_list(clippings, output_file, root_notebook_name, location, creator_name)

    def process_clippings_from_list(self, clippings: List[Clipping], output_file: str, 
                                   root_notebook_name: str, 
                                   location: Tuple[float, float, int], 
                                   creator_name: str):
         self._process_list(clippings, output_file, root_notebook_name, location, creator_name)

    def _process_list(self, clippings: List[Clipping], output_file: str, 
                      root_notebook_name: str, 
                      location: Tuple[float, float, int], 
                      creator_name: str):

        logger.info(f"Processing {len(clippings)} clippings for export...")

        # Create Root Notebook
        root_nb = self.builder.create_notebook(root_notebook_name)
        self.entities_to_export.append(root_nb)
        root_id = root_nb['id']

        for clip in clippings:
            self._process_single_clipping(clip, root_id, location, creator_name)

        logger.info(f"Exporting {len(self.entities_to_export)} items to {output_file}...")
        self.exporter.create_jex(output_file, self.entities_to_export)
        logger.info("Export completed.")

    def _process_single_clipping(self, clip: Clipping, root_id: str, 
                                location: Tuple[float, float, int], creator: str):
        
        author_name = clip.author
        if author_name not in self.authors_cache:
            author_nb = self.builder.create_notebook(author_name, parent_id=root_id)
            self.entities_to_export.append(author_nb)
            self.authors_cache[author_name] = author_nb['id']
        author_id = self.authors_cache[author_name]

        book_title = clip.book_title
        book_cache_key = f"{author_name}__{book_title}"
        
        if book_cache_key not in self.books_cache:
            book_nb = self.builder.create_notebook(book_title, parent_id=author_id)
            self.entities_to_export.append(book_nb)
            self.books_cache[book_cache_key] = book_nb['id']
        book_id = self.books_cache[book_cache_key]

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
        
        for tag_str in clip.tags:
            if tag_str not in self.tags_cache:
                tag_obj = self.builder.create_tag(tag_str)
                self.entities_to_export.append(tag_obj)
                self.tags_cache[tag_str] = tag_obj['id']
            
            tag_id = self.tags_cache[tag_str]
            assoc = self.builder.create_tag_association(tag_id=tag_id, note_id=note['id'])
            self.entities_to_export.append(assoc)

    def _format_title(self, text: str, page: str) -> str:
        snippet = text[:50].replace('\n', ' ')
        ref = ''
        if page and page.replace('-', '').isnumeric() and len(page) < 7:
             try:
                 p_val = int(page.split('-')[0]) 
                 ref = f"[{p_val}] " 
             except:
                 ref = f"[{page}] "
        
        return f"{ref}{snippet}"

    def _format_body(self, clip: Clipping) -> str:
        meta = [
            f"- date: {clip.date_time}",
            f"- author: {clip.author}",
            f"- book: {clip.book_title}",
            f"- page: {clip.page}",
            f"- location: {clip.location}",
            f"- tags: {', '.join(clip.tags)}" if clip.tags else None
        ]
        footer = "\n".join([m for m in meta if m])
        return f"{clip.content}\n\n\n-----\n{footer}\n-----\n"

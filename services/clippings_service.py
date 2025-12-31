from typing import Dict, List, Tuple
import logging
from domain.models import Clipping
from parsers.kindle_parser import KindleClippingsParser
from exporters.base import BaseExporter
from exporters.joplin_exporter import JoplinExporter
from exporters.csv_exporter import CsvExporter
from exporters.csv_exporter import CsvExporter
from exporters.markdown_exporter import MarkdownExporter
from exporters.json_exporter import JsonExporter

logger = logging.getLogger("KindleToJex.Service")

class ClippingsService:
    def __init__(self, language_code="es"):
        self.parser = KindleClippingsParser(language_code=language_code)
        
        # Strategy Registry
        self.exporters: Dict[str, BaseExporter] = {
            'jex': JoplinExporter(),
            'csv': CsvExporter(),
            'md': MarkdownExporter(),
            'json': JsonExporter()
        }

    def process_clippings(self, input_file: str, output_file: str, 
                         root_notebook_name: str, 
                         location: Tuple[float, float, int], 
                         creator_name: str,
                         enable_deduplication: bool = True,
                         export_format: str = 'jex'):
        
        clippings = self.parser.parse_file(input_file)
        if not clippings:
            logger.warning("No clippings found to process.")
            return

        final_clippings = clippings

        if enable_deduplication:
            from services.deduplication_service import SmartDeduplicator
            deduplicator = SmartDeduplicator()
            final_clippings = deduplicator.deduplicate(clippings)
        
        self.process_clippings_from_list(final_clippings, output_file, 
                                        root_notebook_name, location, creator_name, export_format)

    def process_clippings_from_list(self, clippings: List[Clipping], output_file: str, 
                                   root_notebook_name: str, 
                                   location: Tuple[float, float, int], 
                                   creator_name: str,
                                   export_format: str = 'jex'):
         
        logger.info(f"Processing {len(clippings)} clippings for {export_format.upper()} export...")

        exporter = self._get_exporter(export_format)
        
        # Prepare Context
        context = {
            'root_notebook': root_notebook_name,
            'location': location,
            'creator': creator_name
        }

        try:
            exporter.export(clippings, output_file, context)
            logger.info("Export completed successfully.")
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            raise e

    def _get_exporter(self, format_code: str) -> BaseExporter:
        """Factory method to get the correct strategy."""
        code = format_code.lower()
        if code not in self.exporters:
            logger.warning(f"Unknown format '{format_code}', defaulting to 'jex'")
            return self.exporters['jex']
        return self.exporters[code]

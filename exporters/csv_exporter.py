import csv
import logging
from typing import List, Dict, Any
from domain.models import Clipping
from exporters.base import BaseExporter

logger = logging.getLogger("KindleToJex.CsvExporter")

class CsvExporter(BaseExporter):
    """
    Handles the export of clippings to CSV format.
    """
    
    def create_csv_string(self, clippings: List[Clipping]) -> str:
        """
        Generates the CSV string content for a list of clippings.
        Useful for clipboard operations or in-memory processing.
        """
        import io
        output = io.StringIO()
        fieldnames = ['book_title', 'author', 'content', 'type', 'date_time', 'page', 'location', 'tags', 'is_duplicate', 'source']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        # Manually write header to avoid potential issues with DictWriter in older pythons (though 3.8+ is fine)
        writer.writeheader()
        
        for clipping in clippings:
            writer.writerow({
                'book_title': clipping.book_title,
                'author': clipping.author,
                'content': clipping.content,
                'type': clipping.type,
                'date_time': clipping.date_time.isoformat() if clipping.date_time else '',
                'page': clipping.page,
                'location': clipping.location,
                'tags': ', '.join(clipping.tags),
                'is_duplicate': clipping.is_duplicate,
                'source': 'kindle'
            })
        
        return output.getvalue()

    def export(self, clippings: List[Clipping], output_file: str, context: Dict[str, Any] = None):
        """
        Writes a list of Clipping objects to a CSV file.
        Context is accepted but ignored for CSV.
        """
        # Ensure output filename ends with .csv
        if not output_file.lower().endswith('.csv'):
            output_file += '.csv'
            
        csv_content = self.create_csv_string(clippings)
        
        logger.info(f"Exporting {len(clippings)} clippings to CSV: {output_file}")
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                f.write(csv_content)
        except Exception as e:
            raise IOError(f"Failed to write CSV file: {e}")

    # Alias for backward compatibility during transitions, can be deprecated later
    def export_clippings(self, clippings: List[Clipping], output_file: str):
         self.export(clippings, output_file)

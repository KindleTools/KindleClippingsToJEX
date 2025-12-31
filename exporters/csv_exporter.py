import csv
from typing import List
from domain.models import Clipping

class CsvExporter:
    """
    Handles the export of clippings to CSV format.
    """
    
    def export_clippings(self, clippings: List[Clipping], output_file: str):
        """
        Writes a list of Clipping objects to a CSV file.
        """
        # Ensure output filename ends with .csv
        if not output_file.lower().endswith('.csv'):
            output_file += '.csv'
            
        fieldnames = ['book_title', 'author', 'content', 'type', 'date_time', 'page', 'location', 'tags']
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
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
                        'tags': ', '.join(clipping.tags)
                    })
        except Exception as e:
            raise IOError(f"Failed to write CSV file: {e}")

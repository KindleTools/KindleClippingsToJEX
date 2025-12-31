import json
import logging
from typing import List, Dict, Any, Optional
from domain.models import Clipping
from exporters.base import BaseExporter

logger = logging.getLogger("KindleToJex.JsonExporter")


class JsonExporter(BaseExporter):
    """
    Handles the export of clippings to a raw JSON file.
    Ideal for backups or developers who want to process the data programmatically.
    """

    def create_json_string(
        self, clippings: List[Clipping], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generates the JSON string for a list of clippings.
        """
        context = context or {}

        # Convert Clipping objects to dictionaries
        data_list = []
        for clip in clippings:
            item = {
                "book_title": clip.book_title,
                "author": clip.author,
                "content": clip.content,
                "type": clip.entry_type,
                "date_time": clip.date_time.isoformat() if clip.date_time else None,
                "page": clip.page,
                "location": clip.location,
                "tags": list(clip.tags),
                # Include raw boolean indicating if it was flagged as dupe
                "is_duplicate": clip.is_duplicate,
                "source": "kindle",
            }
            data_list.append(item)

        export_data = {
            "meta": {
                "count": len(data_list),
                "generated_at": context.get("generated_at", None),
                "creator": context.get("creator", "System"),
                "source": "KindleClippingsToJEX",
            },
            "clippings": data_list,
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)

    def export(
        self, clippings: List[Clipping], output_file: str, context: Optional[Dict[str, Any]] = None
    ):
        """
        Writes a list of Clipping objects to a JSON file.
        """
        # Ensure output filename ends with .json
        if not output_file.lower().endswith(".json"):
            output_file += ".json"

        json_content = self.create_json_string(clippings, context)

        logger.info(f"Exporting {len(clippings)} clippings to {output_file}...")

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_content)
        except Exception as e:
            raise IOError(f"Failed to write JSON file: {e}")

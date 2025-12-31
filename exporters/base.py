from abc import ABC, abstractmethod
from typing import List, Dict, Any
from domain.models import Clipping

class BaseExporter(ABC):
    """
    Abstract Base Class for all exporters.
    Enforces a consistent interface for the Strategy Pattern.
    """
    
    @abstractmethod
    def export(self, clippings: List[Clipping], output_file: str, context: Dict[str, Any] = None):
        """
        Exports the given clippings to the specified output file.
        
        Args:
            clippings: List of Clipping objects to export.
            output_file: Path to the destination file.
            context: Dictionary containing additional metadata (e.g., 'creator', 'location', 'root_notebook').
        """
        pass

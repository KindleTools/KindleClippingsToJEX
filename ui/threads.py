from PyQt5.QtCore import QThread, pyqtSignal
from typing import List, Tuple
from domain.models import Clipping
from parsers.kindle_parser import KindleClippingsParser
from services.clippings_service import ClippingsService
import logging

class LoadFileThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, file_path: str, language: str):
        super().__init__()
        self.file_path = file_path
        self.language = language

    def run(self):
        try:
            parser = KindleClippingsParser(language_code=self.language)
            clippings = parser.parse_file(self.file_path)
            self.finished.emit(clippings)
        except Exception as e:
            logging.error(f"Error loading file: {e}", exc_info=True)
            self.error.emit(str(e))

class ExportThread(QThread):
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, service: ClippingsService, clippings: List[Clipping], 
                 output_file: str, root_notebook: str, 
                 location: Tuple[float, float, int], creator: str):
        super().__init__()
        self.service = service
        self.clippings = clippings
        self.output_file = output_file
        self.root_notebook = root_notebook
        self.location = location
        self.creator = creator

    def run(self):
        try:
            self.service.process_clippings_from_list(
                clippings=self.clippings,
                output_file=self.output_file,
                root_notebook_name=self.root_notebook,
                location=self.location,
                creator_name=self.creator
            )
            self.finished.emit(len(self.clippings))
        except Exception as e:
            logging.error(f"Error exporting file: {e}", exc_info=True)
            self.error.emit(str(e))

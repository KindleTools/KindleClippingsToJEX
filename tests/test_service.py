import unittest
from unittest.mock import MagicMock
from datetime import datetime
from services.clippings_service import ClippingsService
from domain.models import Clipping

class TestClippingsService(unittest.TestCase):
    def setUp(self):
        self.service = ClippingsService()
        
        # Mock Strategies
        self.mock_jex = MagicMock()
        self.mock_csv = MagicMock()
        self.mock_md = MagicMock()
        
        self.service.exporters['jex'] = self.mock_jex
        self.service.exporters['csv'] = self.mock_csv
        self.service.exporters['md'] = self.mock_md

    def test_process_jex_format_strategy(self):
        clippings = [MagicMock(spec=Clipping)]
        
        self.service.process_clippings_from_list(
            clippings=clippings,
            output_file="out.jex",
            root_notebook_name="Root",
            location=(0,0,0),
            creator_name="Me",
            export_format='jex'
        )
        
        # Verify JEX strategy called
        self.mock_jex.export.assert_called_once()
        self.mock_csv.export.assert_not_called()
        self.mock_md.export.assert_not_called()
        
        # Verify Context passing
        _, _, context = self.mock_jex.export.call_args[0]
        self.assertEqual(context['creator'], "Me")
        self.assertEqual(context['root_notebook'], "Root")

    def test_process_csv_format_strategy(self):
        clippings = [MagicMock(spec=Clipping)]
        
        self.service.process_clippings_from_list(
            clippings, "out.csv", "Root", (0,0,0), "Me", export_format='csv'
        )
        
        self.mock_csv.export.assert_called_once()
        self.mock_jex.export.assert_not_called()

    def test_process_md_format_strategy(self):
        clippings = [MagicMock(spec=Clipping)]
        
        self.service.process_clippings_from_list(
            clippings, "out.zip", "Root", (0,0,0), "Me", export_format='md'
        )
        
        self.mock_md.export.assert_called_once()

    def test_default_strategy_fallback(self):
        """Should default to JEX if format unknown"""
        clippings = [MagicMock(spec=Clipping)]
        
        self.service.process_clippings_from_list(
            clippings, "out.stuff", "Root", (0,0,0), "Me", export_format='unknown_format'
        )
        
        self.mock_jex.export.assert_called_once()

if __name__ == '__main__':
    unittest.main()

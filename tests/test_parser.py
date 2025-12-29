import unittest
import os
import sys

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parsers.kindle_parser import KindleClippingsParser
from src.domain.models import Clipping

class TestKindleClippingsParser(unittest.TestCase):
    def setUp(self):
        # Sample clipping content
        self.sample_content = """El Quijote (Cervantes, Miguel de)
- La subrayado en la página 12 | posición 100-120 | Añadid. el sábado 24 de agosto de 2018 10:00:00

En un lugar de la mancha...
==========
"""
        self.parser = KindleClippingsParser(language_code="es")
        
        # Write temporary sample file
        with open("test_sample.txt", "w", encoding="utf-8") as f:
            f.write(self.sample_content)

    def tearDown(self):
        if os.path.exists("test_sample.txt"):
            os.remove("test_sample.txt")

    def test_parse_single_highlight(self):
        clippings = self.parser.parse_file("test_sample.txt", encoding="utf-8")
        
        self.assertEqual(len(clippings), 1)
        clip = clippings[0]
        
        self.assertEqual(clip.book_title, "El Quijote")
        self.assertEqual(clip.author, "Cervantes, Miguel de")
        self.assertEqual(clip.type, "highlight")
        self.assertEqual(clip.page, "12")
        self.assertEqual(clip.content.strip(), "En un lugar de la mancha...")
        self.assertEqual(clip.date_time.year, 2018)

if __name__ == '__main__':
    unittest.main()

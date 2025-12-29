import unittest
import os
import tempfile
from parsers.kindle_parser import KindleClippingsParser

class TestKindleClippingsParser(unittest.TestCase):
    def setUp(self):
        # Sample clipping content
        self.sample_content = """El Quijote (Cervantes, Miguel de)
- La subrayado en la página 12 | posición 100-120 | Añadid. el sábado 24 de agosto de 2018 10:00:00

En un lugar de la mancha...
==========
"""
        self.parser = KindleClippingsParser(language_code="es")
        
        # Create a temporary file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8')
        self.temp_file.write(self.sample_content)
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_parse_single_highlight(self):
        clippings = self.parser.parse_file(self.temp_file.name, encoding="utf-8")
        
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

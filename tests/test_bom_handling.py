import unittest
import os
import tempfile
from parsers.kindle_parser import KindleClippingsParser
from utils.title_cleaner import TitleCleaner

class TestBOMHandling(unittest.TestCase):
    def setUp(self):
        self.parser = KindleClippingsParser(language_code="es")
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_title_cleaner_removes_bom(self):
        # Direct test of TitleCleaner
        dirty_title = "\ufeffLa libertad cristiana"
        clean = TitleCleaner.clean_title(dirty_title)
        self.assertEqual(clean, "La libertad cristiana")

    def test_title_cleaner_removes_zero_width_space(self):
        dirty_title = "\u200bLa libertad cristiana"
        clean = TitleCleaner.clean_title(dirty_title)
        self.assertEqual(clean, "La libertad cristiana")

    def test_parser_with_mid_file_bom(self):
        # Scenario where BOM appears in the middle of the file (e.g. concatenated files)
        # Clipping 1: Normal
        clip1 = """Libro Uno (Autor A)
- La subrayado en la página 1 | posición 10-20 | Añadido el 1 de enero de 2024

Contenido 1
"""
        # Clipping 2: Starts with BOM (simulating file concatenation)
        clip2 = """\ufeffLibro Uno (Autor A)
- La nota en la página 1 | posición 15 | Añadido el 1 de enero de 2024

Tag1
"""
        content = clip1 + "==========" + "\n" + clip2 + "=========="
        
        # Write to file
        with open(self.temp_file.name, "w", encoding="utf-8") as f:
            f.write(content)

        clippings = self.parser.parse_file(self.temp_file.name, encoding="utf-8")
        
        self.assertEqual(len(clippings), 1)
        clip = clippings[0]
        
        # Verify tag linking works because titles match
        self.assertEqual(clip.book_title, "Libro Uno")
        self.assertIn("Tag1", clip.tags)

    def test_global_sanitation(self):
        # Test that BOMs are removed from ANYWHERE in the content, including author and body
        # Use Spanish patterns since parser defaults to 'es'
        content = """\ufeffTitle (Author\ufeffName)
- La subrayado en la página 1 | posición 10 | Añadid. el 1 de enero de 2024

Body\ufeffText
==========
"""
        with open(self.temp_file.name, "w", encoding="utf-8") as f:
            f.write(content)

        clippings = self.parser.parse_file(self.temp_file.name, encoding="utf-8")
        clip = clippings[0]
        
        self.assertEqual(clip.book_title, "Title")
        self.assertEqual(clip.author, "AuthorName") # BOM removed
        self.assertEqual(clip.content.strip(), "BodyText") # BOM removed

if __name__ == "__main__":
    unittest.main()

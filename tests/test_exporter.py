import unittest
from datetime import datetime
from exporters.joplin_exporter import JoplinEntityBuilder, JoplinEntityType

class TestJoplinEntityBuilder(unittest.TestCase):
    def test_create_notebook(self):
        notebook = JoplinEntityBuilder.create_notebook("My Notebook")
        self.assertEqual(notebook.title, "My Notebook")
        self.assertEqual(notebook.type_, JoplinEntityType.FOLDER)
        self.assertTrue(notebook.id)
        self.assertTrue(notebook.created_time)

    def test_create_note(self):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        note = JoplinEntityBuilder.create_note(
            title="My Note", 
            body="# Content", 
            parent_id="notebook_id",
            created_time=dt,
            author="Me"
        )
        
        self.assertEqual(note.title, "My Note")
        self.assertEqual(note.body, "# Content")
        self.assertEqual(note.parent_id, "notebook_id")
        self.assertEqual(note.type_, JoplinEntityType.NOTE)
        self.assertEqual(note.author, "Me")
        # Check date formatting if critical, or just presence
        self.assertTrue(note.created_time.startswith("2023-01-01T12:00:00"))

    def test_create_tag(self):
        tag = JoplinEntityBuilder.create_tag("important")
        self.assertEqual(tag.title, "important")
        self.assertEqual(tag.type_, JoplinEntityType.TAG)
        
    def test_create_tag_association(self):
        assoc = JoplinEntityBuilder.create_tag_association("tag1", "note1")
        self.assertEqual(assoc.tag_id, "tag1")
        self.assertEqual(assoc.note_id, "note1")
        self.assertEqual(assoc.type_, JoplinEntityType.NOTE_TAG)

if __name__ == '__main__':
    unittest.main()

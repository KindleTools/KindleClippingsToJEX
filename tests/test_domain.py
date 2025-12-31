import unittest
from datetime import datetime
from domain.models import Clipping

class TestClippingModel(unittest.TestCase):
    def test_clipping_creation(self):
        now = datetime.now()
        clip = Clipping(
            book_title="Test Book",
            author="Test Author",
            content="Test content",
            entry_type="highlight",
            date_time=now,
            page="10",
            location="100-120"
        )
        
        self.assertEqual(clip.book_title, "Test Book")
        self.assertEqual(clip.author, "Test Author")
        self.assertEqual(clip.content, "Test content")
        self.assertEqual(clip.entry_type, "highlight")
        self.assertEqual(clip.date_time, now)
        self.assertEqual(clip.page, "10")
        self.assertEqual(clip.location, "100-120")

    def test_clipping_defaults(self):
        # Assuming we might want to test default values if any, 
        # but currently the dataclass/model requires fields.
        # This is a placeholder for future logic if models get methods.
        pass

if __name__ == '__main__':
    unittest.main()

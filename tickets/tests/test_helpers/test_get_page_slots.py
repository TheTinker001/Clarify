from datetime import timedelta

from django.test import TestCase
from tickets.helpers import get_page_slots


class GetPageSlotsTests(TestCase):
    """Tests for the helper function 'get_page_slots'"""

    def test_pages_less_than_9(self):
        self.assertEqual(get_page_slots(1, 5), [1, 2, 3, 4, 5])

    def test_first_page(self):
        self.assertEqual(get_page_slots(2, 15), [1, 2, 3, 4, 5, 6, 7, "...", 15])

    def test_last_page(self):
        self.assertEqual(get_page_slots(19, 20), [1, "...", 14, 15, 16, 17, 18, 19, 20])

    def test_middle_page(self):
        self.assertEqual(
            get_page_slots(10, 20), [1, "...", 8, 9, 10, 11, 12, "...", 20]
        )

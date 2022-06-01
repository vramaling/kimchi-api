"""
Demo tests
"""

from django.test import SimpleTestCase

from app import calc

class CalcTest(SimpleTestCase):

    def test_add_numbners(self):
        result = calc.add(4,6)

        self.assertEqual(result,10)
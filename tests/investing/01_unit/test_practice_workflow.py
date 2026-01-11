from django.test import TestCase


def add(a, b):
    return a + b


class PracticeWorkflowTests(TestCase):
    def test_add_numbers(self):
        self.assertEqual(add(2, 3), 5)

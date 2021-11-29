from capstone_project.models import User
from django.test import TestCase


class TestModels(TestCase):

    def setUp(self) -> None:
        self.maybe_type1 = '0'
        self.maybe_type2 = ''
        self.maybe_type3 = '5'

    def test_from_str(self):
        response = User.from_int(int(self.maybe_type1))
        self.assertEqual(User.UserType.Supervisor, response, msg='Expected Supervisor type returned.')

    def test_from_str_non_type(self):
        with self.assertRaises(TypeError):
            User.from_int(int(self.maybe_type3))

    def test_from_str_with_empty_maybe_type(self):
        with self.assertRaises(TypeError):
            User.from_int(int(self.maybe_type2))

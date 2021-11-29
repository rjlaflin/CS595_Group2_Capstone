from django.shortcuts import reverse
from django.test import TestCase, Client
from django.http import HttpRequest, HttpResponse
from django.db.models import ObjectDoesNotExist

from capstone_project.models import User
from capstone_project.viewsupport.errors import UserEditPlace, UserEditError
from capstone_project.AcceptanceTests.acceptance_tests_base import AcceptanceTestCase
from capstone_project.viewsupport.message import MessageQueue, Message


class TestCreateUserView(AcceptanceTestCase[UserEditError]):
    def setUp(self):
        self.client = Client()
        self.session = self.client.session

        # Only Supervisors may create new users, so we need the
        # session to have one for most tests

        self.supervisor_username = 'chriswojta'
        self.Supervisor = User.objects.create(
            unique_id=self.supervisor_username,
            pwd='a-great-password',
            user_type=User.UserType.Supervisor,
            # pwd_tmp=False
        )

        self.Staff_username = 'arodgers'
        self.Staff = User.objects.create(
            unique_id=self.Staff_username,
            pwd='a-great-password',
            user_type=User.UserType.Staff,
            # pwd_tmp=False
        )

        self.session['user_id'] = self.Supervisor.id
        self.session.save()

        self.good_password = 'a-great-password'

        self.url = reverse('users-create')

    def test_rejects_empty_password(self):
        resp = self.client.post(self.url, {
            'login_id': 'cmwojta',
            # 'new_password': '',
            'user_type': '2',

        }, follow=False)

        self.assertIsNotNone(resp, 'Did not return a response')

        error = self.assertContextError(resp)

        self.assertTrue(error.place() is UserEditPlace.PASSWORD)
        self.assertEqual('Password must be at least 8 characters in length', error.message())

    def test_rejects_short_password(self):
        resp = self.client.post(self.url, {
            'unique_id': 'cmwojta',
            'new_password': '1234567',  # Short password
            'user_type': '2',

        }, follow=False)

        self.assertIsNotNone(resp, 'Did not return a response')

        error = self.assertContextError(resp)  # Asserts that an error exists as well

        self.assertTrue(error.place() is UserEditPlace.PASSWORD)
        self.assertEqual('Password must be at least 8 characters in length', error.message())

    def test_rejects_empty_username(self):
        resp = self.client.post(self.url, {
            # 'unique_id': '',
            'new_password': self.good_password,  # Short password
            'user_type': '2',

        }, follow=False)

        self.assertIsNotNone(resp, 'Did not return a response')

        error = self.assertContextError(resp)  # Asserts that an error exists as well

        self.assertTrue(error.place() is UserEditPlace.USERNAME)
        self.assertEqual('You must provide a login id', error.message())

    def test_rejects_long_username(self):
        resp = self.client.post(self.url, {
            'unique_id': 'a-very-long-username-that-would-never-fit-in-the-database',
            'new_password': self.good_password,
            'user_type': '2',

        }, follow=False)

        self.assertIsNotNone(resp, 'Did not return a response')

        error = self.assertContextError(resp)  # Asserts that an error exists as well

        self.assertTrue(error.place() is UserEditPlace.USERNAME, 'Did not recognize missing username')
        self.assertEqual('A login id may not be longer than 20 characters', error.message())

    def test_rejects_username_with_spaces(self):
        resp = self.client.post(self.url, {
            'unique_id': 'chris wojta',
            'new_password': self.good_password,
            'user_type': '2',

        }, follow=False)

        self.assertIsNotNone(resp, 'Did not return a response')

        error = self.assertContextError(resp)  # Asserts that an error exists as well

        self.assertTrue(error.place() is UserEditPlace.USERNAME, 'Did not recognize missing username')
        self.assertEqual('A username may not have spaces', error.message())

    def test_rejects_non_supervisor(self):
        self.session['user_id'] = self.Staff.id
        self.session.save()

        resp = self.client.post(self.url, {
            'login_id': 'arodgers',
            'new_password': self.good_password,
            'user_type': '2',

        }, follow=False)

        self.assertContainsMessage(resp, Message(
            'You do not have permission to create users',
            Message.Type.ERROR,
        ))

        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get(unique_id='arodgers')

        self.assertRedirects(resp, reverse('users-directory'))

from django.test import Client, TestCase
from capstone_project.models import User
from django.urls import reverse
from capstone_project.viewsupport.errors import PageError, LoginError


class TestLoginView(TestCase):

    def setUp(self):
        self.client = Client()
        self.check_pass = 'password1'

        self.long_user_username = 'cmwojta'
        long_user = User.objects.create(
            user_type=User.UserType.Supervisor,
            unique_id=self.long_user_username,
            pwd=self.check_pass,
            name="chris wojta",
            # pwd_tmp=False
        )

        self.long_user = long_user.id

        self.short_user_username = 'chriswojta'
        self.short_user = User.objects.create(
            user_type=User.UserType.Staff,
            unique_id=self.short_user_username,
            pwd=self.check_pass,
        )

    def test_rejects_empty_username(self):
        resp = self.client.post(reverse('login'), {
            'unique_id': '',
            'pwd': 'verysecurepassword'
        })

        error: LoginError = resp.context['error']

        self.assertIsNotNone(error, 'Did not return error message')
        self.assertTrue(error.place().username(), 'Did not return error with username')
        self.assertEqual(error.message(), 'You must provide a username')

    def test_rejects_long_username(self):
        # Usernames may not be longer than 20 characters,
        # does not even ask the database

        resp = self.client.post(reverse('login'), {
            'unique_id': 'very_long_username_username_that_the_database_cannot_hold',
            'pwd': 'verysecurepassword',
        })

        error: LoginError = resp.context['error']

        self.assertIsNotNone(error, 'Did not return error for too long username')
        self.assertTrue(error.place().username(), 'Did not return error for username')
        self.assertEqual(error.message(), 'That Username is too Long')

    def test_rejects_no_such_username(self):
        # Username does not exist in the database
        resp = self.client.post(reverse('login'), {
            'unique_id': 'arodgers12',
            'pwd': 'password1',
        })

        error = resp.context['error']

        self.assertIsNotNone(error, 'Did not return error for nonexistent user')
        self.assertTrue(error.place().username(), 'Did not return error for non-existence username.')
        self.assertEqual(error.message(), 'No such user')

    def test_rejects_empty_password(self):
        resp = self.client.post(reverse('login'), {
            'unique_id': self.long_user_username,
            'pwd': ''
        })

        error: LoginError = resp.context['error']

        self.assertIsNotNone(error, 'Did not return error message')
        self.assertTrue(error.place().password(), 'Did not return error with password')
        self.assertEqual(error.message(), 'You must provide a password')

    def test_rejects_short_password(self):
        # Passwords of less than or equal to 8 passwords are not valid
        resp = self.client.post(reverse('login'), {
            'unique_id': self.long_user_username,
            'pwd': '1234'
        })

        error: LoginError = resp.context['error']

        self.assertIsNotNone(error, 'Did not return error message')
        self.assertTrue(error.place().password(), 'Did not return error with password')
        self.assertEqual(error.message(), 'A password must be at least 8 characters in length')

    def test_rejects_mismatched_password(self):
        # Username and password do not match
        resp = self.client.post(reverse('login'), {
            'unique_id': self.long_user_username,
            'pwd': '1234567890'
        })

        error: LoginError = resp.context['error']

        self.assertIsNotNone(error, 'Did not return error message')
        self.assertTrue(error.place().password(), 'Did not return error with password')
        self.assertEqual(error.message(), 'Incorrect Password')

    def test_successful_login_sets_session(self):
        # Successful login sets the session with the users' primary key (user_id)
        # from the database
        resp = self.client.post(reverse('login'), {
            'unique_id': self.long_user_username,
            'pwd': self.check_pass,
        })

        try:
            user_id = self.client.session['user_id']
        except KeyError:
            self.assertTrue(False, 'Did not set user_id on successful login')
            return  # Only here to assure that the previous assertion always fails

        self.assertIsNotNone(user_id, 'Did not set user_id on login')
        self.assertEqual(user_id, self.long_user, 'Did not set correct key with valid login')

    def test_successful_login_sends_redirect(self):
        # Successful login redirects the user to their homepage
        resp = self.client.post(reverse('login'), {
            'unique_id': self.long_user_username,
            'pwd': self.check_pass,
        }, follow=True)

        redirects = resp.redirect_chain

        self.assertEqual(len(redirects), 1, 'Redirected too many times')
        self.assertEqual(redirects[0][0], reverse('info'), 'Did not redirect returning user to homepage')

    def test_first_login_sends_redirect(self):
        # Successful login, when a user has not logged in before,
        # redirects them to the password change form
        resp = self.client.post(reverse('login'), {
            'username': self.short_user_username,
            'password': self.check_pass,
        }, follow=False)

        self.assertRedirects(resp, reverse('users-edit', args=[self.short_user.id]))

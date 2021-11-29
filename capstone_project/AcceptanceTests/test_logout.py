from django.test import Client, TestCase
from capstone_project.models import User
from django.urls import reverse
from capstone_project.viewsupport.errors import PageError, LoginError


class TestLogoutView(TestCase):

    def setUp(self):
        self.client = Client()
        self.session = self.client.session

        self.supervisor_user = User.objects.create(
            unique_id='cmwojta',
            pwd='password',
            user_type=User.UserType.Supervisor,
            # pwd_tmp=False
        )

    def test_logout_as_supervisor(self):
        self.session['user_id'] = self.supervisor_user.id
        self.session.save()

        resp = self.client.get(reverse('logout'))

        self.assertIsNone(resp.client.session.get('user_id', None), 'Logout did not clear the current user')

    def test_rejects_logout_not_logged_in(self):
        resp = self.client.get(reverse('logout'))

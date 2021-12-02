from django.shortcuts import reverse
from django.test import TestCase, Client
from django.http import HttpRequest, HttpResponse
from django.db.models import ObjectDoesNotExist
from typing import Optional

from capstone_project.models import User
from capstone_project.AcceptanceTests.acceptance_tests_base import AcceptanceTestCase
from capstone_project.viewsupport.errors import UserEditError, UserEditPlace
from capstone_project.viewsupport.message import Message, MessageQueue


class TestEditUser(AcceptanceTestCase[UserEditError]):
    def setUp(self):
        self.client = Client()
        self.session = self.client.session
        self.old_password = 'a-very-good-password'
        self.new_password = 'another-lesser-password'
        self.new_phone = '2622915566'

        self.supervisor_username = 'cmwojta'
        self.supervisor = User.objects.create(
            unique_id=self.supervisor_username,
            pwd=self.old_password,
            # pwd_tmp=False,
            user_type=User.UserType.Supervisor
        )

        self.supervisor_edit_url = reverse('users-edit', args=(self.supervisor.id,))

        self.staff_username = 'arodgers12'
        self.staff = User.objects.create(
            unique_id=self.staff_username,
            pwd=self.old_password,
            # pwd_tmp=False,
            user_type=User.UserType.Staff
        )

        self.staff_edit_url = reverse('users-edit', args=(self.staff.id,))

    def set_supervisor_session(self):
        self.session['user_id'] = self.supervisor.id
        self.session.save()

    def set_staff_session(self):
        self.session['user_id'] = self.staff.id
        self.session.save()

    def test_edit_self_contact(self):
        self.set_supervisor_session()
        resp = self.client.post(self.supervisor_edit_url, {
            'unique_id': self.supervisor_username,
            'phone': '4253084859'
        }, follow=False)

        self.assertContainsMessage(resp, Message('Contact Information Updated'))

        self.assertRedirects(
            resp,
            reverse('users-view', args=(self.supervisor.id,))
        )

    def test_edit_self_password(self):
        self.set_supervisor_session()
        resp = self.client.post(self.supervisor_edit_url, {
            'unique_id': self.supervisor_username,
            'old_password': self.old_password,
            'new_password': self.new_password,
        }, follow=False)

        self.assertContainsMessage(resp, Message('Password Updated'))

        self.assertRedirects(
            resp,
            reverse('users-view', args=(self.supervisor.id,)),
        )

    def test_edit_self_updates_database(self):
        # This test uses the staff to update self instead of supervisor, to cover more use cases
        self.set_staff_session()
        resp = self.client.post(self.staff_edit_url, {
            'unique_id': self.staff_username,
            'phone': self.new_phone,
        }, follow=False)

        new_staff = User.objects.get(unique_id=self.staff_username)

        self.assertIsNotNone(new_staff)
        self.assertEqual(new_staff.phone, self.new_phone, 'Did not change contact information in database')

    def test_supervisor_edit_other_updates_database(self):
        self.set_supervisor_session()
        resp = self.client.post(self.staff_edit_url, {
            'unique_id': self.staff_username,
            'phone': self.new_phone,
        }, follow=False)

        new_staff = User.objects.get(username=self.staff_username)

        self.assertIsNotNone(new_staff)
        self.assertEqual(new_staff.phone, self.new_phone, 'Did not change contact information in database')

    def test_rejects_supervisor_edit_other_password(self):
        self.set_supervisor_session()
        resp = self.client.post(self.staff_edit_url, {
            'unique_id': self.staff_username,
            'old_password': self.old_password,
            'new_password': self.new_password,
        }, follow=False)

        self.assertContainsMessage(resp, Message('You may not change another users password', Message.Type.ERROR))

        # self.assertDoesNotRedirect(resp, 'Tried to redirect after failing to update user')

    def test_supervisor_edit_other_type(self):
        self.set_supervisor_session()
        resp = self.client.post(self.staff_edit_url, {
            'unique_id': self.staff_username,
            'user_type': '0'
        }, follow=False)

        self.assertContainsMessage(
            resp,
            Message(f'User {self.staff.username} is now a Supervisor')
        )

        self.assertRedirects(resp, reverse('users-view', args=(self.staff.id,)))

    def test_rejects_empty_username(self):
        self.set_supervisor_session()
        resp = self.client.post(self.staff_edit_url, {
            'unique_id': ''

        }, follow=True)

        error = self.assertContextError(resp)

        self.assertTrue(error.place() is UserEditPlace.USERNAME,
                        msg='Didn\'t return username error when attempting to remove username.')
        self.assertEqual(error.message(), 'You can\'t remove a user\'s username.')

    def test_rejects_too_long_username(self):
        self.set_supervisor_session()
        resp = self.client.post(self.staff_edit_url, {
            'unique_id': 'a-very-long-username-that-the-database-could-not-hold'

        }, follow=True)

        error = self.assertContextError(resp)
        self.assertTrue(error.place() is UserEditPlace.USERNAME,
                        msg='Should have received an error about an username that was too long.')
        self.assertEqual(error.message(), 'A username may not be longer than 20 characters.')

    def test_rejects_incorrect_password_change(self):
        self.session['user_id'] = self.supervisor.id
        self.session.save()

        resp = self.client.post(self.supervisor_edit_url, {
            'unique_id': self.supervisor_username,
            'old_password': 'a password that is definitely correct',
            'new_password': self.new_password,
        }, follow=True)

        error = self.assertContextError(resp)
        self.assertTrue(error.place() is UserEditPlace.PASSWORD,
                        msg='Should have received an error about incorrect password.')
        self.assertEqual(error.message(), 'Incorrect password')

    def test_rejects_empty_password_change(self):
        self.set_supervisor_session()
        resp = self.client.post(self.supervisor_edit_url, {
            'unique_id': self.supervisor_username,
            'old_password': self.old_password,
            'new_password': '',
        }, follow=True)

        error = self.assertContextError(resp)
        self.assertTrue(error.place() is UserEditPlace.PASSWORD,
                        msg='Should have recieved an error about empty new password.')
        self.assertEqual(error.message(), 'New password can\'t be empty.')

    def test_rejects_too_short_password_change(self):
        self.set_supervisor_session()
        resp = self.client.post(self.supervisor_edit_url, {
            'unique_id': self.supervisor_username,
            'old_password': self.old_password,
            'new_password': '1234',
        }, follow=True)

        error = self.assertContextError(resp)
        self.assertTrue(error.place() is UserEditPlace.PASSWORD,
                        msg='Should have received an error about new password being too short.')
        self.assertEqual(error.message(), 'New Password needs to be 8 or more characters.')

    def test_rejects_invalid_phone(self):
        self.set_supervisor_session()
        resp = self.client.post(self.supervisor_edit_url, {
            'unique_id': self.supervisor_username,
            'phone': '123456'
        }, follow=True)

        error = self.assertContextError(resp)

        self.assertTrue(error.place() is UserEditPlace.PHONE,
                        msg='Should have received an error about incorrect phone edit.')
        self.assertEqual(error.message(), 'Phone number needs to be exactly 10 digits long.')

    def test_rejects_non_supervisor_edit_other(self):
        self.set_staff_session()
        resp_post = self.client.post(self.supervisor_edit_url, {
            'unique_id': self.supervisor_username,
            'phone': '123456'
        }, follow=False)

        self.assertContainsMessage(resp_post, Message('You are not allowed to edit other users.', Message.Type.ERROR))

        self.assertRedirects(resp_post, reverse('login'))

        resp_get = self.client.get(self.supervisor_edit_url, {}, follow=False)

        self.assertContainsMessage(resp_get, Message('You are not allowed to edit other users.', Message.Type.ERROR))

        self.assertRedirects(resp_get, reverse('login'))

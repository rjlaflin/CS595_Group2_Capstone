from capstone_project.ClassDesign.users import Users
from capstone_project.ClassDesign.LoginUtil import LoginUtil
from django.test import TestCase
import more_itertools
from capstone_project.models import User


class TestUser(TestCase):

    def setUp(self):
        self.name1 = 'john doe'
        self.phone1 = '123-456-7890'
        self.username1 = 'johndoe'
        self.password1 = 'password123'
        self.id1 = User.objects.create(
            user_type=User.UserType.Supervisor,
            unique_id=self.username1,
            pwd=self.password1,
            name=self.name1,
            phone=self.phone1)
        self.id2 = User.objects.create(user_type=User.UserType.Staff, username='staffmember', pwd='Password456')

    def test_create_user(self):
        user_id = Users.create_user(User.UserType.Supervisor, 'johndoe', 'password456')
        self.assertTrue(user_id > 0, msg='Expecting id returned confirming saved to database.')

    def test_get_user_by_user_id(self):
        user = Users.get_user_by_user_id(self.id1.id)
        self.assertEqual(self.id1.id, user.id, msg='User id should be equal userId1')

    def test_get_user_by_username(self):
        user = Users.get_user_by_login_id(self.username1)
        self.assertEqual(self.username1, user.unique_id, msg='Login ID should be equal to user1s login id.')

    def test_get_all_users(self):
        user_set = Users.get_all_users()
        list_of_users = list(user_set)
        length = more_itertools.ilen(list_of_users)
        self.assertEqual(2, length, msg='Expected list of courses to be 2.')
        self.assertTrue(self.id1 in list_of_users, msg='Exepect course1 in all courses.')
        self.assertTrue(self.id1 in list_of_users, msg='Expected course2 in all courses.')

    def test_delete_user(self):
        response = Users.delete_user(self.id1.id)
        self.assertEqual(True, response, msg='Because we expect that the object is not in database.')

    def test_update_user(self):
        user = Users.get_user_by_user_id(self.id2.id)
        name2 = 'Jane Doe'
        phone2 = '456-123-7890'
        Users.update_user(user, name2, phone2)
        user = Users.get_user_by_user_id(self.id2.id)
        self.assertEqual(name2, user.name, msg='')
        self.assertEqual(phone2, user.phone, msg='')

    def test_update_password(self):
        new_password = 'NewPassword123'
        user = Users.get_user_by_user_id(self.id1.id)
        LoginUtil.update_password(user, new_password)
        user = Users.get_user_by_user_id(self.id1.id)
        self.assertEqual(new_password, user.pwd, msg="Password is expected to be updated with new password.")
        # self.assertEqual(False, user.pwd_tmp, msg='Failed because expected tmp password was updated.')

    def test_check_user_type(self):
        user = Users.get_user_by_user_id(self.id1.id)
        self.assertEqual('0', user.user_type, msg="Expected SuperVisor as type for user1")

    def test_empty_user_type(self):
        with self.assertRaises(TypeError):
            new_user = Users.create_user('', 'cwojta', 'password456')

    def test_empty_username(self):
        new_user = Users.create_user(User.UserType.Supervisor, self.username1, self.password1)
        user = Users.get_user_by_user_id(new_user)
        self.assertTrue(user.unique_id, msg='Login ID can not be empty')

    def test_empty_password(self):
        with self.assertRaises(TypeError):
            new_user = Users.create_user(User.UserType.Supervisor, self.id1, '')

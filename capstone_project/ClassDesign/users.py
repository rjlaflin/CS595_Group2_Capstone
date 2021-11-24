from capstone_project.models import User
from typing import Union, Iterable, Optional
from django.core.exceptions import ObjectDoesNotExist
import more_itertools


class Users:

    @staticmethod
    def create_user(
            user_type: Union[User.UserType, int],
            login_id: str,
            password: str,
            name: str = '',
            phone: str = ''
    ) -> int:
        """
        Create User with mandatory user type, login_id(front end email), and password, returns user id
        """
        if type(user_type) is str:
            user_type = User.UserType.from_str(user_type)

        if login_id is None or login_id == '':
            raise TypeError('username cannot be blank')

        if password is None or password == '':
            raise TypeError('password cannot be blank')

        new_user = User.objects.create(
            user_type=user_type,
            unique_id=login_id,
            pwd=password,
            name=name,
            phone=phone
        )
        return new_user.id

    @staticmethod
    def get_user_by_user_id(user_id) -> Optional[User]:
        """
        Get user by user id and returns User if it exists, otherwise returns None
        """
        try:
            return User.UserType.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_login_id(login_id: str) -> Optional[User]:
        """
        Get user by login id and returns User if it exists, otherwise returns None
        """
        try:
            return User.UserType.objects.get(unique_id=login_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_all_users() -> Optional[Iterable[User]]:
        """
        Get all users if any exist otherwise return None
        """
        user_set = User.objects.all()
        return user_set if more_itertools.ilen(user_set) > 0 else None
        # try:
        #     return User.objects.all()
        # except User.DoesNotExist:
        #     return None

    @staticmethod
    def delete_user(id: int, keep_parents=False) -> bool:
        """
        Deletes User if it exists using the id and returns a boolean for confirmation
        """
        try:
            user = User.objects.get(id=id)
            user.delete()
            return True
        except ObjectDoesNotExist:
            return False

    @staticmethod
    def check_user_type(user: User):
        if user.UserType == User.UserType.Supervisor.value[0]:
            return User.UserType.SuperVisor
        elif user.UserType == User.UserType.Staff.value[0]:
            return User.UserType.Staff
        else:
            return User.UserType.Patient

    @staticmethod
    def update_user(user: User, name: Optional[str] = None, phone: Optional[str] = None):
        """
        Updates user for last name, first name, and phone.
        If field is None then does not update, if empty string then removes current.
        """
        if name is not None:
            user.name = name

        if phone is not None:
            user.phone = phone

        user.save()

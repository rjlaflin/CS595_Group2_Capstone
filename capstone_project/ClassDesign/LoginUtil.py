import uuid
from typing import Union, Optional, List
from django.http import HttpResponseRedirect

from capstone_project.ClassDesign.users import Users
from capstone_project.models import User
from capstone_project.viewsupport.message import Message, MessageQueue
from django.shortcuts import redirect, reverse
from django.contrib.sessions.backends.base import SessionBase


class LoginUtil:

    @staticmethod
    def update_password(user: User, pwd: str):
        user.pwd = pwd
        # user.pwd_tmp = False
        user.save()
    """ 
    @staticmethod
    def generate_tmp_password() -> str:
        return str(uuid.uuid4())[:8] """

    @staticmethod
    def get_user_and_validate_by_user_id(
            session: SessionBase,
            types: Optional[List[User.UserType]] = None,
            redirect_to: Optional[HttpResponseRedirect] = None,
            redirect_message: Optional[Message] = None,
            password_change_redirect: bool = True,
    ) -> Union[User, HttpResponseRedirect]:
        """
        Get a user from a request context and validate the user's type
        To ensure that the user has permission to look at this page at this time.
        If the user is redirected for being the incorrect type then `redirect_message` is added to their message queue.
        """

        try:
            user_id = session['user_id']
        except KeyError:
            user_id = None

        if user_id is None or type(user_id) is not int:
            MessageQueue.push(session, Message('You must log into the application before you can view that page'))
            return redirect(reverse('login'))

        user = Users.get_user_by_user_id(user_id)

        if user is None:
            MessageQueue.push(session, Message('You must log into the application before you can view that page'))
            return redirect(reverse('login'))

        """
        if user.pwd_tmp and password_change_redirect:
            MessageQueue.push(session, Message('You must change your password before accessing the application'))
            return redirect(reverse('users-edit', args=(user_id,))) """

        user_type = Users.check_user_type(user)

        if types is not None and len(types) > 0 and user_type not in types:

            if redirect_message is not None:
                MessageQueue.push(session, redirect_message)

            if redirect_to is None:
                redirect_to = redirect(reverse('index'))

            if type(redirect_to) is str:
                redirect_to = redirect(redirect_to)

            return redirect_to

        return user

from django.test import TestCase
from typing import TypeVar, Generic, Optional
from capstone_project.viewsupport.message import Message, MessageQueue

E = TypeVar('E')


class AcceptanceTestCase(Generic[E], TestCase):

    def assertContainsMessage(self, resp, has: Message, msg: Optional[str] = None):
        """
        Assert that the session contains a message, must be called before redirects are
        evaluated as most pages drain the message queue.
        """
        if msg is None:
            msg = f'Context did not contain message {has}'

        self.assertTrue(
            has in MessageQueue.get(resp.client.session),
            msg=f'{msg}\nMessage queue had these items:{MessageQueue.get(resp.client.session)}'
        )

    def assertContextVar(self, resp, var_name: str) -> object:
        ret = resp.context.get(var_name)

        self.assertIsNotNone(ret, msg=f'Context did not contain any variable with the name {var_name}')
        return ret

    def assertContextError(self, resp) -> E:
        """
        Assert that the render context contains an error object of the type T and return it.
        """
        error = self.assertContextVar(resp, 'error')

        return error

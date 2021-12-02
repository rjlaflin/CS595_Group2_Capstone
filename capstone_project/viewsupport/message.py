from enum import Enum, auto
from typing import Iterable, List, Union, Dict

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.base import SessionBase


class Message:
    """
    Represents a popover message to be shown ot the user on page load.
    """

    class Type(Enum):
        ERROR = 0,
        REGULAR = 1,

    def __init__(self, messsage: str, ty: Type = Type.REGULAR):
        self._message = messsage
        self._ty = ty

    def message(self) -> str:
        """Get the value of this popover message"""
        return self._message

    def type(self) -> Type:
        """Get the type of this popover message"""
        return self._ty

    def is_error(self) -> bool:
        return self._ty == Message.Type.ERROR

    def __eq__(self, other) -> bool:
        if type(other) is not Message:
            return False
        return self._ty.value == other._ty.value and self._message == other._message

    def __str__(self) -> str:
        return f'{self._ty}: {self._message}'


class MessageQueue:
    """
    Methods for sending messages to the user across application pages.
    Should be drained into view on each page load.
    """

    @staticmethod
    def drain(session: SessionBase) -> Iterable[Message]:
        """Take all messages from the message queue"""
        try:
            messages = MessageQueue.get(session)

            # Clear message queue
            del session['messages']

            return iter(messages)
        except KeyError:
            return iter([])

    @staticmethod
    def drain_n(session: SessionBase, n: int) -> Iterable[Message]:
        """Take up to n messages from the message queue"""
        try:
            messages = MessageQueue.get(session)
            m_len = len(messages)

            # Take n from message queue, or remainder if there are fewer than n left
            if m_len < n:
                del session['messages']
                session.save()
                return iter(messages)
            else:
                MessageQueue.put(session, messages[n:])
                return iter(messages[:n])

        except KeyError:
            return iter([])

    @staticmethod
    def push(session: SessionBase, messages: Union[List[Message], Message]):
        """Add a message to the message queue for the next page render"""
        current = MessageQueue.get(session)

        if type(messages) is Message:
            MessageQueue.put(session, current + [messages])
        else:
            MessageQueue.put(session, current + messages)

    @staticmethod
    def __to_serializable__(message: Message) -> Dict:
        """Mapping function for putting an individual message into the context, do not user directly"""
        return {
            'message': message.message(),
            'type': message.type().value[0],
        }

    @staticmethod
    def __from_serialized__(message: Dict) -> Message:
        """Mapping function for getting an individual message from the context, do not user directly"""
        m = message['message']
        t = int(message['type'])

        if t == Message.Type.REGULAR.value[0]:
            t = Message.Type.REGULAR
        elif t == Message.Type.ERROR.value[0]:
            t = Message.Type.ERROR
        else:
            raise TypeError(
                f'Could not deserialize message object due to type {t} being out of range.\nHad message {m}'
            )

        return Message(m, t)

    @staticmethod
    def get(session: SessionBase) -> List[Message]:
        """
        Get all messages currently in the session, without modifying them.
        Use iterable functions `drain`, `drain_n` instead.
        """
        try:
            return list(map(MessageQueue.__from_serialized__, session['messages']))
        except KeyError as e:
            return []

    @staticmethod
    def put(session: SessionBase, messages: List[Message]):
        """
        Set the messages in the context, overwriting what may have been already there.
        Use `push` instead.
        """
        session['messages'] = list(map(MessageQueue.__to_serializable__, messages))
        session.save()

from django.test import TestCase, Client
from capstone_project.viewsupport.message import Message, MessageQueue


class TestMessage(TestCase):
    def test_sets_message(self):
        m = 'This is a message to the user'
        message = Message(m)
        self.assertEqual(message.message(), m, 'Did not return correct message from object')

    def test_default_type(self):
        message = Message('message')
        self.assertTrue(message.type() is Message.Type.REGULAR, 'Did not default type correctly')

    def test_override_type(self):
        message = Message('m', Message.Type.ERROR)
        self.assertTrue(message.type() is Message.Type.ERROR, 'Did not override type correctly')


class TestMessageQueue(TestCase):

    def setUp(self) -> None:
        self.client = Client()
        self.sesion = self.client.session

        self.msg_text = 'This is a test message'

        self.reg_message = Message(self.msg_text)
        self.err_message = Message(self.msg_text, Message.Type.ERROR)

    def test_maps_serializable(self):
        serializable = MessageQueue.__to_serializable__(self.reg_message)

        self.assertIsNotNone(
            serializable.get('message'),
            msg='Did not place message field into serializable dict'
        )

        self.assertIsNotNone(
            serializable.get('type'),
            msg='Did not place type field into serializable dict'
        )

        self.assertEqual(
            self.msg_text,
            serializable['message'],
            msg='Did not serialize message field correctly'
        )
        self.assertEqual(
            self.reg_message.type().value[0],
            serializable['type'],
            msg='Did not serialize type field to correct value'
        )

    def test_maps_deserializable(self):
        deserialized = MessageQueue.__from_serialized__(
            MessageQueue.__to_serializable__(self.reg_message)
        )

        self.assertEqual(
            self.reg_message,
            deserialized,
            msg='Did not deserialize message components correctly'
        )

    def test_set_directly(self):
        MessageQueue.put(
            self.sesion,
            [self.reg_message]
        )

        self.assertEqual(1, len(MessageQueue.get(self.sesion)), msg='Did not place item in list')

    def test_get_all(self):
        MessageQueue.put(
            self.sesion,
            [self.reg_message]
        )

        queue_list = MessageQueue.get(self.sesion)

        self.assertTrue(
            self.reg_message in queue_list,
            msg='Did not get same item from list',
        )

    def test_pushes(self):
        MessageQueue.push(self.sesion, self.reg_message)

        self.assertTrue(
            self.reg_message in MessageQueue.get(self.sesion),
            msg='Did not push message into queue'
        )

    def test_drain_all(self):
        MessageQueue.push(self.sesion, self.reg_message)

        drain = MessageQueue.drain(self.sesion)

        self.assertTrue(self.reg_message in drain)

    def test_drain_fewer(self):
        MessageQueue.push(self.sesion, self.reg_message)
        MessageQueue.push(self.sesion, self.err_message)

        drain = MessageQueue.drain_n(self.sesion, 1)

        self.assertTrue(self.reg_message in drain, msg='Did not return first message when draining')
        self.assertTrue(self.err_message not in drain, msg='Returned too many messages when draining')

        remain = MessageQueue.get(self.sesion)

        self.assertEqual(1, len(remain), 'Did not leave extra messages in queue after partial drain')
        self.assertEqual(self.err_message, remain[0], msg='Did not leave correct message in queue after partial drain')

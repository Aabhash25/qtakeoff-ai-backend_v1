from django.test import TestCase, override_settings
from django.core import mail
from users.models import CustomUser
from users.utils import Util, generate_verification_email_token


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class UtilTests(TestCase):
    def test_send_email(self):
        data = {
            'subject': 'Test Subject',
            'body': 'This is for testing',
            'to_email': 'test@gmail.com'
        }
        Util.send_email(data)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, data['subject'])
        self.assertEqual(email.body, data['body'])
        self.assertEqual(email.to, [data['to_email']])

    def test_generate_verification_email_token(self):
        user = CustomUser.objects.create_user(
            email = 'user@gmail.com',
            username = 'Testuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1',
            is_active = True
        )
        uid, token = generate_verification_email_token(user)
        self.assertIsNotNone(uid)
        self.assertIsNotNone(token)
        self.assertTrue(isinstance(uid, str))
        self.assertTrue(isinstance(token, str))
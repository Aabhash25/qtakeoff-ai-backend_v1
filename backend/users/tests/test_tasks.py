from django.test import TestCase
from unittest.mock import patch
from users.tasks import send_email_verification, send_rest_password_email

class EmailTaskTest(TestCase):
    @patch('users.tasks.send_mail')
    def test_send_email_verification(self, mock_send_mail):
        mock_send_mail.return_value = 1
        result = send_email_verification(
            subject = 'Test Subject',
            message = 'Test Message',
            to_email = 'testing@gmail.com'
        )
        mock_send_mail.assert_called_once_with(
            subject = 'Test Subject',
            message = 'Test Message',
            from_email = 'toshiro.limbu01@gmail.com',
            recipient_list = ['testing@gmail.com']
        )
        self.assertTrue(result)

    @patch('users.tasks.send_mail')
    def test_send_rest_password_email_success(self, mock_send_mail):
        mock_send_mail.return_value = 1

        result = send_rest_password_email(
            subject="Reset Password",
            message="Click here to reset your password",
            to_email="test@example.com"
        )

        mock_send_mail.assert_called_once_with(
            subject="Reset Password",
            message="Click here to reset your password",
            from_email='toshiro.limbu01@gmail.com',
            recipient_list=["test@example.com"]
        )
        self.assertTrue(result)

    @patch('users.tasks.send_mail', side_effect=Exception("SMTP Error"))
    def test_send_email_verification_failure(self, mock_send_mail):
        result = send_email_verification(
            subject="Fail Subject",
            message="This should fail",
            to_email="fail@example.com"
        )

        self.assertFalse(result)

    @patch('users.tasks.send_mail', side_effect=Exception("SMTP Error"))
    def test_send_rest_password_email_failure(self, mock_send_mail):
        result = send_rest_password_email(
            subject="Fail Reset",
            message="Failure test",
            to_email="fail@example.com"
        )

        self.assertFalse(result)

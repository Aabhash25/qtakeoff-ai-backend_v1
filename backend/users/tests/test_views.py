from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import CustomUser, Role
from django.core import mail
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
from django.test import override_settings
from unittest.mock import patch
from users.tasks import send_rest_password_email

class UserViewTests(APITestCase):

    def setUp(self):
        self.user_data = {
            'email': 'testuser@gmail.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'role': Role.USER,
        }
        self.user = CustomUser.objects.create_user(
            email=self.user_data['email'],
            username=self.user_data['username'],
            first_name='Test',
            last_name='User',
            password='StrongPass123!',  # plain text
            role=Role.USER,
            is_active=True
        )
        self.user.is_active = True
        self.user.save()

    def test_user_registration(self):
        data = {
            'email': 'newuser@gmail.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'NewUserPass123!',
            'password2': 'NewUserPass123!',
            'role': 'user'
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertTrue(CustomUser.objects.filter(email='newuser@gmail.com').exists())

    def test_user_login(self):
        response = self.client.post(reverse('login'), {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_user_logout(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.post(reverse('logout'), data={'refresh': str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_password_change(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('change-password'), {
            'old_password': 'StrongPass123!',
            'new_password': 'NewStrongPass123!',
            'new_password2': 'NewStrongPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('users.serializers.send_rest_password_email.delay')
    def test_password_reset_email(self, mock_send_email):
        mock_send_email.side_effect = send_rest_password_email 
        response = self.client.post(reverse('send-reset-password-email'), {'email': self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)


    def test_email_verification_invalid_token(self):
        response = self.client.get(reverse('verify-email', kwargs={'uidb64': 'invalid', 'token': 'invalid'}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('users.views.id_token.verify_oauth2_token')
    @patch('users.views.SocialAccount.objects.get_or_create')
    def test_google_login(self, mock_social, mock_verify_token):
        mock_verify_token.return_value = {
            'email': 'googleuser@gmail.com',
            'sub': 'google123',
            'name': 'Google User',
            'given_name': 'Google',
            'family_name': 'User'
        }
        mock_social.return_value = (None, True)
        response = self.client.post(reverse('google-login'), {
            'token': 'fake-google-token',
            'role': 'user'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

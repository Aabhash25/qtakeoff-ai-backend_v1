from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from users.models import CustomUser, Role
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch


class UserURLsTest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email = 'testuser@gmail.com',
            username = 'testuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1',
            role = Role.USER,
            is_active = True
        )
    
    def test_register(self):
        url = reverse('register')
        data = {
            'email': 'newuser@gmail.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'HelloWorld!1',
            'password2': 'HelloWorld!1',
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def rest_login(self):
        url = reverse('login')
        data = {
            'email' : self.user.email,
            'password': 'HelloWorld!1',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_verify_email(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = PasswordResetTokenGenerator().make_token(self.user)
        url = reverse('verify-email', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_302_FOUND])

    def test_logout(self):
        refresh = RefreshToken.for_user(self.user)
        url = reverse('logout')
        self.client.force_authenticate(user=self.user)
        data = {
            'refresh': refresh
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_205_RESET_CONTENT])

    def test_change_password(self):
        url = reverse('change-password')
        self.client.force_authenticate(user=self.user)
        data = {
            'old_password': 'HelloWorld!1',
            'new_password': 'HelloWorld!1234',
            'new_password2': 'HelloWorld!1234'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_send_reset_password_email(self):
        url = reverse('send-reset-password-email')
        data = {
            'email': self.user.email
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = PasswordResetTokenGenerator().make_token(self.user)
        url = reverse('reset-password', kwargs={'uid':uid, 'token': token})
        data = {
            'password': 'HelloWorld!1234',
            'password2': 'HelloWorld!1234'
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

    @patch('users.views.id_token.verify_oauth2_token')
    @patch('users.views.SocialAccount.objects.get_or_create')
    def test_google_login(self, mock_social_get_or_create, mock_verify_token):
        mock_verify_token.return_value = {
            'email': 'googletestuser@gmail.com',
            'sub': 'google123',
            'name': 'Google TestUser',
            'given_name': 'Google',
            'family_name': 'TestUser'
        }
        mock_social_get_or_create.return_value = (None, True)
        url = reverse('google-login')
        data  = {
            'token': 'fake-google-token',
            'role': Role.USER
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    

from django.test import TestCase
from users.serializers import (
    CustomUserRegistrationSerializer,
    CustomUserLoginSerializer,
    CustomUserLogoutSerailizer,
    CustomUserChangePasswordSerializer,
    SendPasswordResetEmailSerializer,
    SetNewPasswordSerializer,
    GoogleAuthSerializer
)
from users.models import CustomUser, Role
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework_simplejwt.tokens import RefreshToken

class SerializerTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@gmail.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            password="Password@123",
            role=Role.USER
        )
        self.user.is_active = True
        self.user.save()

    def test_registration_serializer_valid(self):
        data = {
            "email": "newuser@gmail.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "role": "user",
            "password": "Password@123",
            "password2": "Password@123"
        }
        serializer = CustomUserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_registration_serializer_invalid_email_domain(self):
        data = {
            "email": "invalid@yahoo.com",
            "username": "baduser",
            "first_name": "Bad",
            "last_name": "Email",
            "role": "user",
            "password": "Password@123",
            "password2": "Password@123"
        }
        serializer = CustomUserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_login_serializer_success(self):
        data = {
            "email": "test@gmail.com",
            "password": "Password@123"
        }
        serializer = CustomUserLoginSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_login_serializer_wrong_password(self):
        data = {
            "email": "test@gmail.com",
            "password": "wrongpass"
        }
        serializer = CustomUserLoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_logout_serializer_token_blacklisting(self):
        refresh = RefreshToken.for_user(self.user)
        serializer = CustomUserLogoutSerailizer(data={"refresh": str(refresh)})
        self.assertTrue(serializer.is_valid())
        serializer.save()

    def test_change_password_serializer_valid(self):
        self.client.force_login(self.user)
        context = {"request": type('Request', (), {"user": self.user})()}
        data = {
            "old_password": "Password@123",
            "new_password": "NewPassword@456",
            "new_password2": "NewPassword@456"
        }
        serializer = CustomUserChangePasswordSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_send_password_reset_email_serializer_valid(self):
        data = {"email": "test@gmail.com"}
        serializer = SendPasswordResetEmailSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_set_new_password_serializer_valid(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = PasswordResetTokenGenerator().make_token(self.user)
        context = {"uid": uid, "token": token}
        data = {
            "password": "NewPassword@123",
            "password2": "NewPassword@123"
        }
        serializer = SetNewPasswordSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_google_auth_serializer_valid(self):
        data = {
            "token": "dummy-google-token",
            "role": "user"
        }
        serializer = GoogleAuthSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

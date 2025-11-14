from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from users.models import Role

CustomUser = get_user_model()

class CustomUserModelTest(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name='User')
        Group.objects.get_or_create(name='Estimator')
        Group.objects.get_or_create(name='Admin')

    def test_create_user_with_valid_data(self):
        user = CustomUser.objects.create_user(
            email='user@example.com',
            username='testuser',
            first_name='John',
            last_name='Doe',
            password='securepassword123',
            role=Role.USER
        )
        self.assertEqual(user.email, 'user@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIn(Group.objects.get(name='User'), user.groups.all())

    def test_create_estimator_with_invalid_email_should_fail(self):
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(
                email='estimator@gmail.com',
                username='badestimator',
                first_name='Jane',
                last_name='Smith',
                password='password123',
                role=Role.ESTIMATOR
            )

    def test_create_estimator_with_valid_email_should_pass(self):
        user = CustomUser.objects.create_user(
            email='estimator@ssnbuilders.com',
            username='goodestimator',
            first_name='Eli',
            last_name='Wong',
            password='password123',
            role=Role.ESTIMATOR
        )
        self.assertEqual(user.role, Role.ESTIMATOR)
        self.assertIn(Group.objects.get(name='Estimator'), user.groups.all())

    def test_create_superuser(self):
        admin = CustomUser.objects.create_superuser(
            email='admin@ssnbuilders.com',
            username='superadmin',
            first_name='Super',
            last_name='User',
            password='supersecurepassword'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
        self.assertEqual(admin.role, Role.USER)

    def test_string_representation(self):
        user = CustomUser.objects.create_user(
            email='str@example.com',
            username='stringtest',
            first_name='String',
            last_name='Test',
            password='str12345'
        )
        self.assertEqual(str(user), 'str@example.com')

    def test_clean_estimator_validation(self):
        user = CustomUser(
            email='notallowed@gmail.com',
            username='fakeest',
            first_name='Fake',
            last_name='Estimator',
            role=Role.ESTIMATOR
        )
        with self.assertRaises(ValidationError):
            user.full_clean()

from django.test import TestCase
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save
from django.apps import apps
from users.models import CustomUser, Role
from users.signals import create_user_groups, sync_user_group


class SignalsTestCase(TestCase):

    def setUp(self):
        Group.objects.all().delete()

    def test_create_user_groups_signal(self):
        create_user_groups(sender=apps.get_app_config('users'))

        self.assertTrue(Group.objects.filter(name='User').exists())
        self.assertTrue(Group.objects.filter(name='Estimator').exists())
        self.assertTrue(Group.objects.filter(name='Admin').exists())

        user_group = Group.objects.get(name='User')
        estimator_group = Group.objects.get(name='Estimator')
        admin_group = Group.objects.get(name='Admin')

        self.assertGreater(user_group.permissions.count(), 0)
        self.assertGreater(estimator_group.permissions.count(), 0)
        self.assertEqual(
            admin_group.permissions.count(),
            Permission.objects.count()
        )

    def test_sync_user_group_signal_for_user(self):
        user = CustomUser.objects.create_user(
            email="user@gmail.com",
            username="normaluser",
            first_name="normal",
            last_name="user",
            password="Test@1234",
            role=Role.USER,
        )
        self.assertTrue(user.groups.filter(name="User").exists())
        self.assertFalse(user.groups.filter(name="Estimator").exists())

    def test_sync_user_group_signal_for_estimator(self):
        user = CustomUser.objects.create_user(
            email="estimator@ssnbuilders.com",
            username="estimatoruser",
            first_name="estimator",
            last_name="user",
            password="Test@1234",
            role=Role.ESTIMATOR,
        )
        self.assertTrue(user.groups.filter(name="Estimator").exists())
        self.assertFalse(user.groups.filter(name="User").exists())

    def test_sync_user_group_signal_for_admin(self):
        admin = CustomUser.objects.create_superuser(
            email="admin@ssnbuilders.com",
            username="adminuser",
            first_name="admin",
            last_name="user",
            password="Admin@1234",
            role=Role.ADMIN,
        )
        self.assertTrue(admin.groups.filter(name="Admin").exists())

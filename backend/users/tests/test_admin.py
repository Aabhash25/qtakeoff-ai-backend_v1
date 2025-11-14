from django.contrib import admin
from django.test import TestCase
from users.admin import CustomUserAdmin
from users.models import CustomUser


class CustomUserAdminTest(TestCase):

    def test_admin_registration(self):
        # Ensure the model is registered
        self.assertIn(CustomUser, admin.site._registry)

    def test_admin_class_type(self):
        # Ensure the registered admin class is our CustomUserAdmin
        registered_admin = type(admin.site._registry[CustomUser])
        self.assertEqual(registered_admin, CustomUserAdmin)

    def test_list_display_fields(self):
        expected_fields = ('email', 'username', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
        admin_instance = CustomUserAdmin(CustomUser, admin.site)
        self.assertEqual(admin_instance.list_display, expected_fields)

    def test_fieldsets_configuration(self):
        admin_instance = CustomUserAdmin(CustomUser, admin.site)
        fieldset_titles = [fieldset[0] for fieldset in admin_instance.fieldsets]
        self.assertIn('Personal info', fieldset_titles)
        self.assertIn('Permissions', fieldset_titles)

    def test_add_fieldsets_contains_custom_fields(self):
        admin_instance = CustomUserAdmin(CustomUser, admin.site)
        add_fields = admin_instance.add_fieldsets[0][1]['fields']
        self.assertIn('email', add_fields)
        self.assertIn('role', add_fields)



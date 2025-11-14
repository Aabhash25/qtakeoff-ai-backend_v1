from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import uuid
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, RegexValidator

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')
        role = extra_fields.pop('role', Role.USER)

        email = self.normalize_email(email)
        if role == Role.ESTIMATOR and not email.endswith('@ssnbuilders.com'):
            raise ValueError('Estimators must use an @ssnbuilders.com email address.')
        
        user = self.model(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=role,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        
        if role == Role.ESTIMATOR:
            group = Group.objects.get(name='Estimator')
        elif role == Role.USER:
            group = Group.objects.get(name='User')
        elif role == Role.ADMIN:
            group = Group.objects.get(name='Admin')
        else:
            group = None
        if group:
            user.groups.add(group)
        
        return user
    
    def create_superuser(self, email, username, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_active') is not True:
            raise ValueError('Superuser must have is_active=True.')

        return self.create_user(email, username, first_name, last_name, password, **extra_fields)
    
class Role(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    USER = 'user', 'User'
    ESTIMATOR = 'estimator', 'Estimator'

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email
    
    def clean(self):
        super().clean()
        if self.role == Role.ESTIMATOR and not self.email.endswith('@ssnbuilders.com'):
            raise ValidationError("Estimators must use an @ssnbuilders.com email address.")

    def save(self, *args, **kwargs):
        skip_clean = kwargs.pop('skip_clean', False)
        if not skip_clean:
            self.full_clean()
        super().save(*args, **kwargs)
        
    # def get_full_name(self):
    #     return f"{self.first_name} {self.last_name}".strip()


class CustomUserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE,related_name='user_profile')
    mobile_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\d{10}$', 'Enter a valid mobile number.')], null=True, blank=True
    )

    def __str__(self):
        return self.user.username
       
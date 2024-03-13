from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext as _


class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, blank=False, max_length=255, verbose_name="email")

    phoneNumber = models.CharField(unique=True, null=True, max_length=255, verbose_name="phone")

    avatar = models.CharField(null=True, blank=True, max_length=255)
    country = models.CharField(null=True, blank=True, max_length=255)
    city = models.CharField(null=True, blank=True, max_length=255)
    first_name = models.CharField(null=True, blank=True, max_length=255)
    last_name = models.CharField(null=True, blank=True, max_length=255)

    password_reset_token = models.CharField(null=True, blank=True)
    password_reset_token_expires_at = models.DateTimeField(null=True, blank=True)

    username = models.CharField(_('username'), max_length=150, unique=True, blank=True, null=True)

    objects = CustomUserManager()  # pyright: ignore [reportAssignmentType,reportGeneralTypeIssues]

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []


User = CustomUser

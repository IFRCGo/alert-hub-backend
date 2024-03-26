from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError(_('The email must be set'))
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class EmailNotificationType(models.IntegerChoices):
    # Generic email types
    ACCOUNT_ACTIVATION = 1, 'Account Activation'
    PASSWORD_RESET = 2, 'Password Reset'
    PASSWORD_CHANGED = 3, 'Password Changed'
    NEWS_AND_OFFERS = 4, 'News And Offers'
    # Other emails are configured using subscriptions

    @classmethod
    def get_opt_emails(cls):
        always_send = [
            cls.ACCOUNT_ACTIVATION,
            cls.PASSWORD_RESET,
        ]
        return {enum.name: (enum.value, enum.label) for enum in cls if enum.value not in always_send}


class User(AbstractUser):
    class OptEmailNotificationType(models.IntegerChoices):
        NEWS_AND_OFFERS = EmailNotificationType.NEWS_AND_OFFERS

    OPT_EMAIL_NOTIFICATION_TYPES = [value for value, _ in OptEmailNotificationType.choices]

    username = None
    email = models.EmailField(verbose_name=_('email'), unique=True, blank=False, max_length=255)
    # bounced_email = models.BooleanField(verbose_name=_('Email tagged as bounced'), default=False)

    email_opt_outs = ArrayField(
        models.IntegerField(
            choices=OptEmailNotificationType.choices,
        ),
        default=list,
        blank=True,
    )

    first_name = models.CharField(null=True, blank=True, max_length=255)
    last_name = models.CharField(null=True, blank=True, max_length=255)
    display_name = models.CharField(
        verbose_name=_('system generated user display name'), null=True, blank=True, max_length=255
    )

    # avatar = models.CharField(null=True, blank=True, max_length=255)
    phone_number = models.CharField(verbose_name=_('phone'), unique=True, null=True, max_length=20)

    # TODO: Need validation for these?
    country = models.CharField(null=True, blank=True, max_length=255)
    city = models.CharField(null=True, blank=True, max_length=255)

    EMAIL_FIELD = USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()  # type: ignore [reportAssignmentType,reportGeneralTypeIssues]

    def save(self, *args, **kwargs):
        self.display_name = self.get_full_name() or f'User#{self.pk}'
        return super().save(*args, **kwargs)

    def unsubscribe_email(self, email_type, save=False) -> None:
        self.email_opt_outs = list(
            set(
                [
                    *self.email_opt_outs,
                    email_type,
                ]
            )
        )
        if save:
            self.save(update_fields=('email_opt_outs',))

    def is_email_subscribed_for(self, email_type) -> bool:
        return email_type in self.email_opt_outs and email_type in self.OPT_EMAIL_NOTIFICATION_TYPES

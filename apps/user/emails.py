from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from main.permalinks import Permalink
from main.tokens import TokenManager
from utils.emails import send_email

from .models import EmailNotificationType, User


def send_account_activation(user: User):
    """
    Generate a one-use only link for account activation and send it to the
    user.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = TokenManager.account_activation_token_generator.make_token(user)
    context = {
        'activation_url': Permalink.user_activation(uid, token),
    }
    send_email(
        user=user,
        email_type=EmailNotificationType.ACCOUNT_ACTIVATION,
        subject="Account Activation",
        email_html_template='emails/user/activation/body.html',
        email_text_template='emails/user/activation/body.txt',
        context=context,
    )


def send_password_reset(
    user: User,
    client_ip: str | None = None,
    device_type: str | None = None,
) -> tuple[str, str]:
    """
    Generate a one-use only link for resetting password and send it to the
    user.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = TokenManager.password_reset_token_generator.make_token(user)
    context = {
        'time': timezone.now(),
        'location': client_ip,
        'device': device_type,
        'password_reset_url': Permalink.user_password_reset(uid, token),
    }
    send_email(
        user=user,
        email_type=EmailNotificationType.PASSWORD_RESET,
        subject="Alert Hub: Password Reset",
        email_html_template='emails/user/password_reset/body.html',
        email_text_template='emails/user/password_reset/body.txt',
        context=context,
    )
    return uid, token


def send_password_changed_notification(user, client_ip, device_type):
    context = {
        'time': timezone.now(),
        'location': client_ip,
        'device': device_type,
        'frontend_forgot_password': Permalink.FORGOT_PASSWORD,
    }
    send_email(
        user=user,
        email_type=EmailNotificationType.PASSWORD_CHANGED,
        subject='Alert Hub: Password Changed',
        email_html_template='emails/user/password_changed/body.html',
        email_text_template='emails/user/password_changed/body.txt',
        context=context,
    )

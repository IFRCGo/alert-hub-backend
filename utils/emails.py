import logging

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.user.models import EmailNotificationType, User

logger = logging.getLogger(__name__)


def _base_send_email(
    subject: str | None,
    subject_template: str | None,
    email_html_template: str,
    email_text_template: str,
    context: dict,
    from_email: str,
    to_email: str,
):
    """
    Send a django.core.mail.EmailMultiAlternatives to `to_email`.
    Renders provided templates and send it to to_email
    Low level, Don't use this directly
    """
    # Subject
    if subject_template:
        subject = loader.render_to_string(subject_template, context)
    elif subject:
        subject = ''.join(
            # Email subject *must not* contain newlines
            subject.splitlines()
        )
    else:
        raise ValueError('Both arguments subject/subject_template cannot be None')

    # Body
    html_content = loader.render_to_string(email_html_template, context)
    text_content = loader.render_to_string(email_text_template, context)
    # Email message
    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_content,  # Plain text
        from_email=from_email,
        to=[to_email],
    )
    # HTML
    email_message.attach_alternative(html_content, "text/html")
    # Send email
    email_message.send()


def send_email(
    user: User,
    email_type: EmailNotificationType,
    subject: str | None,
    email_html_template: str,
    email_text_template: str,
    context: None | dict = None,
    subject_template: str | None = None,
):
    """
    Validates email request
    Add common context variable
    """
    # NOTE: We don't handle bounced email status
    if not user.is_email_subscribed_for(email_type):
        logger.warning(
            '[{}] Email not sent: User <{}>({}) has not subscribed!!'.format(
                email_type,
                user.email,
                user.pk,
            )
        )
        return

    if context is None:
        context = {}
    context.update(
        {
            'client_domain': settings.APP_FRONTEND_HOST,
            'protocol': settings.APP_HTTP_PROTOCOL,
            'domain': settings.APP_DOMAIN,
            'user': user,
            'email_type': email_type,
            # WIP
            'unsubscribe_email_types': User.OPT_EMAIL_NOTIFICATION_TYPES,
            'unsubscribe_email_token': PasswordResetTokenGenerator().make_token(user),
            'unsubscribe_email_id': urlsafe_base64_encode(force_bytes(user.pk)),
        }
    )

    _base_send_email(
        subject=subject,
        subject_template=subject_template,
        email_html_template=email_html_template,
        email_text_template=email_text_template,
        context=context,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_email=user.email,
    )

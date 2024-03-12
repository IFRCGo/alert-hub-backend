from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from project import settings


@shared_task(bind=True, queue='user_manager')
def send_email(self, email, subject, template_name, context=None):

    message = render_to_string(template_name, context)

    send_mail(
        subject=subject,
        message=strip_tags(message),
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=True,
    )

    return "Done"

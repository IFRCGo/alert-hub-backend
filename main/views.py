from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader

from apps.subscription.emails import generate_user_alert_subscription_email_context
from apps.subscription.models import UserAlertSubscription
from main.permalinks import Permalink

USER_ALERT_SUBSCRIPTION_EMAIL_PREVIEW_MESSAGE = """
    To use email_frequency in GET params, Please specify integer values. Default is Daily </br>
    Use this for reference </br></br>
    """ + '</br>'.join(
    [f"{frequency.label}: {frequency.value}" for frequency in UserAlertSubscription.EmailFrequency]
)


@login_required
def user_alert_subscription_email_preview(request):
    try:
        email_frequency = int(
            request.GET.get(
                "email_frequency",
                UserAlertSubscription.EmailFrequency.DAILY,
            )
        )
        if email_frequency not in UserAlertSubscription.EmailFrequency:
            return HttpResponse(USER_ALERT_SUBSCRIPTION_EMAIL_PREVIEW_MESSAGE)
        email_frequency = UserAlertSubscription.EmailFrequency(email_frequency)
    except ValueError:
        return HttpResponse(USER_ALERT_SUBSCRIPTION_EMAIL_PREVIEW_MESSAGE)

    have_data, context, _ = generate_user_alert_subscription_email_context(
        request.user,
        email_frequency,
    )
    if have_data:
        template = loader.get_template("emails/subscription/body.html")
        return HttpResponse(template.render(context, request))
    return HttpResponse("Nothing to display.. Try tagging alerts to subscriptions")


def password_reset_email_preview(request):
    context = {
        "location": "192.168.00.00",
        "device": "FakeOS",
        "password_reset_url": Permalink.user_password_reset("fake-uid", "fake-token"),
    }
    template = loader.get_template("emails/user/password_reset/body.html")
    return HttpResponse(template.render(context, request))


def password_changed_email_preview(request):
    context = {
        "location": "192.168.00.00",
        "device": "FakeOS",
        "frontend_forgot_password": Permalink.FORGOT_PASSWORD,
    }
    template = loader.get_template("emails/user/password_changed/body.html")
    return HttpResponse(template.render(context, request))


def user_activation_email_preview(request):
    context = {
        "activation_url": Permalink.user_activation("fake-uid", "fake-token"),
    }
    template = loader.get_template("emails/user/activation/body.html")
    return HttpResponse(template.render(context, request))

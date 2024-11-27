from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader

from .emails import generate_user_alert_subscription_email_context
from .models import UserAlertSubscription

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

    context, _ = generate_user_alert_subscription_email_context(
        request.user,
        email_frequency,
    )
    template = loader.get_template("emails/subscription/body.html")
    return HttpResponse(template.render(context, request))

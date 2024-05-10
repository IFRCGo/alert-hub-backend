from django.db import models
from django.http import HttpResponse
from django.template import loader

from .models import Alert


def index(request):
    latest_alert_list = Alert.objects.order_by("-sent").values(
        'identifier',
        'sender',
        'sent',
        'status',
        'msg_type',
        country_name=models.F('country__name'),
        country_iso3=models.F('country__iso3'),
        feed_url=models.F('feed__url'),
    )[:10]
    template = loader.get_template("cap_feed/index.html")
    context = {
        "latest_alert_list": latest_alert_list,
    }
    return HttpResponse(template.render(context, request))

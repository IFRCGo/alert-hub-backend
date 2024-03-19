from django.http import HttpResponse
from django.template import loader

from apps.cap_feed.tasks import inject_data

from .models import Alert


def index(request):
    latest_alert_list = Alert.objects.order_by("-sent")[:10]
    template = loader.get_template("cap_feed/index.html")
    context = {
        "latest_alert_list": latest_alert_list,
    }
    return HttpResponse(template.render(context, request))


def inject(request):
    try:
        inject_data.apply_async(args=(), kwargs={}, queue='inject')
    except Exception:
        print('Celery not running')
    return HttpResponse("Done")

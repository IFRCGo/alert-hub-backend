from django.http import HttpResponse, JsonResponse
from django.template import loader
from .models import Alert, Feed, LanguageInfo

from cap_feed.tasks import inject_data



def index(request):
    latest_alert_list = Alert.objects.order_by("-sent")[:10]
    template = loader.get_template("cap_feed/index.html")
    context = {
        "latest_alert_list": latest_alert_list,
    }
    return HttpResponse(template.render(context, request))

def inject(request):
    try:
        inject_data.apply_async(args=[], kwargs={}, queue='inject')
    except:
        print('Celery not running')
    return HttpResponse("Done")

def get_feeds(request):
    feeds = Feed.objects.filter(enable_rebroadcast=True)
    response = {'sources' : []}
    for feed in feeds:

        language_set = []
        for info in LanguageInfo.objects.filter(feed=feed):
            language_set.append(
                {
                    'name' : info.name,
                    'code' : info.language,
                    'logo' : info.logo
                }
            )

        response['sources'].append(
            {'source' : {
                'sourceId': feed.id,
                'byLanguage' : language_set,
                'authorName': feed.author_name,
                'authorEmail': feed.author_email,
                'sourceIsOfficial': feed.official,
                'capAlertFeed': feed.url,
                'capAlertFeedStatus': 'testing',
                'authorityCountry': feed.country.iso3,
                }
            }
        )
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

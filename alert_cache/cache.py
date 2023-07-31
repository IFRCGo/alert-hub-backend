import json

from .models import CapFeedAlert, CapFeedCountry
from django.core.cache import cache

def cache_alert():
    all_alerts = CapFeedAlert.objects.all()
    #This dictionary is used for returning all alerts in fewer fields
    short_alert_dictionary = {}
    #This dictionary is used for fast search of alert by id and return all information of that alert
    alert_dictionary = {}
    for alert in all_alerts:
        short_alert_dictionary[alert.id] = alert.to_dict_in_short()
        alert_dictionary[alert.id] = json.dumps(alert.to_dict())
    cache.set("short_alert_dictionary",short_alert_dictionary,timeout=None)
    cache.set("alerts_in_json", json.dumps(list(short_alert_dictionary.values()), indent=None),
              timeout=None)
    cache.set("alert_dictionary", alert_dictionary, timeout=None)


def cache_country():
    all_countries = CapFeedCountry.objects.all()
    country_dictionary = {}
    for country in all_countries:
        country_dictionary[country.id] = json.dumps(country.to_dict())
    cache.set("countries", country_dictionary, timeout=None)
    cache.set("countries_in_json", json.dumps(list(country_dictionary.values()), indent=None),
              timeout=None)

def get_alerts():
    alerts = cache.get("alerts_in_json")
    return alerts

def get_alert_by_id(alert_id):
    alert_dictionary = cache.get("alert_dictionary")
    print(len(alert_dictionary))
    if alert_id in alert_dictionary:
        return alert_dictionary[alert_id]
    else:
        return "Alert is Not Found!"


def get_countries():
    countries = cache.get("countries_in_json")
    return countries

def get_country_by_id(country_id):
    country_dictionary = cache.get("countries")

    if country_id in country_dictionary:
        return country_dictionary[country_id]
    else:
        return "No Country with Provided Id is Found."


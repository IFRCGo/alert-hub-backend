import json

from .models import CapFeedAlert, CapFeedCountry, CapFeedRegion
from django.core.cache import cache


#Region Level Cache
def initialise_region_cache():
    regions = CapFeedRegion.objects.all()

    regions_dict = {}
    for region in regions:
        region_dict = {}
        region_dict["id"] = region.id
        region_dict["name"] = region.name
        region_dict["centroid"] = region.centroid
        region_dict["countries"] = {}
        regions_dict[region.id] = region_dict

    #Append country data
    countries = CapFeedCountry.objects.all()
    for country in countries:
        country_dict = {}
        country_dict["id"] = country.id
        country_dict["name"] = country.name
        country_dict["centroid"] = country.centroid
        country_dict["urgency"] = {}
        country_dict["severity"] = {}
        country_dict["certainty"] = {}

        regions_dict[country.region.id]["countries"][country.id] = country_dict

    #Append all existing alerts data into region dict
    alerts = CapFeedAlert.objects.all()
    for alert in alerts:
        append_alert_info_to_region_cache(regions_dict, alert)
    cache.set("regions", regions_dict, timeout=None)
    cache.set("regions_in_json", json.dumps(regions_dict,indent=None), timeout=None)


def cache_imcoming_alerts_info_into_region_cache(alert_id):
    alert = CapFeedAlert.objects.filter(id=alert_id).first()
    regions_dict = cache.get("regions")
    if alert != None:
        append_alert_info_to_region_cache(regions_dict,alert)
        cache.set("regions", regions_dict, timeout=None)
        cache.set("regions_in_json", json.dumps(regions_dict, indent=None), timeout=None)

def append_alert_info_to_region_cache(regions_dict, alert):
    alert_region_id = alert.country.region.id
    alert_country_id = alert.country.id
    country_dict = regions_dict[alert_region_id]["countries"][alert_country_id]
    severity_dict = country_dict["severity"]
    urgency_dict = country_dict["urgency"]
    certainty_dict = country_dict["certainty"]

    info = alert.capfeedalertinfo_set.first()
    if info != None:
        severity = info.severity
        urgency = info.urgency
        certainty = info.certainty
        if severity not in severity_dict:
            severity_dict[severity] = 1
        else:
            severity_dict[severity] = severity_dict[severity] + 1

        if urgency not in urgency_dict:
            urgency_dict[urgency] = 1
        else:
            urgency_dict[urgency] = urgency_dict[urgency] + 1

        if certainty not in certainty_dict:
            certainty_dict[certainty] = 1
        else:
            certainty_dict[certainty] = certainty_dict[certainty] + 1

def remove_alerts_info_from_regions_cache(alert_id):
    cache_keys = cache.client.keys('*')
    alert_cache_key = "alert" + str(alert_id)

    if alert_cache_key not in cache_keys:
        return f"Alert: {alert_id} is not in the cache."
    alert_dict = json.loads(cache.get(alert_cache_key))
    regions_dict = cache.get("regions")

    alert_region_id = alert_dict["region_id"]
    alert_country_id = alert_dict["country_id"]
    alert_info = alert_dict["info"]
    if len(alert_info) == 0:
        return None
    severity = alert_info[0]["severity"]
    urgency = alert_info[0]["urgency"]
    certainty = alert_info[0]["certainty"]

    country_dict = regions_dict[alert_region_id]["countries"][alert_country_id]
    severity_dict = country_dict["severity"]
    urgency_dict = country_dict["urgency"]
    certainty_dict = country_dict["certainty"]
    if severity in severity_dict:
        severity_dict[severity] -= 1
        if severity_dict[severity] == 0:
            del severity_dict[severity]
    if urgency in urgency_dict:
        urgency_dict[urgency] -= 1
        if urgency_dict[urgency] == 0:
            del urgency_dict[urgency]

    if certainty in certainty_dict:
        certainty_dict[certainty] -= 1
        if certainty_dict[certainty] == 0:
            del certainty_dict[certainty]
    cache.set("regions", regions_dict, timeout=None)
    cache.set("regions_in_json", json.dumps(regions_dict, indent=None), timeout=None)
    return f"Alert: {alert_id} is removed from regional level records."


def get_regions():
    return cache.get("regions_in_json")
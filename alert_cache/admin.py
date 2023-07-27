from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CapFeedAlert, CapFeedAlertInfo, CapFeedAlertInfoParameter, CapFeedAlertInfoArea, \
    CapFeedAlertInfoAreaGeocode, CapFeedAlertInfoAreaPolygon, CapFeedAlertInfoAreaCircle, CapFeedContinent, \
    CapFeedRegion, CapFeedCountry, CapFeedFeed
from django_celery_beat.models import CrontabSchedule, ClockedSchedule, SolarSchedule, IntervalSchedule

class CapFeedAlertInfoAreaGeocodeAdmin(admin.ModelAdmin):
    list_display = ["alert_info_area", "value_name", "value"]

class CapFeedAlertInfoAreaPolygonAdmin(admin.ModelAdmin):
    list_display = ["alert_info_area", "value"]

class CapFeedAlertInfoAreaCircleAdmin(admin.ModelAdmin):
    list_display = ["alert_info_area", "value"]

class CapFeedAlertInfoParameterAdmin(admin.ModelAdmin):
    list_display = ["alert_info", "value_name", "value"]

class CapFeedAlertInfoAreaAdmin(admin.ModelAdmin):
    list_display = ["alert_info", "area_desc"]

class CapFeedAlertInfoAdmin(admin.ModelAdmin):
    list_display = ["alert", "language"]
    list_filter = ["alert__feed", "alert__country"]
    search_fields = ["alert__id"]
    fieldsets = [
        ("Administration", {"fields": ["alert"]}),
        ("Alert Info" , {"fields": ["language", "category", "event", "response_type", "urgency", "severity", "certainty", "audience", "event_code", "effective", "onset", "expires", "sender_name", "headline", "description", "instruction", "web", "contact"]}),
    ]

class CapFeedAlertInfoInline(admin.StackedInline):
    model = CapFeedAlertInfo
    extra = 0

class CapFeedAlertAdmin(admin.ModelAdmin):
    list_display = ["id", "feed", "sent", "status", "msg_type", "scope"]
    list_filter = ["feed", "country"]
    search_fields = ["id"]
    fieldsets = [
        ("Administration", {"fields": ["country", "feed"]}),
        ("Alert Header" , {"fields": ["identifier", "sender", "sent", "status", "msg_type", "source", "scope", "restriction", "addresses", "code", "note", "references", "incidents"]}),
    ]
    inlines = [CapFeedAlertInfoInline]

class CapFeedCountryAdmin(admin.ModelAdmin):
    list_display = ["name", "iso3", "region", "continent"]
    list_filter = ["region", "continent"]
    search_fields = ["name", "iso3"]

class CapFeedFeedAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "url", "format", "polling_interval"]
    list_filter = ["format", "polling_interval"]
    search_fields = ["url", "country"]



admin.site.register(CapFeedAlert, CapFeedAlertAdmin)
admin.site.register(CapFeedContinent)
admin.site.register(CapFeedRegion)
admin.site.register(CapFeedCountry, CapFeedCountryAdmin)
admin.site.register(CapFeedFeed, CapFeedFeedAdmin)
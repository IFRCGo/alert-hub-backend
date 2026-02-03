from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import (
    Admin1,
    Alert,
    AlertAdmin1,
    AlertInfo,
    Continent,
    Country,
    Feed,
    FeedLog,
    LanguageInfo,
    ProcessedAlert,
    Region,
)


class AlertInfoAreaGeocodeAdmin(admin.ModelAdmin):
    list_display = ['alert_info_area', 'value_name', 'value']


class AlertInfoAreaPolygonAdmin(admin.ModelAdmin):
    list_display = ['alert_info_area', 'value']


class AlertInfoAreaCircleAdmin(admin.ModelAdmin):
    list_display = ['alert_info_area', 'value']


class AlertInfoParameterAdmin(admin.ModelAdmin):
    list_display = ['alert_info', 'value_name', 'value']


class AlertInfoAreaAdmin(admin.ModelAdmin):
    list_display = ['alert_info', 'area_desc']


class AlertInfoAdmin(admin.ModelAdmin):
    list_display = ['alert', 'language']
    list_filter = (
        AutocompleteFilterFactory('Feed', 'alert__feed'),
        AutocompleteFilterFactory('Country', 'alert__country'),
    )
    search_fields = ['alert__url']
    fieldsets = [
        ('Administration', {'fields': ['alert']}),
        (
            'Alert Info',
            {
                'fields': [
                    'language',
                    'category',
                    'event',
                    'response_type',
                    'urgency',
                    'severity',
                    'certainty',
                    'audience',
                    'event_code',
                    'effective',
                    'onset',
                    'expires',
                    'sender_name',
                    'headline',
                    'description',
                    'instruction',
                    'web',
                    'contact',
                ]
            },
        ),
    ]


class AlertInfoInline(admin.StackedInline):
    model = AlertInfo
    extra = 0


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['url', 'country', 'feed', 'is_expired', 'sent', 'status', 'msg_type', 'scope']
    list_filter = (
        'is_expired',
        AutocompleteFilterFactory('Feed', 'feed'),
        AutocompleteFilterFactory('Country', 'country'),
    )
    search_fields = ['url']
    fieldsets = [
        ('Administration', {'fields': ['country', 'feed']}),
        (
            'Alert Header',
            {
                'fields': [
                    'identifier',
                    'sender',
                    'sent',
                    'status',
                    'msg_type',
                    'source',
                    'scope',
                    'restriction',
                    'addresses',
                    'code',
                    'note',
                    'references',
                    'incidents',
                ]
            },
        ),
    ]
    inlines = [AlertInfoInline]


@admin.register(Region)
class RegionAdmin(TranslationAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Country)
class CountryAdmin(TranslationAdmin):
    list_display = ['name', 'iso3', 'region', 'continent', 'has_preparedness_messages']
    list_filter = (
        'region',
        'continent',
        'has_preparedness_messages',
    )
    search_fields = ['name', 'iso3']


@admin.register(Admin1)
class Admin1Admin(admin.ModelAdmin):
    list_display = ['name', 'country']
    list_filter = (AutocompleteFilterFactory('Country', 'country'),)
    search_fields = ['name']


class LanguageInfoInline(admin.StackedInline):
    model = LanguageInfo
    extra = 0
    min_num = 1
    validate_min = True

    def get_formset(self, *args, **kwargs):
        return super().get_formset(validate_min=self.validate_min, *args, **kwargs)


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'url', 'format', 'polling_interval']
    list_filter = (
        'format',
        'country__region',
        'enable_polling',
        AutocompleteFilterFactory('Country', 'country'),
    )
    readonly_fields = ("archived_at",)
    search_fields = ['url']
    inlines = [LanguageInfoInline]

    def name(self, obj):
        feed_name = 'unnamed feed'
        try:
            if english_feed := LanguageInfo.objects.filter(feed=obj, language='en').first():
                feed_name = english_feed.name
            elif other_feed := LanguageInfo.objects.filter(feed=obj).first():
                feed_name = other_feed.name
        except Exception as e:
            print(e)
        return feed_name


@admin.register(FeedLog)
class FeedLogAdmin(admin.ModelAdmin):
    list_display = ['exception', 'feed', 'description', 'alert_url', 'timestamp']
    list_filter = (
        'exception',
        AutocompleteFilterFactory('Feed', 'feed'),
    )
    search_fields = ['feed', 'exception', 'alert_url']
    fieldsets = [
        ('Log Context', {'fields': ['feed', 'alert_url', 'timestamp', 'notes']}),
        ('Log Details', {'fields': ['exception', 'error_message', 'description', 'response']}),
    ]


@admin.register(AlertAdmin1)
class AlertAdmin1Admin(admin.ModelAdmin):
    list_display = ['alert', 'admin1']
    list_filter = (
        AutocompleteFilterFactory('Admin1', 'admin1'),
        AutocompleteFilterFactory('Country', 'alert__country'),
    )
    search_fields = ['alert__url', 'admin1__name']


@admin.register(ProcessedAlert)
class ProcessedAlertAdmin(admin.ModelAdmin):
    list_display = ['url', 'feed']
    list_filter = (AutocompleteFilterFactory('Feed', 'feed'),)
    search_fields = ['url']


admin.site.register(Continent)

from django.contrib import admin

from .external_alert_models import (
    CapFeedAdmin1,
    CapFeedAlert,
    CapFeedAlertadmin1,
    CapFeedAlertinfo,
    CapFeedCountry,
)
from .models import Alert, SubscriptionAlerts


class AlertAdmin1Inline(admin.StackedInline):
    model = CapFeedAlertadmin1
    extra = 0


class AlertInfoInline(admin.StackedInline):
    model = CapFeedAlertinfo
    extra = 0


class AlertAdmin(admin.ModelAdmin):
    # using = 'AlertDB'
    list_display = ["id", "sent"]
    search_fields = ["id"]

    inlines = [AlertInfoInline, AlertAdmin1Inline]


admin.site.register(CapFeedAdmin1)
admin.site.register(CapFeedAlert, AlertAdmin)
admin.site.register(CapFeedAlertadmin1)
admin.site.register(CapFeedAlertinfo)
admin.site.register(CapFeedCountry)
admin.site.register(SubscriptionAlerts)
admin.site.register(Alert)

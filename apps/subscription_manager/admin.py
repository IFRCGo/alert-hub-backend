from django.contrib import admin

from apps.cap_feed.models import AlertAdmin1, AlertInfo

from .models import Alert, SubscriptionAlerts


class AlertAdmin1Inline(admin.StackedInline):
    model = AlertAdmin1
    extra = 0


class AlertInfoInline(admin.StackedInline):
    model = AlertInfo
    extra = 0


class AlertAdmin(admin.ModelAdmin):
    # using = 'AlertDB'
    list_display = ["id", "sent"]
    search_fields = ["id"]

    inlines = [AlertInfoInline, AlertAdmin1Inline]


admin.site.register(SubscriptionAlerts)
admin.site.register(Alert)

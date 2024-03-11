from django.contrib import admin

from apps.subscription_manager.models import SubscriptionAlerts
from .models import Subscription


class SubscriptionAlertsInline(admin.StackedInline):
    model = SubscriptionAlerts
    extra = 0


class SubscriptionAdmin(admin.ModelAdmin):
    # using = 'AlertDB'
    list_display = ["id", "subscription_name"]
    search_fields = ["id", "subscription_name"]

    inlines = [SubscriptionAlertsInline]


# Register your models here.
admin.site.register(Subscription)#, SubscriptionAdmin)

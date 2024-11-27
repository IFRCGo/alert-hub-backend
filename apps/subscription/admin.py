from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin

from .models import SubscriptionAlert, UserAlertSubscription


@admin.register(UserAlertSubscription)
class UserAlertSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    search_fields = ("name",)
    autocomplete_fields = ("user",)
    list_filter = (
        AutocompleteFilterFactory("User", "user"),
        "is_active",
    )


@admin.register(SubscriptionAlert)
class SubscriptionAlertAdmin(admin.ModelAdmin):
    list_display = ["subscription", "alert"]
    autocomplete_fields = ["subscription", "alert"]
    list_filter = (AutocompleteFilterFactory("Subscription", "subscription"),)

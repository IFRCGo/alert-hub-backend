from django.utils.functional import cached_property

from apps.cap_feed.dataloaders import CapFeedDataloader
from apps.subscription.dataloaders import SubscriptionDataloader
from apps.user.dataloaders import UserDataLoader


class GlobalDataLoader:

    @cached_property
    def user(self):
        return UserDataLoader()

    @cached_property
    def cap_feed(self):
        return CapFeedDataloader()

    @cached_property
    def subscription(self):
        return SubscriptionDataloader()

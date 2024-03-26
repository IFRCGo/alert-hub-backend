from django.utils.functional import cached_property

from apps.cap_feed.dataloaders import CapFeedDataloader
from apps.user.dataloaders import UserDataLoader


class GlobalDataLoader:

    @cached_property
    def user(self):
        return UserDataLoader()

    @cached_property
    def cap_feed(self):
        return CapFeedDataloader()

import logging

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Feed
from .utils import FeedTaskManager

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Feed)
def create_feed(sender, instance, created, **_):
    if created:
        # NOTE: id is required to create tasks, so using post_save for new
        FeedTaskManager.add_task(instance)
        return
    # NOTE: Update will be handled by update_feed signal


@receiver(pre_save, sender=Feed)
def update_feed(sender, instance, **_):
    if instance.pk is None:
        # NOTE: Create will be handled by create_feed signal
        return

    if instance.is_archived:
        if not instance.archived_at:
            instance.archived_at = timezone.now()
        FeedTaskManager.remove_task(instance)
        return

    instance.archived_at = None
    # TODO: Use enable_polling and is_archived to create/delete the tasks
    FeedTaskManager.add_task(instance)

    # NOTE: pre/post polling_interval is required to update tasks
    existing_feed = Feed.objects.get(pk=instance.pk)
    if existing_feed.polling_interval != instance.polling_interval:
        FeedTaskManager.update_task(instance)


@receiver(post_delete, sender=Feed)
def delete_feed(sender, instance, *args, **kwargs):
    FeedTaskManager.remove_task(instance)

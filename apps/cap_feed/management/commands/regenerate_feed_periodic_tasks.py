from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask

from apps.cap_feed.models import Feed
from apps.cap_feed.utils import FeedTaskManager


class Command(BaseCommand):

    def force_delete_all_tasks(self):
        # TODO: Use INTERNAL_CELERY_TASK_NAME_PREFIX to remove legacy tasks
        deleted = PeriodicTask.objects.filter(
            name__in=[
                # Legacy
                'remove_expired_alerts',
                # Name changed
                'tag_expired_alerts',
                'remove_expired_alert_records',
            ]
        ).delete()
        self.stdout.write(self.style.WARNING(f'Removed {deleted}'))
        deleted = PeriodicTask.objects.filter(name__startswith='poll_feed').delete()
        self.stdout.write(self.style.WARNING(f'Removed {deleted}'))

    def handle(self, *_, **options):
        self.force_delete_all_tasks()
        deleted_count = FeedTaskManager.force_delete_all_tasks()
        self.stdout.write(self.style.WARNING(f'Removing existing feed tasks {deleted_count}'))
        proccessed_feeds = 0
        for feed in Feed.objects.all():
            FeedTaskManager.add_task(feed)
            proccessed_feeds += 1
        self.stdout.write(self.style.SUCCESS(f'Create tasks for {proccessed_feeds} feeds'))

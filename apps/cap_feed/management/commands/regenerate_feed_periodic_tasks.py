from django.core.management.base import BaseCommand

from apps.cap_feed.models import Feed
from apps.cap_feed.utils import FeedTaskManager


class Command(BaseCommand):

    def handle(self, *_, **options):
        deleted_count = FeedTaskManager.force_delete_all_tasks()

        self.stdout.write(self.style.WARNING(f'Removing existing feed tasks count: {deleted_count}'))

        proccessed_feeds = 0
        for feed in Feed.objects.all():
            if not feed.is_archived:
                FeedTaskManager.add_task(feed)
            else:
                FeedTaskManager.remove_task(feed)
            proccessed_feeds += 1

        self.stdout.write(self.style.SUCCESS(f'Create tasks for {proccessed_feeds} feeds'))
        self.stdout.write(f'Total feeds: {Feed.objects.count()}')
        self.stdout.write(f'Active feeds: {Feed.objects.filter(is_archived=False).count()}')
        self.stdout.write(f'Archived feeds: {Feed.objects.filter(is_archived=True).count()}')

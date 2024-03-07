import pytz
from datetime import datetime
from unittest import mock
from io import StringIO
from django.test import TestCase
from django.utils import timezone

from .models import Alert, AlertInfo, Country, Feed
import cap_feed.tasks as tasks
from cap_feed.formats.utils import convert_datetime
from cap_feed.formats.format_handler import get_alerts



class AlertModelTests(TestCase):
    fixtures = ['cap_feed/fixtures/test_data.json']

    def create_alert(self, url='', days=1):
        alert = Alert()
        alert.country = Country.objects.get(pk=1)
        alert.feed = Feed.objects.get(url='test_feed')
        alert.url = url
        alert.identifier = ''
        alert.sender = ''
        alert.sent = timezone.now()
        alert.status = 'Actual'
        alert.msg_type = 'Alert'
        alert.scope = 'Public'

        alert_info = AlertInfo()
        alert_info.alert = alert
        alert_info.category = 'Met'
        alert_info.event = ''
        alert_info.urgency = 'Immediate'
        alert_info.severity = 'Extreme'
        alert_info.certainty = 'Observed'
        alert_info.expires = timezone.now() + timezone.timedelta(days = days)

        alert.save()
        alert_info.save()

        return alert, alert_info

    def test_feed_datetime_converted_to_utc(self):
        """
        Is the iso format cap alert datetime field with timezone offsets processed correctly to utc timezone?
        """
        cap_sent = "2023-06-24T22:00:00-05:00"
        cap_effective = "2023-06-24T22:00:00+00:00"
        cap_onset = "2023-06-24T22:00:00-00:00"
        cap_expires = "2023-06-24T22:00:00+05:00"

        alert = Alert()
        alert.sent = convert_datetime(cap_sent)
        alert_info = AlertInfo()
        alert_info.effective = convert_datetime(cap_effective)
        alert_info.onset = convert_datetime(cap_onset)
        alert_info.expires = convert_datetime(cap_expires)

        utc_sent = datetime(2023, 6, 25, 3, 0, 0, 0, pytz.UTC)
        utc_effective = datetime(2023, 6, 24, 22, 0, 0, 0, pytz.UTC)
        utc_onset = datetime(2023, 6, 24, 22, 0, 0, 0, pytz.UTC)
        utc_expires = datetime(2023, 6, 24, 17, 0, 0, 0, pytz.UTC)

        assert alert.sent == utc_sent
        assert alert_info.effective == utc_effective
        assert alert_info.onset == utc_onset
        assert alert_info.expires == utc_expires

    def test_django_timezone_is_utc(self):
        """
        Is the django timezone set to UTC?
        """
        assert timezone.get_default_timezone_name() == 'UTC'
        assert timezone.get_current_timezone_name() == 'UTC'

    def test_expired_alert_is_removed(self):
        """
        Is an expired alert identified and removed from the database?
        """
        self.create_alert(days=-1)
        previous_alert_count = Alert.objects.count()
        previous_alert_info_count = AlertInfo.objects.count()
        tasks.remove_expired_alerts()
        assert Alert.objects.count() == previous_alert_count - 1
        assert AlertInfo.objects.count() == previous_alert_info_count - 1

    def test_active_alert_is_kept(self):
        """
        Is an active alert identified and kept in the database?
        """
        self.create_alert(days=1)
        previous_alert_count = Alert.objects.count()
        previous_alert_info_count = AlertInfo.objects.count()
        tasks.remove_expired_alerts()
        assert Alert.objects.count() == previous_alert_count
        assert AlertInfo.objects.count() == previous_alert_info_count

    def test_deleted_alert_is_removed(self):
        """
        Is an existing active alert removed from the database when it is deleted from the feed?
        """
        self.create_alert(url='test_url', days=1)
        previous_alert_count = Alert.objects.count()
        previous_alert_info_count = AlertInfo.objects.count()
        with mock.patch('sys.stdout', new = StringIO()) as std_out:
            get_alerts(Feed.objects.get(url="test_feed"), set())
        assert Alert.objects.count() == previous_alert_count - 1
        assert AlertInfo.objects.count() == previous_alert_info_count - 1

    def test_persisting_alert_is_kept(self):
        """
        Is an existing active alert kept in the database when it persists in the feed?
        """
        self.create_alert(url='test_url', days=1)
        previous_alert_count = Alert.objects.count()
        previous_alert_info_count = AlertInfo.objects.count()
        with mock.patch('sys.stdout', new = StringIO()) as std_out:
            get_alerts(Feed.objects.get(url="test_feed"), {'test_url'})
        assert Alert.objects.count() == previous_alert_count
        assert AlertInfo.objects.count() == previous_alert_info_count
        
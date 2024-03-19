import json
from datetime import timedelta
from typing import TYPE_CHECKING

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import IntegrityError, models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from iso639 import iter_langs
from shapely.geometry import MultiPolygon, Polygon

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import ManyRelatedManager


class Continent(models.Model):
    name = models.CharField()

    def __str__(self):
        return self.name


class Region(models.Model):
    name = models.CharField()
    polygon = models.TextField(blank=True, null=True)
    centroid = models.CharField(blank=True, null=True)

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField()
    iso3 = models.CharField(unique=True, validators=[MinValueValidator(3), MaxValueValidator(3)])
    polygon = models.TextField(blank=True, null=True)
    multipolygon = models.TextField(blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE)
    centroid = models.CharField(blank=True, null=True)

    region_id: int
    continent_id: int

    def __str__(self):
        return self.iso3 + ' ' + self.name


@receiver(post_save, sender=Country)
def create_unknown_admin1(sender, instance, created, **kwargs):
    if created:
        Admin1.objects.get_or_create(id=-instance.id, name='Unknown', country=instance)


class Admin1(models.Model):
    name = models.CharField()
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    polygon = models.TextField(blank=True, null=True)
    multipolygon = models.TextField(blank=True, null=True)
    min_latitude = models.FloatField(editable=False, null=True)
    max_latitude = models.FloatField(editable=False, null=True)
    min_longitude = models.FloatField(editable=False, null=True)
    max_longitude = models.FloatField(editable=False, null=True)

    country_id: int

    if TYPE_CHECKING:
        alert_set: ManyRelatedManager['Alert']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.polygon:
            polygon_string = '{"coordinates": ' + str(self.polygon) + '}'
            polygon = json.loads(polygon_string)['coordinates'][0]
            self.min_longitude, self.min_latitude, self.max_longitude, self.max_latitude = Polygon(polygon).bounds
        elif self.multipolygon:
            multipolygon_string = '{"coordinates": ' + str(self.multipolygon) + '}'
            polygon_list = json.loads(multipolygon_string)['coordinates']
            polygons = [Polygon(x[0]) for x in polygon_list]
            self.min_longitude, self.min_latitude, self.max_longitude, self.max_latitude = MultiPolygon(polygons).bounds
        super(Admin1, self).save(*args, **kwargs)


class LanguageInfo(models.Model):
    LANGUAGE_CHOICES = [(lg.pt1, lg.pt1 + ' - ' + lg.name) for lg in iter_langs() if lg.pt1]
    """
    TODO: Move this to textchoices
    Language = models.TextChoices('Language', {
        lg.pt1.upper(): (
            lg.pt1,
            lg.pt1 + ' - ' + lg.name,
        )
        for lg in iter_langs() if lg.pt1
    })
    """

    feed = models.ForeignKey('Feed', on_delete=models.CASCADE)
    name = models.CharField()
    language = models.CharField(blank=True, null=True, choices=LANGUAGE_CHOICES, default='en-US')
    logo = models.CharField(blank=True, null=True)

    feed_id: int


class Feed(models.Model):
    class PoolingInterval(models.IntegerChoices):
        """
        Generated using: range(5, 65, 5):
        """

        I_05 = 5, '5 seconds'
        I_10 = 10, '10 seconds'
        I_15 = 15, '15 seconds'
        I_20 = 20, '20 seconds'
        I_25 = 25, '25 seconds'
        I_30 = 30, '30 seconds'
        I_35 = 35, '35 seconds'
        I_40 = 40, '40 seconds'
        I_45 = 45, '45 seconds'
        I_50 = 50, '50 seconds'
        I_55 = 55, '55 seconds'
        I_60 = 60, '60 seconds'

    class Format(models.TextChoices):
        ATOM = ['atom', 'ATOM']
        RSS = 'rss', 'RSS'
        NWS_US = 'nws_us', 'NWS_US'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        TESTING = 'testing', 'Testing'
        INACTIVE = 'inactive', 'Inactive'
        UNUSABLE = 'unusable', 'Unusable'

    url = models.CharField(unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    format = models.CharField(choices=Format.choices)
    polling_interval = models.IntegerField(choices=PoolingInterval.choices)
    enable_polling = models.BooleanField(default=False)
    enable_rebroadcast = models.BooleanField(default=False)
    official = models.BooleanField(default=False)
    status = models.CharField(choices=Status.choices, default=Status.ACTIVE)
    author_name = models.CharField(default='')
    author_email = models.CharField(default='')

    notes = models.TextField(blank=True, default='')

    country_id: int

    __old_polling_interval = None
    __old_url = None

    def __init__(self, *args, **kwargs):
        super(Feed, self).__init__(*args, **kwargs)
        self.__old_polling_interval = self.polling_interval
        self.__old_url = self.url

    def __str__(self):
        return self.url

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self._state.adding:
            add_task(self)
        else:
            update_task(self, self.__old_url, self.__old_polling_interval)
        super(Feed, self).save(force_insert, force_update, *args, **kwargs)


class ProcessedAlert(models.Model):
    # Set expire time to 1 week
    @staticmethod
    def default_expire():
        return timezone.now() + timedelta(weeks=1)

    url = models.CharField(unique=True)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    expires = models.DateTimeField(default=default_expire)

    def __str__(self):
        return self.url


class Alert(models.Model):
    class Status(models.TextChoices):
        ACTUAL = 'Actual', 'Actual'
        EXERCISE = 'Exercise', 'Exercise'
        SYSTEM = 'System', 'System'
        TEST = 'Test', 'Test'
        DRAFT = 'Draft', 'Draft'

    class MsgType(models.TextChoices):
        ALERT = 'Alert', 'Alert'
        UPDATE = 'Update', 'Update'
        CANCEL = 'Cancel', 'Cancel'
        ACK = 'Ack', 'Ack'
        ERROR = 'Error', 'Error'

    class Scope(models.TextChoices):  # XXX: Not used, maybe we need to use this in scope field?
        PUBLIC = 'Public', 'Public'
        RESTRICTED = 'Restricted', 'Restricted'
        PRIVATE = 'Private', 'Private'

    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    admin1s = models.ManyToManyField(Admin1, through='AlertAdmin1')
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    url = models.CharField(unique=True)

    identifier = models.CharField()
    sender = models.CharField()
    sent = models.DateTimeField()
    status = models.CharField(choices=Status.choices)
    msg_type = models.CharField(choices=MsgType.choices)
    source = models.CharField(blank=True, null=True, default=None)
    scope = models.CharField(blank=True, null=True, default=None)
    restriction = models.CharField(blank=True, null=True, default=None)
    addresses = models.TextField(blank=True, null=True, default=None)
    code = models.CharField(blank=True, null=True, default=None)
    note = models.TextField(blank=True, null=True, default=None)
    references = models.TextField(blank=True, null=True, default=None)
    incidents = models.TextField(blank=True, null=True, default=None)

    country_id: int
    feed_id: int

    if TYPE_CHECKING:
        alertinfo_set: ManyRelatedManager['AlertInfo']
    __all_info_added = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__all_info_added = False

    def __str__(self):
        return self.url

    def info_has_been_added(self):
        self.__all_info_added = True

    def all_info_are_added(self):
        return self.__all_info_added


class AlertAdmin1(models.Model):
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    admin1 = models.ForeignKey(Admin1, on_delete=models.CASCADE)

    alert_id: int
    admin1_id: int

    # TODO: Add unique constraint


class AlertInfo(models.Model):
    # To dynamically set default expire time
    @staticmethod
    def default_expire():
        return timezone.now() + timedelta(days=1)

    class Category(models.TextChoices):
        GEO = 'Geo', 'Geo'
        MET = 'Met', 'Met'
        SAFETY = 'Safety', 'Safety'
        SECURITY = 'Security', 'Security'
        RESCUE = 'Rescue', 'Rescue'
        FIRE = 'Fire', 'Fire'
        HEALTH = 'Health', 'Health'
        ENV = 'Env', 'Env'
        TRANSPORT = 'Transport', 'Transport'
        INFRA = 'Infra', 'Infra'
        CBRNE = 'CBRNE', 'CBRNE'
        OTHER = 'Other', 'Other'

    class ResponseType(models.TextChoices):
        SHELTER = 'Shelter', 'Shelter'
        EVACUATE = 'Evacuate', 'Evacuate'
        PREPARE = 'Prepare', 'Prepare'
        EXECUTE = 'Execute', 'Execute'
        AVOID = 'Avoid', 'Avoid'
        MONITOR = 'Monitor', 'Monitor'
        ASSESS = 'Assess', 'Assess'
        ALLCLEAR = 'AllClear', 'AllClear'
        NONE = 'None', 'None'

    class Urgency(models.TextChoices):
        IMMEDIATE = 'Immediate', 'Immediate'
        EXPECTED = 'Expected', 'Expected'
        FUTURE = 'Future', 'Future'
        PAST = 'Past', 'Past'
        UNKNOWN = 'Unknown', 'Unknown'

    class Severity(models.TextChoices):
        EXTREME = 'Extreme', 'Extreme'
        SEVERE = 'Severe', 'Severe'
        MODERATE = 'Moderate', 'Moderate'
        MINOR = 'Minor', 'Minor'
        UNKNOWN = 'Unknown', 'Unknown'

    class Certainty(models.TextChoices):
        OBSERVED = 'Observed', 'Observed'
        LIKELY = 'Likely', 'Likely'
        POSSIBLE = 'Possible', 'Possible'
        UNLIKELY = 'Unlikely', 'Unlikely'
        UNKNOWN = 'Unknown', 'Unknown'

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='infos')

    language = models.CharField(blank=True, default='en-US')
    category = models.CharField(choices=Category.choices)
    event = models.CharField()
    response_type = models.CharField(choices=ResponseType.choices, blank=True, null=True, default=None)
    urgency = models.CharField(choices=Urgency.choices)
    severity = models.CharField(choices=Severity.choices)
    certainty = models.CharField(choices=Certainty.choices)
    audience = models.CharField(blank=True, null=True, default=None)
    event_code = models.CharField(blank=True, null=True, default=None)
    # effective = models.DateTimeField(default=Alert.objects.get(pk=alert).sent)
    effective = models.DateTimeField(blank=True, default=timezone.now)
    onset = models.DateTimeField(blank=True, null=True)
    expires = models.DateTimeField(blank=True, null=True, default=default_expire)
    sender_name = models.CharField(blank=True, null=True, default=None)
    headline = models.CharField(blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    instruction = models.TextField(blank=True, null=True, default=None)
    web = models.URLField(blank=True, null=True, default=None)
    contact = models.CharField(blank=True, null=True, default=None)
    parameter = models.CharField(blank=True, null=True, default=None)

    alert_id: int

    def __str__(self):
        return str(self.alert) + ' ' + self.language


class AlertInfoParameter(models.Model):
    alert_info = models.ForeignKey(AlertInfo, on_delete=models.CASCADE)

    value_name = models.CharField()
    value = models.TextField()

    alert_info_id: int

    def to_dict(self):
        alert_info_parameter_dict = dict()
        alert_info_parameter_dict['value_name'] = self.value_name
        alert_info_parameter_dict['value'] = self.value
        return alert_info_parameter_dict


class AlertInfoArea(models.Model):
    alert_info = models.ForeignKey(AlertInfo, on_delete=models.CASCADE)

    area_desc = models.TextField()
    altitude = models.CharField(blank=True, null=True, default=None)
    ceiling = models.CharField(blank=True, null=True, default=None)

    alert_info_id: int

    def __str__(self):
        return str(self.alert_info) + ' ' + self.area_desc


class AlertInfoAreaPolygon(models.Model):
    alert_info_area = models.ForeignKey(AlertInfoArea, on_delete=models.CASCADE)

    value = models.TextField()

    alert_info_area_id: int

    def to_dict(self):
        alert_info_area_ploygon_dict = dict()
        alert_info_area_ploygon_dict['value'] = self.value
        return alert_info_area_ploygon_dict


class AlertInfoAreaCircle(models.Model):
    alert_info_area = models.ForeignKey(AlertInfoArea, on_delete=models.CASCADE)

    value = models.TextField()

    alert_info_area_id: int

    def to_dict(self):
        alert_info_area_circle_dict = dict()
        alert_info_area_circle_dict['value'] = self.value
        return alert_info_area_circle_dict


class AlertInfoAreaGeocode(models.Model):
    alert_info_area = models.ForeignKey(AlertInfoArea, on_delete=models.CASCADE)

    value_name = models.CharField()
    value = models.CharField()

    alert_info_area_id: int

    def to_dict(self):
        alert_info_area_geocode_dict = dict()
        alert_info_area_geocode_dict['value_name'] = self.value_name
        alert_info_area_geocode_dict['value'] = self.value
        return alert_info_area_geocode_dict


class FeedLog(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    exception = models.CharField(default='exception')
    error_message = models.TextField(default='')
    description = models.TextField(default='')
    response = models.TextField(default='')
    alert_url = models.CharField(blank=True, default='')
    timestamp = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, default='')

    class Meta:  # pyright: ignore [reportIncompatibleVariableOverride]
        constraints = [
            models.UniqueConstraint(fields=['alert_url', 'description'], name="unique_alert_error"),
        ]

    def save(self, *args, **kwargs):
        FeedLog.objects.filter(feed=self.feed, timestamp__lt=timezone.now() - timedelta(weeks=2)).delete()
        try:
            super(FeedLog, self).save(*args, **kwargs)
        except IntegrityError:
            pass


# Add task to poll feed
def add_task(feed):
    interval = feed.polling_interval
    interval_schedule = IntervalSchedule.objects.filter(every=interval, period='seconds').first()
    if interval_schedule is None:
        interval_schedule = IntervalSchedule.objects.create(every=interval, period='seconds')
        interval_schedule.save()
    # Create a new PeriodicTask
    try:
        new_task = PeriodicTask.objects.create(
            interval=interval_schedule,
            name='poll_feed_' + feed.url,
            task='apps.cap_feed.tasks.poll_feed',
            start_time=timezone.now(),
            kwargs=json.dumps({"url": feed.url}),
        )
        new_task.save()
    except Exception as e:
        print('Error while adding new PeriodicTask', e)


# Removes task to poll feed
def remove_task(feed):
    try:
        existing_task = PeriodicTask.objects.get(name='poll_feed_' + feed.url)
        existing_task.delete()
    except PeriodicTask.DoesNotExist as e:
        print('Error while removing unknown PeriodicTask', e)


# Update task to poll feed
def update_task(feed, old_url, old_interval):
    if feed.url != old_url or feed.polling_interval != old_interval:
        remove_task(feed)
        add_task(feed)

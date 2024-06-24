from datetime import timedelta
from typing import TYPE_CHECKING

from django.contrib.gis.db import models as gid_models
from django.contrib.gis.geos import GEOSGeometry, Point, Polygon
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import IntegrityError, models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from iso639 import iter_langs

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import ManyRelatedManager


# To dynamically set default expire time
def alert_info_default_expire():
    return timezone.now() + timedelta(days=1)


def processed_alert_default_expire():
    return timezone.now() + timedelta(weeks=1)


class Continent(models.Model):
    name = models.CharField()

    def __str__(self):
        return self.name


class Region(models.Model):
    ifrc_go_id = models.IntegerField(unique=True, null=True, editable=False)
    name = models.CharField()
    bbox = gid_models.PolygonField(srid=4326, blank=True, null=True)

    def __str__(self):
        return self.name


class Country(models.Model):
    ifrc_go_id = models.IntegerField(unique=True, null=True, editable=False)
    name = models.CharField()
    iso3 = models.CharField(unique=True, validators=[MinValueValidator(3), MaxValueValidator(3)])
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    bbox = gid_models.PolygonField(srid=4326, blank=True, null=True)

    # XXX: Not used anywhere right now, maybe we can remove this. Need to confirm first
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE, null=True, blank=True)

    region_id: int
    continent_id: int | None

    def __str__(self):
        return self.iso3 + ' ' + self.name


@receiver(post_save, sender=Country)
def create_unknown_admin1(sender, instance, created, **kwargs):
    if created:
        Admin1.objects.get_or_create(id=-instance.id, name='Unknown', country=instance)


class Admin1(models.Model):
    ifrc_go_id = models.IntegerField(unique=True, null=True, editable=False)
    name = models.CharField()
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    bbox = gid_models.PolygonField(srid=4326, blank=True, null=True)
    geometry = gid_models.GeometryField(null=True, blank=True, default=None)

    country_id: int

    if TYPE_CHECKING:
        alert_set: ManyRelatedManager['Alert']

    def __str__(self):
        return self.name


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

        I_05 = 5, _('5 seconds')
        I_10 = 10, _('10 seconds')
        I_15 = 15, _('15 seconds')
        I_20 = 20, _('20 seconds')
        I_25 = 25, _('25 seconds')
        I_30 = 30, _('30 seconds')
        I_35 = 35, _('35 seconds')
        I_40 = 40, _('40 seconds')
        I_45 = 45, _('45 seconds')
        I_50 = 50, _('50 seconds')
        I_55 = 55, _('55 seconds')
        I_60 = 60, _('60 seconds')
        I_10m = 600, _('10 minutes')

    class Format(models.TextChoices):
        ATOM = 'atom', _('ATOM')
        RSS = 'rss', _('RSS')
        NWS_US = 'nws_us', _('NWS_US')

    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        TESTING = 'testing', _('Testing')
        INACTIVE = 'inactive', _('Inactive')
        UNUSABLE = 'unusable', _('Unusable')

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

    def __init__(self, *args, **kwargs):
        super(Feed, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.url


class ProcessedAlert(models.Model):
    url = models.CharField(unique=True)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    expires = models.DateTimeField(default=processed_alert_default_expire)

    def __str__(self):
        return self.url


class Alert(models.Model):
    class Status(models.TextChoices):
        ACTUAL = 'Actual', _('Actual')
        EXERCISE = 'Exercise', _('Exercise')
        SYSTEM = 'System', _('System')
        TEST = 'Test', _('Test')
        DRAFT = 'Draft', _('Draft')

    class MsgType(models.TextChoices):
        ALERT = 'Alert', _('Alert')
        UPDATE = 'Update', _('Update')
        CANCEL = 'Cancel', _('Cancel')
        ACK = 'Ack', _('Ack')
        ERROR = 'Error', _('Error')

    class Scope(models.TextChoices):  # XXX: Not used, maybe we need to use this in scope field?
        PUBLIC = 'Public', _('Public')
        RESTRICTED = 'Restricted', _('Restricted')
        PRIVATE = 'Private', _('Private')

    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    admin1s = models.ManyToManyField(Admin1, through='AlertAdmin1')
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    url = models.CharField(unique=True)

    # This is updated by the system to filter out is_expired
    is_expired = models.BooleanField(default=False)

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

    @classmethod
    def get_queryset(cls) -> models.QuerySet:
        return cls.objects.filter(is_expired=False)

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
    class Category(models.TextChoices):
        GEO = 'Geo', _('Geo')
        MET = 'Met', _('Met')
        SAFETY = 'Safety', _('Safety')
        SECURITY = 'Security', _('Security')
        RESCUE = 'Rescue', _('Rescue')
        FIRE = 'Fire', _('Fire')
        HEALTH = 'Health', _('Health')
        ENV = 'Env', _('Env')
        TRANSPORT = 'Transport', _('Transport')
        INFRA = 'Infra', _('Infra')
        CBRNE = 'CBRNE', _('CBRNE')
        OTHER = 'Other', _('Other')

    class ResponseType(models.TextChoices):
        SHELTER = 'Shelter', _('Shelter')
        EVACUATE = 'Evacuate', _('Evacuate')
        PREPARE = 'Prepare', _('Prepare')
        EXECUTE = 'Execute', _('Execute')
        AVOID = 'Avoid', _('Avoid')
        MONITOR = 'Monitor', _('Monitor')
        ASSESS = 'Assess', _('Assess')
        ALLCLEAR = 'AllClear', _('AllClear')
        NONE = 'None', _('None')

    class Urgency(models.TextChoices):
        IMMEDIATE = 'Immediate', _('Immediate')
        EXPECTED = 'Expected', _('Expected')
        FUTURE = 'Future', _('Future')
        PAST = 'Past', _('Past')
        UNKNOWN = 'Unknown', _('Unknown')

    class Severity(models.TextChoices):
        EXTREME = 'Extreme', _('Extreme')
        SEVERE = 'Severe', _('Severe')
        MODERATE = 'Moderate', _('Moderate')
        MINOR = 'Minor', _('Minor')
        UNKNOWN = 'Unknown', _('Unknown')

    class Certainty(models.TextChoices):
        OBSERVED = 'Observed', _('Observed')
        LIKELY = 'Likely', _('Likely')
        POSSIBLE = 'Possible', _('Possible')
        UNLIKELY = 'Unlikely', _('Unlikely')
        UNKNOWN = 'Unknown', _('Unknown')

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
    expires = models.DateTimeField(blank=True, null=True, default=alert_info_default_expire)
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

    @property
    def value_geojson(self) -> GEOSGeometry | None:
        """
        NOTE: Value have data something like "50.532,55.692 50.905,56.234 50.902,56.356 51.075,56.53 ...."
        """
        try:
            points = [point.split(',') for point in self.value.split(' ')]
            return Polygon([Point(float(point[1]), float(point[0])) for point in points])
        except Exception:
            return

    def to_dict(self):
        alert_info_area_ploygon_dict = dict()
        alert_info_area_ploygon_dict['value'] = self.value
        return alert_info_area_ploygon_dict


class AlertInfoAreaCircle(models.Model):
    alert_info_area = models.ForeignKey(AlertInfoArea, on_delete=models.CASCADE)

    value = models.TextField()

    alert_info_area_id: int

    # NOTE: Circle can't be drawn using Geojson. A polygon needs to be created which holds large data then raw value

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

    class Meta:  # type: ignore [reportIncompatibleVariableOverride]
        constraints = [
            models.UniqueConstraint(fields=['alert_url', 'description'], name="unique_alert_error"),
        ]

    def save(self, *args, **kwargs):
        FeedLog.objects.filter(feed=self.feed, timestamp__lt=timezone.now() - timedelta(weeks=2)).delete()
        try:
            super(FeedLog, self).save(*args, **kwargs)
        except IntegrityError:
            pass

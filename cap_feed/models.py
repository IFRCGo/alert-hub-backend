import json
from datetime import timedelta
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, IntegrityError
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from django_celery_beat.models import PeriodicTask
from shapely.geometry import Polygon, MultiPolygon



class Continent(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Region(models.Model):
    name = models.CharField(max_length=255)
    polygon = models.TextField(blank=True, default='')
    centroid = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=255)
    iso3 = models.CharField(unique=True, validators=[MinValueValidator(3), MaxValueValidator(3)])
    polygon = models.TextField(blank=True, default='')
    multipolygon = models.TextField(blank=True, default='')
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE)
    centroid = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return self.iso3 + ' ' + self.name
    
class District(models.Model):
    name = models.CharField(max_length=255)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    polygon = models.TextField(blank=True, null=True)
    multipolygon = models.TextField(blank=True, null=True)
    min_latitude = models.FloatField(editable=False, null=True)
    max_latitude = models.FloatField(editable=False, null=True)
    min_longitude = models.FloatField(editable=False, null=True)
    max_longitude = models.FloatField(editable=False, null=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.polygon:
            polygon = json.loads(self.polygon)['coordinates'][0]
            self.min_longitude, self.min_latitude, self.max_longitude, self.max_latitude = Polygon(polygon).bounds
        elif self.multipolygon:
            polygon_list = json.loads(self.multipolygon)['coordinates']
            polygons = [Polygon(x[0]) for x in polygon_list]
            self.min_longitude, self.min_latitude, self.max_longitude, self.max_latitude = MultiPolygon(polygons).bounds
        super(District, self).save(*args, **kwargs)

class Feed(models.Model):
    INTERVAL_CHOICES = []
    for interval in range(10, 60, 5):
        INTERVAL_CHOICES.append((interval, f"{interval} seconds"))

    FORMAT_CHOICES = [
        ('meteoalarm', 'meteoalarm'),
        ('aws', 'aws'),
        ('nws_us', 'nws_us'),
        ('meteo_ru', 'meteo_ru')
    ]
    name = models.CharField(max_length=255)
    url = models.CharField(primary_key=True, max_length=255)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    format = models.CharField(choices=FORMAT_CHOICES)
    polling_interval = models.IntegerField(choices=INTERVAL_CHOICES)
    atom = models.CharField(editable=False, default='http://www.w3.org/2005/Atom')
    cap = models.CharField(editable=False, default='urn:oasis:names:tc:emergency:cap:1.2')
    notes = models.TextField(blank=True, default='')
    
    __old_polling_interval = None
    __old_url = None

    def __init__(self, *args, **kwargs):
        super(Feed, self).__init__(*args, **kwargs)
        self.__old_polling_interval = self.polling_interval
        self.__old_url = self.url

    def __str__(self):
        name = self.name
        return name

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self._state.adding:
            add_task(self)
        else:
            update_task(self, self.__old_url, self.__old_polling_interval)
        super(Feed, self).save(force_insert, force_update, *args, **kwargs)
    
class Alert(models.Model):
    STATUS_CHOICES = [
        ('Actual', 'Actual'),
        ('Exercise', 'Exercise'),
        ('System', 'System'),
        ('Test', 'Test'),
        ('Draft', 'Draft')
    ]

    MSG_TYPE_CHOICES = [
        ('Alert', 'Alert'),
        ('Update', 'Update'),
        ('Cancel', 'Cancel'),
        ('Ack', 'Ack'),
        ('Error', 'Error')
    ]

    SCOPE_CHOICES = [
        ('Public', 'Public'),
        ('Restricted', 'Restricted'),
        ('Private', 'Private')
    ]

    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    districts = models.ManyToManyField(District, through='AlertDistrict')
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    url = models.CharField(max_length=255, unique=True)

    identifier = models.CharField(max_length=255)
    sender = models.CharField(max_length=255)
    sent = models.DateTimeField()
    status = models.CharField(choices = STATUS_CHOICES)
    msg_type = models.CharField(choices = MSG_TYPE_CHOICES)
    source = models.CharField(max_length=255, blank=True, default='')
    scope = models.CharField(choices = SCOPE_CHOICES)
    restriction = models.CharField(max_length=255, blank=True, default='')
    addresses = models.TextField(blank=True, default='')
    code = models.CharField(max_length=255, blank=True, default='')
    note = models.TextField(blank=True, default='')
    references = models.TextField(blank=True, default='')
    incidents = models.TextField(blank=True, default='')

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

    # This method will be used for serialization of alert object to be cached into Redis.
    def to_dict(self):
        alert_dict = dict()
        alert_dict['url'] = self.url
        alert_dict['identifier'] = self.identifier
        alert_dict['source'] = self.source
        alert_dict['country'] = self.country.name
        alert_dict['iso3'] = self.country.iso3

        info_list = []
        for info in self.info.all():
            info_list.append(info.to_dict())
        alert_dict['info'] = info_list
        return alert_dict

    # This method will be used for serialization of alert object to be transferred by websocket.
    def alert_to_be_transferred_to_dict(self):
        alert_dict = dict()
        alert_dict['url'] = self.url
        alert_dict['country_name'] = self.country.name
        alert_dict['country_id'] = self.country.id
        alert_dict['feed_url'] = self.feed.url
        alert_dict['scope'] = self.scope

        first_info = self.info.first()
        if first_info != None:
            alert_dict['urgency'] = first_info.urgency
            alert_dict['severity'] = first_info.severity
            alert_dict['certainty'] = first_info.certainty

        info_list = []
        for info in self.info.all():
            info_list.append(info.alert_info_to_be_transferred_to_dict())
        alert_dict['info'] = info_list

        return alert_dict
    
class AlertDistrict(models.Model):
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.CASCADE)

class AlertCacheEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Alert):
            return obj.to_dict()

        return super().default(obj)

class AlertTransferEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Alert):
            return obj.alert_to_be_transferred_to_dict()

        return super().default(obj)
    
class AlertInfo(models.Model):
    # To dynamically set default expire time
    def default_expire():
        return timezone.now() + timedelta(days=1)

    CATEGORY_CHOICES = [
        ('Geo', 'Geo'),
        ('Met', 'Met'),
        ('Safety', 'Safety'),
        ('Security', 'Security'),
        ('Rescue', 'Rescue'),
        ('Fire', 'Fire'),
        ('Health', 'Health'),
        ('Env', 'Env'),
        ('Transport', 'Transport'),
        ('Infra', 'Infra'),
        ('CBRNE', 'CBRNE'),
        ('Other', 'Other')
    ]

    RESPONSE_TYPE_CHOICES = [
        ('Shelter', 'Shelter'),
        ('Evacuate', 'Evacuate'),
        ('Prepare', 'Prepare'),
        ('Execute', 'Execute'),
        ('Avoid', 'Avoid'),
        ('Monitor', 'Monitor'),
        ('Assess', 'Assess'),
        ('AllClear', 'AllClear'),
        ('None', 'None')
    ]

    URGENCY_CHOICES = [
        ('Immediate', 'Immediate'),
        ('Expected', 'Expected'),
        ('Future', 'Future'),
        ('Past', 'Past'),
        ('Unknown', 'Unknown')
    ]

    SEVERITY_CHOICES = [
        ('Extreme', 'Extreme'),
        ('Severe', 'Severe'),
        ('Moderate', 'Moderate'),
        ('Minor', 'Minor'),
        ('Unknown', 'Unknown')
    ]

    CERTAINTY_CHOICES = [
        ('Observed', 'Observed'),
        ('Likely', 'Likely'),
        ('Possible', 'Possible'),
        ('Unlikely', 'Unlikely'),
        ('Unknown', 'Unknown')
    ]

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="info")
    
    language = models.CharField(max_length=255, blank=True, default='en-US')
    category = models.CharField(choices = CATEGORY_CHOICES)
    event = models.CharField(max_length=255)
    response_type = models.CharField(choices = RESPONSE_TYPE_CHOICES, blank=True, default='')
    urgency = models.CharField(choices = URGENCY_CHOICES)
    severity = models.CharField(choices = SEVERITY_CHOICES)
    certainty = models.CharField(choices = CERTAINTY_CHOICES)
    audience = models.CharField(blank=True, default='')
    event_code = models.CharField(max_length=255, blank=True, default='')
    #effective = models.DateTimeField(default=Alert.objects.get(pk=alert).sent)
    effective = models.DateTimeField(blank=True, default=timezone.now)
    onset = models.DateTimeField(blank=True, null=True)
    expires = models.DateTimeField(blank=True, default=default_expire)
    sender_name = models.CharField(max_length=255, blank=True, default='')
    headline = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, null=True, default=None)
    instruction = models.TextField(blank=True, null=True, default=None)
    web = models.URLField(blank=True, null=True)
    contact = models.CharField(max_length=255, blank=True, default='')
    parameter = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return str(self.alert) + ' ' + self.language

    def to_dict(self):
        alert_info_dict = dict()
        alert_info_dict['language'] = self.language
        alert_info_dict['category'] = self.category
        alert_info_dict['event'] = self.event
        alert_info_dict['urgency'] = self.urgency
        alert_info_dict['severity'] = self.severity
        alert_info_dict['certainty'] = self.certainty
        alert_info_dict['expires'] = str(self.expires)
        alert_info_dict['sender_name'] = self.sender_name
        alert_info_dict['headline'] = self.headline
        alert_info_dict['description'] = self.description
        alert_info_dict['instruction'] = self.instruction

        area_set = self.alertinfoarea_set.all()
        area_list = []
        for area in area_set:
            area_list.append(area.to_dict())
        if len(area_list) != 0:
            alert_info_dict['area'] = area_list

        return alert_info_dict

    def alert_info_to_be_transferred_to_dict(self):
        alert_info_dict = dict()
        alert_info_dict['language'] = self.language
        alert_info_dict['category'] = self.category
        alert_info_dict['headline'] = self.headline
        alert_info_dict['description'] = self.description
        alert_info_dict['instruction'] = self.instruction
        return alert_info_dict

class AlertInfoParameter(models.Model):
    alert_info = models.ForeignKey(AlertInfo, on_delete=models.CASCADE)

    value_name = models.CharField(max_length=255)
    value = models.TextField()

    def to_dict(self):
        alert_info_parameter_dict = dict()
        alert_info_parameter_dict['value_name'] = self.value_name
        alert_info_parameter_dict['value'] = self.value
        return alert_info_parameter_dict

class AlertInfoArea(models.Model):
    alert_info = models.ForeignKey(AlertInfo, on_delete=models.CASCADE)

    area_desc = models.TextField()
    altitude = models.CharField(blank=True, default='')
    ceiling = models.CharField(blank=True, default='')

    def __str__(self):
        return str(self.alert_info) + ' ' + self.area_desc

    def to_dict(self):
        alert_info_area_dict = dict()
        alert_info_area_dict['area_desc'] = self.area_desc
        alert_info_area_dict['altitude'] = self.altitude
        alert_info_area_dict['ceiling'] = self.ceiling

        area_polygon_set = self.alertinfoareapolygon_set.all()
        area_polygon_list = []
        for area_polygon in area_polygon_set:
            area_polygon_list.append(area_polygon.to_dict())
        if len(area_polygon_list) != 0:
            alert_info_area_dict['polygon'] = area_polygon_list

        area_circle_set = self.alertinfoareacircle_set.all()
        area_circle_list = []
        for area_circle in area_circle_set:
            area_circle_list.append(area_circle.to_dict())
        if len(area_circle_list) != 0:
            alert_info_area_dict['circle'] = area_circle_list

        area_geocode_set = self.alertinfoareageocode_set.all()
        area_geocode_list = []
        for area_geocode in area_geocode_set:
            area_geocode_list.append(area_geocode.to_dict())
        if len(area_geocode_list) != 0:
            alert_info_area_dict['geocode'] = area_geocode_list

        return alert_info_area_dict

class AlertInfoAreaPolygon(models.Model):
    alert_info_area = models.ForeignKey(AlertInfoArea, on_delete=models.CASCADE)

    value = models.TextField()

    def to_dict(self):
        alert_info_area_ploygon_dict = dict()
        alert_info_area_ploygon_dict['value'] = self.value
        return alert_info_area_ploygon_dict

class AlertInfoAreaCircle(models.Model):
    alert_info_area = models.ForeignKey(AlertInfoArea, on_delete=models.CASCADE)

    value = models.TextField()

    def to_dict(self):
        alert_info_area_circle_dict = dict()
        alert_info_area_circle_dict['value'] = self.value
        return alert_info_area_circle_dict

class AlertInfoAreaGeocode(models.Model):
    alert_info_area = models.ForeignKey(AlertInfoArea, on_delete=models.CASCADE)

    value_name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def to_dict(self):
        alert_info_area_geocode_dict = dict()
        alert_info_area_geocode_dict['value_name'] = self.value_name
        alert_info_area_geocode_dict['value'] = self.value
        return alert_info_area_geocode_dict
    
class FeedLog(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    exception = models.CharField(max_length=255, default='exception')
    error_message = models.TextField(default='')
    description = models.TextField(default='')
    response = models.TextField(default='')
    alert_url = models.CharField(max_length=255, blank=True, default='')
    timestamp = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, default='')

    class Meta:
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
            interval = interval_schedule,
            name = 'poll_feed_' + feed.url,
            task = 'cap_feed.tasks.poll_feed',
            start_time = timezone.now(),
            kwargs = json.dumps({"url": feed.url}),
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
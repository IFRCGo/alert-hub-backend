from django.db import models

class CapFeedAlert(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    identifier = models.CharField(max_length=255)
    sender = models.CharField(max_length=255)
    sent = models.DateTimeField()
    status = models.CharField()
    msg_type = models.CharField()
    source = models.CharField(max_length=255)
    scope = models.CharField()
    restriction = models.CharField(max_length=255)
    addresses = models.TextField()
    code = models.CharField(max_length=255)
    note = models.TextField()
    references = models.TextField()
    incidents = models.TextField()
    country = models.ForeignKey('CapFeedCountry', models.DO_NOTHING)
    feed = models.ForeignKey('CapFeedFeed', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cap_feed_alert'

    def to_dict(self):
        alert_dict = dict()
        #alert_dict['id'] = self.id
        alert_dict['identifier'] = self.identifier
        alert_dict['sender'] = self.sender
        alert_dict['sent'] = str(self.sent)
        alert_dict['status'] = self.status
        alert_dict['msg_type'] = self.msg_type
        alert_dict['source'] = self.source
        alert_dict['scope'] = self.scope
        alert_dict['restriction'] = self.restriction
        alert_dict['addresses'] = self.addresses
        alert_dict['code'] = self.code
        alert_dict['note'] = self.note
        alert_dict['references'] = self.references
        alert_dict['incidents'] = self.incidents
        alert_dict['feed_url'] = self.feed.url
        alert_dict['feed_format'] = self.feed.format
        alert_dict['country'] = self.country.name
        alert_dict['iso3'] = self.country.iso3
        alert_dict['country_polygon'] = self.country.polygon

        info_list = []
        for info in self.capfeedalertinfo_set.all():
            info_list.append(info.to_dict())
        alert_dict['info'] = info_list
        return alert_dict


class CapFeedAlertInfo(models.Model):
    id = models.BigAutoField(primary_key=True)
    language = models.CharField(max_length=255)
    category = models.CharField()
    event = models.CharField(max_length=255)
    response_type = models.CharField()
    urgency = models.CharField()
    severity = models.CharField()
    certainty = models.CharField()
    audience = models.CharField()
    event_code = models.CharField(max_length=255)
    effective = models.DateTimeField()
    onset = models.DateTimeField(blank=True, null=True)
    expires = models.DateTimeField()
    sender_name = models.CharField(max_length=255)
    headline = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    instruction = models.TextField(blank=True, null=True)
    web = models.CharField(max_length=200, blank=True, null=True)
    contact = models.CharField(max_length=255)
    parameter = models.CharField(max_length=255)
    alert = models.ForeignKey(CapFeedAlert, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cap_feed_alertinfo'

    def to_dict(self):
        alert_info_dict = dict()
        alert_info_dict['language'] = self.language
        alert_info_dict['category'] = self.category
        alert_info_dict['event'] = self.event
        alert_info_dict['response_type'] = self.response_type
        alert_info_dict['urgency'] = self.urgency
        alert_info_dict['severity'] = self.severity
        alert_info_dict['certainty'] = self.certainty
        alert_info_dict['audience'] = self.audience
        alert_info_dict['event_code'] = self.event_code
        alert_info_dict['effective'] = str(self.effective)
        alert_info_dict['onset'] = str(self.onset)
        alert_info_dict['expires'] = str(self.expires)
        alert_info_dict['sender_name'] = self.sender_name
        alert_info_dict['headline'] = self.headline
        alert_info_dict['description'] = self.description
        alert_info_dict['instruction'] = self.instruction
        alert_info_dict['web'] = self.web
        alert_info_dict['contact'] = self.contact
        parameter_set = self.capfeedalertinfoparameter_set.all()
        parameter_list = []
        for parameter in parameter_set:
            parameter_list.append(parameter.to_dict())
        if len(parameter_list) != 0:
            alert_info_dict['parameter'] = parameter_list
        area_set = self.capfeedalertinfoarea_set.all()

        area_list = []
        for area in area_set:
            area_list.append(area.to_dict())
        if len(area_list) != 0:
            alert_info_dict['area'] = area_list
        return alert_info_dict


class CapFeedAlertInfoArea(models.Model):
    id = models.BigAutoField(primary_key=True)
    area_desc = models.TextField()
    altitude = models.CharField()
    ceiling = models.CharField()
    alert_info = models.ForeignKey(CapFeedAlertInfo, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cap_feed_alertinfoarea'

    def to_dict(self):
        alert_info_area_dict = dict()
        alert_info_area_dict['area_desc'] = self.area_desc
        alert_info_area_dict['altitude'] = self.altitude
        alert_info_area_dict['ceiling'] = self.ceiling

        area_polygon_set = self.capfeedalertinfoareapolygon_set.all()
        area_polygon_list = []
        for area_polygon in area_polygon_set:
            area_polygon_list.append(area_polygon.to_dict())
        if len(area_polygon_list) != 0:
            alert_info_area_dict['polygon'] = area_polygon_list

        area_circle_set = self.capfeedalertinfoareacircle_set.all()
        area_circle_list = []
        for area_circle in area_circle_set:
             area_circle_list.append(area_circle.to_dict())
        if len(area_circle_list) != 0:
            alert_info_area_dict['circle'] = area_circle_list

        area_geocode_set = self.capfeedalertinfoareageocode_set.all()
        area_geocode_list = []
        for area_geocode in area_geocode_set:
            area_geocode_list.append(area_geocode.to_dict())
        if len(area_geocode_list) != 0:
            alert_info_area_dict['geocode'] = area_geocode_list

        return alert_info_area_dict


class CapFeedAlertInfoAreaCircle(models.Model):
    id = models.BigAutoField(primary_key=True)
    value = models.TextField()
    alert_info_area = models.ForeignKey(CapFeedAlertInfoArea, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cap_feed_alertinfoareacircle'

    def to_dict(self):
        alert_info_area_circle_dict = dict()
        alert_info_area_circle_dict['value'] = self.value
        return alert_info_area_circle_dict



class CapFeedAlertInfoAreaGeocode(models.Model):
    id = models.BigAutoField(primary_key=True)
    value_name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    alert_info_area = models.ForeignKey(CapFeedAlertInfoArea, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cap_feed_alertinfoareageocode'

    def to_dict(self):
        alert_info_area_geocode_dict = dict()
        alert_info_area_geocode_dict['value_name'] = self.value_name
        alert_info_area_geocode_dict['value'] = self.value
        return alert_info_area_geocode_dict

class CapFeedAlertInfoAreaPolygon(models.Model):
    id = models.BigAutoField(primary_key=True)
    value = models.TextField()
    alert_info_area = models.ForeignKey(CapFeedAlertInfoArea, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cap_feed_alertinfoareapolygon'

    def to_dict(self):
        alert_info_area_ploygon_dict = dict()
        alert_info_area_ploygon_dict['value'] = self.value
        return alert_info_area_ploygon_dict

class CapFeedAlertInfoParameter(models.Model):
    id = models.BigAutoField(primary_key=True)
    value_name = models.CharField(max_length=255)
    value = models.TextField()
    alert_info = models.ForeignKey(CapFeedAlertInfo, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cap_feed_alertinfoparameter'



    def to_dict(self):
        alert_info_parameter_dict = dict()
        alert_info_parameter_dict['value_name'] = self.value_name
        alert_info_parameter_dict['value'] = self.value
        return alert_info_parameter_dict



class CapFeedContinent(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'cap_feed_continent'


class CapFeedCountry(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    iso3 = models.CharField(unique=True)
    polygon = models.TextField()
    multipolygon = models.TextField()
    centroid = models.CharField(max_length=255)
    continent = models.ForeignKey(CapFeedContinent, models.DO_NOTHING)
    region = models.ForeignKey('CapFeedRegion', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cap_feed_country'


class CapFeedFeed(models.Model):
    name = models.CharField(max_length=255)
    url = models.CharField(primary_key=True, max_length=255)
    format = models.CharField()
    polling_interval = models.IntegerField()
    atom = models.CharField()
    cap = models.CharField()
    country = models.ForeignKey(CapFeedCountry, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cap_feed_feed'


class CapFeedRegion(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    polygon = models.TextField()
    centroid = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'cap_feed_region'

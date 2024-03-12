# This models is used for getting all alerts in the Alert Database
from django.db import models


class CapFeedCountry(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'cap_feed_country'


class CapFeedAdmin1(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    country = models.ForeignKey('CapFeedCountry', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cap_feed_admin1'


class CapFeedAlert(models.Model):
    id = models.BigAutoField(primary_key=True)
    sent = models.DateTimeField()
    country = models.ForeignKey('CapFeedCountry', models.DO_NOTHING)
    admin1s = models.ManyToManyField(CapFeedAdmin1, through='CapFeedAlertadmin1')

    class Meta:
        managed = False
        db_table = 'cap_feed_alert'

    def to_dict(self):
        alert_dict = {}
        alert_dict["id"] = self.id
        first_info = self.capfeedalertinfo_set.first()

        alert_dict["event"] = first_info.event
        alert_dict["category"] = first_info.category
        alert_dict["country_name"] = self.country.name
        admin1_names = set()
        for admin1 in self.admin1s.all():
            admin1_names.add(admin1.name)
        alert_dict["admin1s"] = list(admin1_names)
        alert_dict["sent"] = str(self.sent)

        return alert_dict


class CapFeedAlertadmin1(models.Model):
    id = models.BigAutoField(primary_key=True)
    admin1 = models.ForeignKey(CapFeedAdmin1, models.DO_NOTHING)
    alert = models.ForeignKey(CapFeedAlert, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cap_feed_alertadmin1'


class CapFeedAlertinfo(models.Model):
    id = models.BigAutoField(primary_key=True)
    category = models.CharField()
    event = models.CharField(max_length=255)
    urgency = models.CharField()
    severity = models.CharField()
    certainty = models.CharField()
    alert = models.ForeignKey(CapFeedAlert, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cap_feed_alertinfo'

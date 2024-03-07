from django.contrib.postgres.fields import ArrayField
from django.db import models

class Subscription(models.Model):
    id = models.AutoField(primary_key=True)
    subscription_name = models.CharField(default="", verbose_name="subscription_name",
                                         max_length=512)
    user_id = models.IntegerField(default=0, verbose_name="user_id")
    country_ids = ArrayField(models.IntegerField(verbose_name='country_ids'), default=list)
    admin1_ids = ArrayField(models.IntegerField(verbose_name='admin1_ids'), default=list)
    urgency_array = ArrayField(models.CharField(verbose_name='urgency_array'), default=list)
    severity_array = ArrayField(models.CharField(verbose_name='severity_array'), default=list)
    certainty_array = ArrayField(models.CharField(verbose_name='certainty_array'), default=list)
    subscribe_by = ArrayField(models.CharField(verbose_name="subscribe_by"), default=list)
    sent_flag = models.IntegerField(default=0, verbose_name="sent_flag")

    def get_alert_id_list(self):
        alerts_list = []
        alerts = self.alert_set.all()

        for alert in alerts:
            alerts_list.append(alert.id)
        return alerts_list

    def save(self, *args, force_insert=False, force_update=False, **kwargs):
        from subscription_manager_dir.tasks import subscription_mapper
        from django.core.cache import cache
        super().save(force_insert, force_update, *args, **kwargs)
        #Add the subscription id as a view lock, so user will not view the subscription during
        # mappings.
        cache.add("v"+str(self.id), True, timeout=None)
        subscription_mapper.apply_async(args=[self.id], queue='subscription_manager')

    def delete(self, *args, force_insert=False, force_update=False):
        super().delete(force_insert, force_update)

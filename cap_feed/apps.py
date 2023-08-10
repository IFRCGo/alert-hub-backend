from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save, pre_delete



class CapFeedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cap_feed'
    # Listen to the new registration event of feed
    def ready(self):
        Feed = self.get_model("Feed")
        Alert = self.get_model("Alert")
        post_delete.connect(delete_feed, sender=Feed)
        post_save.connect(cache_incoming_alert, sender=Alert)
        pre_delete.connect(cache_removed_alert, sender=Alert)
    
def delete_feed(sender, instance, *args, **kwargs):
    from .models import remove_task
    remove_task(instance)

def cache_incoming_alert(sender, instance, *args, **kwargs):
    from capaggregator.celery import app
    if instance.all_info_are_added():
        alert_data = {
            'alert_id': instance.id,
            'country_id': instance.country.id,
            'admin1_ids': [],
        }
        for alert_admin1 in instance.alertadmin1_set.all():
            alert_data['admin1_ids'].append(alert_admin1.admin1.id)

        app.send_task('cache.tasks.cache_incoming_alert', args=[], kwargs=alert_data, queue='cache', routing_key='cache.#', exchange='cache')

def cache_removed_alert(sender, instance, *args, **kwargs):
    from capaggregator.celery import app
    alert_data = {
        'alert_id': instance.id,
        'country_id': instance.country.id,
        'admin1_ids': [],
    }
    for alert_admin1 in instance.alertadmin1_set.all():
        alert_data['admin1_ids'].append(alert_admin1.admin1.id)

    app.send_task('cache.tasks.remove_cached_alert', args=[], kwargs=alert_data, queue='cache', routing_key='cache.#', exchange='cache')
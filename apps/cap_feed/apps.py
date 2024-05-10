from django.apps import AppConfig

# from django.db.models.signals import post_save, pre_delete


class CapFeedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cap_feed'

    # Listen to the new registration event of feed
    def ready(self):
        # Feed = self.get_model("Feed")
        # Alert = self.get_model("Alert")
        # post_save.connect(notify_incoming_alert_for_subscription, sender=Alert)
        # post_delete.connect(notify_removed_alert_for_subscription, sender=Alert)
        # TODO: Clean-up cache
        # post_save.connect(update_cache_instructions, sender=Alert)
        # pre_delete.connect(update_cache_instructions, sender=Alert)
        import apps.cap_feed.receivers

        apps.cap_feed.receivers


def notify_incoming_alert_for_subscription(sender, instance, *args, **kwargs):
    from main.celery import app

    if instance.all_info_are_added():
        app.send_task(
            'apps.subscription_manager.tasks.get_incoming_alert',
            args=[],
            kwargs={'alert_id': instance.id},
            queue='subscription_manager',
            routing_key='subscription_manager.#',
            exchange='subscription_manager',
        )


def notify_removed_alert_for_subscription(sender, instance, *args, **kwargs):
    from main.celery import app

    app.send_task(
        'apps.subscription_manager.tasks.get_removed_alert',
        args=[],
        kwargs={'alert_id': instance.id},
        queue='subscription_manager',
        routing_key='subscription_manager.#',
        exchange='subscription_manager',
    )


# TODO: Rmove this
def update_cache_instructions(sender, instance, *args, **kwargs):
    from main.celery import app

    if instance.all_info_are_added():
        alert_data = {'country_id': instance.country.id}
        app.send_task(
            'cache.tasks.update_cache_instructions',
            args=[],
            kwargs=alert_data,
            queue='cache',
            routing_key='cache.#',
            exchange='cache',
        )

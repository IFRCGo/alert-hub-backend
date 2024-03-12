class AlertDBRouter:
    """
    A router to control all database operations on models in the `external_alert_models.py` file.
    """
    alert_model_names = ['CapFeedCountry', 'CapFeedAdmin1', 'CapFeedAlert',
                         'CapFeedAlertadmin1', 'CapFeedAlertinfo']

    def db_for_read(self, model, **hints):
        """
        Attempts to read specified models go to AlertDB.
        """
        if model.__name__ in self.alert_model_names:
            return 'AlertDB'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Attempts to write specified models go to AlertDB.
        """
        if model.__name__ in self.alert_model_names:
            return 'AlertDB'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if one of the specified models is involved.
        """
        if obj1.__class__.__name__ in self.alert_model_names or obj2.__class__.__name__ in self.alert_model_names:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'AlertDB':
            return False  # Prevent all migrations on 'AlertDB'
        return True  # Allow all migrations on 'default'

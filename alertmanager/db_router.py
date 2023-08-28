class CAPRouter(object):
    "Route cache models to existing CAP Aggregator DB."
    route_app_labels = {"cache"}
    DB_ALIAS = 'cap_aggregator'

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.DB_ALIAS
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.DB_ALIAS
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (obj1._meta.app_label in self.route_app_labels and
            obj2._meta.app_label in self.route_app_labels):
            return True
        return None

    def allow_syncdb(self, db, model):
        if db == self.DB_ALIAS:
            return model._meta.app_label in self.route_app_labels + ('south',)
        elif model._meta.app_label in self.route_app_labels:
            return False
        return None
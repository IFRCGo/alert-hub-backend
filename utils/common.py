import copy
import typing
from django.db import models


# Adapted from this response in Stackoverflow
# http://stackoverflow.com/a/19053800/1072990
def to_camel_case(snake_str):
    components = snake_str.split("_")
    # We capitalize the first letter of each component except the first one
    # with the 'capitalize' method and join them together.
    return components[0] + "".join(x.capitalize() if x else "_" for x in components[1:])


def get_queryset_for_model(
    model: typing.Type[models.Model],
    queryset: models.QuerySet | None = None,
) -> models.QuerySet:
    if queryset is not None:
        return copy.deepcopy(queryset)
    return model.objects.all()


def logger_log_extra(context_data):
    return {
        'context': context_data,
    }

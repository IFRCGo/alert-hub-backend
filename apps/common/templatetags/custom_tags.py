from django import template
from django.conf import settings
from django.core.files.storage import FileSystemStorage, get_storage_class
from django.templatetags.static import static

register = template.Library()

StorageClass = get_storage_class()


@register.filter(is_safe=True)
def static_full_path(path):
    static_path = static(path)
    if StorageClass == FileSystemStorage:
        return f"{settings.APP_HTTP_PROTOCOL}://{settings.APP_DOMAIN}{static_path}"
    # With s3 storage
    return static_path

"""
ASGI config for capaggregator project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""
import os
from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
from dotenv import load_dotenv



if 'WEBSITE_HOSTNAME' not in os.environ:
    load_dotenv(".env")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capaggregator.settings')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capaggregator.production')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
})


#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from dotenv import load_dotenv


def main():
    """Run administrative tasks."""
    if "test" in sys.argv:
        os.environ["Test_Environment"] = 'True'
    else:
        os.environ["Test_Environment"] = 'False'
    # When running on Azure App Service you should use the production settings.
    if 'WEBSITE_HOSTNAME' in os.environ:
        settings_module = "project.production"
    else:
        settings_module = "project.settings"
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

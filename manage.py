#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import logging
logger = logging.getLogger(__name__)

from dotenv import load_dotenv


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
    load_dotenv()
    logging.basicConfig(
        filename='logs.log',
        filemode='a',
        format='%(asctime)s - %(pathname)s - \n\t %(levelname)s - %(message)s',
        level=logging.DEBUG
    )
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
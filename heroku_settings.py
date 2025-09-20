"""
Heroku-specific settings for coda_project.

This module imports the main settings and configures them for Heroku deployment.
"""

import os

# Set environment to 'testing' for Heroku UAT deployment
os.environ.setdefault('ENVIRONMENT', 'testing')

# Import all settings from the main settings module
from .settings import *
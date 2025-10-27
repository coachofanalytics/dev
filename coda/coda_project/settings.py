"""
Django settings for coda_project project.
This is the main settings file that imports from base_settings.py
"""

import os

# Determine environment
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'local')
# ENVIRONMENT = 'staging'  # Commented out - use environment variable or default to 'local'

print(f"Loading settings for environment: {ENVIRONMENT}")


# First, import all base settings
from .coda_settings.base_settings import *

# Then, import environment-specific overrides
if ENVIRONMENT == 'staging':
    # Staging = Heroku UAT environment
    from .coda_settings.heroku_settings import *
elif ENVIRONMENT == 'production':
    from .coda_settings.prod_settings import *
elif ENVIRONMENT == 'local':
    from .coda_settings.local_settings import *
else:
    # Default to local settings for development
    from .coda_settings.local_settings import *

print(f"Settings loaded successfully for {ENVIRONMENT} environment")

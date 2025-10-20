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
    from .coda_settings.local_settings import *
# elif ENVIRONMENT == 'staging':
#     print(f"Loading settings_staging for environment: {ENVIRONMENT}")
#     from .coda_settings.heroku_settings import *
elif ENVIRONMENT == 'production':
    from .coda_settings.prod_settings import *
elif ENVIRONMENT == 'heroku2':
    from .coda_settings.heroku_settings import *
else:
    # Default to local settings
    from .coda_settings.local_settings import *

print(f"Settings loaded successfully for {ENVIRONMENT} environment")

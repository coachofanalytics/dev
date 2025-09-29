"""
Django settings for coda_project project.
This is the main settings file that imports from base_settings.py
"""

import os

# Determine environment
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'local')
# ENVIRONMENT = 'local'

# print(f"Loading settings for environment: {ENVIRONMENT}")

# First, import all base settings
from .base_settings import *

# Then, import environment-specific overrides
if ENVIRONMENT == 'local':
    from .local_settings import *
elif ENVIRONMENT == 'testing':
    from .heroku_settings import *
elif ENVIRONMENT == 'production':
    from .prod_settings import *
elif ENVIRONMENT == 'heroku':
    from .heroku_settings import *
else:
    # Default to local settings
    from .local_settings import *

print(f"Settings loaded successfully for {ENVIRONMENT} environment")

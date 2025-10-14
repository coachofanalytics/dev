"""
Django settings for coda_project project.
This is the main settings file that imports from base_settings.py
"""

import os

# Determine environment - use 'local' as default for development
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'local')

print(f"🚀 Loading Django settings for environment: {ENVIRONMENT}")

# First, import all base settings
from .coda_settings.base_settings import *

# Then, import environment-specific overrides
if ENVIRONMENT == 'local':
    print(f"📁 Loading local development settings...")
    from .coda_settings.local_settings import *
elif ENVIRONMENT == 'staging':
    print(f"🌐 Loading staging/Heroku settings...")
    from .coda_settings.heroku_settings import *
elif ENVIRONMENT == 'production':
    print(f"🔒 Loading production settings...")
    from .coda_settings.prod_settings import *
elif ENVIRONMENT == 'heroku2':
    print(f"🌐 Loading Heroku settings...")
    from .coda_settings.heroku_settings import *
else:
    # Default to local settings
    print(f"📁 Loading default local settings...")
    from .coda_settings.local_settings import *

print(f"✅ Settings loaded successfully for {ENVIRONMENT} environment")
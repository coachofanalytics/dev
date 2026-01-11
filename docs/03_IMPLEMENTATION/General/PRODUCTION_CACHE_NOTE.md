# Production Cache Configuration Note

## Critical Requirement: Shared Cache for Meeting Launcher

**Status:** ✅ Redis cache support added with environment variable switch

## Problem

The meeting launcher integration requires a **shared cache backend** (Redis/memcached) to work correctly in production. 

- **LocMemCache** is process-local and will NOT allow:
  - Autolink management commands to see launch intents from web server
  - Multiple web server processes to share launch intent data
  - Background tasks to access launch intents

## Solution

Redis cache support has been added to all environment settings files with an environment variable switch.

### Environment Variable

```bash
CACHE_BACKEND=redis  # Use Redis (shared cache)
CACHE_BACKEND=locmem # Use LocMemCache (dev only, process-local)
```

### Redis URL Configuration

```bash
# Local/Dev
REDIS_URL=redis://127.0.0.1:6379/1

# Production/Heroku
REDIS_URL=redis://...  # Your Redis instance URL
# OR use Heroku Redis addon
REDISCLOUD_URL=redis://...  # Automatically detected
```

## Configuration Files Updated

1. **`coda/coda_project/coda_settings/local_settings.py`**
   - Default: LocMemCache (OK for single-process dev)
   - Can switch to Redis via `CACHE_BACKEND=redis`

2. **`coda/coda_project/coda_settings/prod_settings.py`**
   - Default: Redis (REQUIRED for production)
   - Falls back to LocMemCache if Redis not available (with warning)

3. **`coda/coda_project/coda_settings/heroku_settings.py`**
   - Default: Redis (REQUIRED for UAT/production)
   - Falls back to LocMemCache if Redis not available (with warning)

## Production Deployment Steps

1. **Install Redis** (if not already installed):
   ```bash
   # Heroku
   heroku addons:create heroku-redis:mini
   
   # Or use Redis Cloud
   heroku addons:create rediscloud:30
   ```

2. **Set Environment Variables**:
   ```bash
   # Heroku (automatic if using Heroku Redis addon)
   # REDISCLOUD_URL is automatically set
   
   # Manual configuration
   heroku config:set CACHE_BACKEND=redis
   heroku config:set REDIS_URL=redis://...
   ```

3. **Verify Cache Backend**:
   ```bash
   poetry run python coda/manage.py shell -c "
   from django.conf import settings
   print('Cache backend:', settings.CACHES['default']['BACKEND'])
   "
   ```

## Verification

After deployment, verify cache is shared:

1. Start web server
2. Click "Start Meeting" in DAF v2 (records launch intent)
3. Run autolink command in separate process:
   ```bash
   poetry run python coda/manage.py autolink_meeting_evidence --diagnose --user-id <ID>
   ```
4. Autolink should see the launch intent (if using Redis)

## Dependencies

If using Redis, ensure `django-redis` is installed:

```bash
poetry add django-redis
# OR
pip install django-redis
```

## Notes

- **Local Development**: LocMemCache is fine for single-process testing
- **Production**: MUST use Redis or another shared cache backend
- **Autolink Commands**: Will only see launch intents if cache is shared
- **Meeting Matching**: Primary matching relies on launch intent from cache



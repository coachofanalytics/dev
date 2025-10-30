import logging
import os
from typing import Any, Callable, Dict

try:
    import heroku3  # type: ignore
except Exception:  # heroku3 may not be installed locally yet
    heroku3 = None  # type: ignore

from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)


class HerokuService:
    """Base service for all Heroku API interactions.

    - Safe initialization (no crash if api key/lib missing)
    - Centralized API call handling and caching
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or getattr(settings, 'HEROKU_API_KEY', os.getenv('HEROKU_API_KEY'))
        self.client = None

        if heroku3 is None:
            logger.warning('heroku3 is not installed. Install with: pip install heroku3')
            return

        if not self.api_key:
            logger.warning('HEROKU_API_KEY not configured. Set it in env or Django settings.')
            return

        try:
            self.client = heroku3.from_key(self.api_key)
        except Exception as exc:  # pragma: no cover
            logger.error('Failed to initialize Heroku client: %s', exc)
            self.client = None

    def _handle_api_call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Dict[str, Any]:
        if self.client is None:
            return {'success': False, 'error': 'Heroku client not initialized'}
        try:
            result = func(*args, **kwargs)
            return {'success': True, 'data': result}
        except Exception as exc:  # pragma: no cover
            logger.error('Heroku API call failed: %s', exc)
            return {'success': False, 'error': str(exc)}

    def list_apps(self) -> Dict[str, Any]:
        return self._handle_api_call(lambda: list(self.client.apps()))  # type: ignore[attr-defined]

    def get_app(self, app_name: str) -> Dict[str, Any]:
        cache_key = f'heroku_app_{app_name}'
        cached = cache.get(cache_key)
        if cached:
            return {'success': True, 'data': cached}
        result = self._handle_api_call(self.client.app, app_name)  # type: ignore[attr-defined]
        if result.get('success'):
            cache.set(cache_key, result['data'], 300)
        return result

    def get_config(self, app_name: str) -> Dict[str, Any]:
        app = self.get_app(app_name)
        if not app.get('success'):
            return app
        return self._handle_api_call(lambda: dict(app['data'].config()))

    def set_config(self, app_name: str, key: str, value: str) -> Dict[str, Any]:
        app = self.get_app(app_name)
        if not app.get('success'):
            return app
        result = self._handle_api_call(lambda: app['data'].config().update({key: value}))
        if result.get('success'):
            cache.delete(f'heroku_app_{app_name}')
        return result



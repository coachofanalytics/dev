import logging
from typing import Any, Dict

from .heroku_service import HerokuService


logger = logging.getLogger(__name__)


class DatabaseService(HerokuService):
    """Database backup and basic management using Heroku Postgres API.

    This is a minimal, safe implementation that returns structured dicts and
    avoids raising exceptions to keep management commands resilient.
    """

    def _get_database_addon(self, app_name: str) -> Dict[str, Any]:
        app = self.get_app(app_name)
        if not app.get('success'):
            return app
        try:
            addons = app['data'].addons()
            postgres_addon = next((a for a in addons if 'postgres' in a.name.lower()), None)
            if not postgres_addon:
                return {'success': False, 'error': 'No PostgreSQL addon found'}
            return {'success': True, 'data': postgres_addon}
        except Exception as exc:  # pragma: no cover
            logger.error('Failed to load addons: %s', exc)
            return {'success': False, 'error': str(exc)}

    def create_backup(self, app_name: str) -> Dict[str, Any]:
        addon = self._get_database_addon(app_name)
        if not addon.get('success'):
            return addon
        try:
            backup = addon['data'].backups.create()
            return {
                'success': True,
                'backup_id': getattr(backup, 'id', None),
                'status': getattr(backup, 'status', 'unknown'),
            }
        except Exception as exc:  # pragma: no cover
            logger.error('Backup creation failed: %s', exc)
            return {'success': False, 'error': str(exc)}

    def list_backups(self, app_name: str, limit: int = 10) -> Dict[str, Any]:
        addon = self._get_database_addon(app_name)
        if not addon.get('success'):
            return addon
        try:
            items = addon['data'].backups()[:limit]
            normalized = []
            for b in items:
                normalized.append({
                    'id': getattr(b, 'id', None),
                    'created_at': getattr(b, 'created_at', None),
                    'status': getattr(b, 'status', None),
                    'size': getattr(b, 'size', None),
                })
            return {'success': True, 'backups': normalized}
        except Exception as exc:  # pragma: no cover
            return {'success': False, 'error': str(exc)}



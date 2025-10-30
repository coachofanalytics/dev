import logging
import os
from typing import Any, Dict, List, Optional

from .heroku_service import HerokuService
import requests


logger = logging.getLogger(__name__)


class DatabaseService(HerokuService):
    """Database backup and basic management using Heroku CLI.

    We invoke the official Heroku CLI for Postgres backups because the
    heroku3 library does not expose the `pg:backups` interface directly.
    """

    # --------------------
    # HTTP API helpers
    # --------------------
    def _heroku_headers(self) -> Dict[str, str]:
        api_key = self.api_key or os.getenv('HEROKU_API_KEY')
        return {
            'Authorization': f'Bearer {api_key}' if api_key else '',
            'Accept': 'application/vnd.heroku+json; version=3',
            'Content-Type': 'application/json',
        }

    def _postgres_headers(self) -> Dict[str, str]:
        api_key = self.api_key or os.getenv('HEROKU_API_KEY')
        return {
            'Authorization': f'Bearer {api_key}' if api_key else '',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def _get_postgres_db_identifier(self, app_name: str) -> Dict[str, Any]:
        """Resolve the Postgres database identifier for the Postgres API.

        The Postgres API expects the database UUID (the add-on id), not the human name.
        Fallbacks try the add-on name if needed.
        """
        try:
            resp = requests.get(
                f'https://api.heroku.com/apps/{app_name}/addons',
                headers=self._heroku_headers(),
                timeout=30,
            )
            if resp.status_code != 200:
                return {'success': False, 'error': f'Addons API failed: {resp.status_code} {resp.text}'}
            addons = resp.json()
            for addon in addons:
                plan = addon.get('plan', {})
                plan_name = plan.get('name', '')
                if plan_name.startswith('heroku-postgresql'):
                    # Prefer add-on id for postgres API
                    return {
                        'success': True,
                        'db_id': addon.get('id'),
                        'db_name': addon.get('name'),
                    }
            return {'success': False, 'error': 'No Heroku Postgres addon found'}
        except Exception as exc:  # pragma: no cover
            logger.error('Failed to query addons: %s', exc)
            return {'success': False, 'error': str(exc)}

    def create_backup(self, app_name: str) -> Dict[str, Any]:
        """Create a database backup via Heroku Postgres HTTP API."""
        addon = self._get_postgres_db_identifier(app_name)
        if not addon.get('success'):
            return addon
        db_id = addon.get('db_id') or addon.get('db_name')
        try:
            # Initiate capture
            resp = requests.post(
                f'https://postgres-api.heroku.com/client/v11/databases/{db_id}/backups',
                headers=self._postgres_headers(),
                json={},
                timeout=60,
            )
            if resp.status_code not in (200, 201, 202):
                return {'success': False, 'error': f'Backup API failed: {resp.status_code} {resp.text}'}
            data = resp.json() if resp.text else {}
            backup_id: Optional[str] = data.get('name') or data.get('id')
            return {'success': True, 'backup_id': backup_id or 'unknown', 'response': data}
        except Exception as exc:  # pragma: no cover
            logger.error('Backup creation failed: %s', exc)
            return {'success': False, 'error': str(exc)}

    def list_backups(self, app_name: str, limit: int = 10) -> Dict[str, Any]:
        """List recent backups via Heroku Postgres HTTP API."""
        addon = self._get_postgres_db_identifier(app_name)
        if not addon.get('success'):
            return addon
        db_id = addon.get('db_id') or addon.get('db_name')
        try:
            resp = requests.get(
                f'https://postgres-api.heroku.com/client/v11/databases/{db_id}/backups',
                headers=self._postgres_headers(),
                timeout=60,
            )
            if resp.status_code != 200:
                return {'success': False, 'error': f'Backups API failed: {resp.status_code} {resp.text}'}
            items = resp.json() if resp.text else []
            # Normalize minimal fields
            normalized = []
            for b in items[:limit]:
                normalized.append({
                    'id': b.get('name') or b.get('id'),
                    'created_at': b.get('created_at'),
                    'status': b.get('finished_at') and 'finished' or 'running',
                    'size': b.get('num_bytes'),
                })
            return {'success': True, 'backups': normalized}
        except Exception as exc:  # pragma: no cover
            logger.error('List backups failed: %s', exc)
            return {'success': False, 'error': str(exc)}



import logging
import os
import subprocess
from typing import Any, Dict, List, Optional
from datetime import datetime

from .heroku_service import HerokuService
import requests


logger = logging.getLogger(__name__)


class DatabaseService(HerokuService):
    """Database backup and management for PostgreSQL databases.

    Supports two backup strategies:
    1. Heroku Postgres HTTP API (for Heroku-managed databases)
    2. pg_dump (for any PostgreSQL database, including external RDS)
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

    def _list_postgres_client_databases(self) -> Dict[str, Any]:
        """Query Postgres Client API for all databases visible to the token."""
        try:
            resp = requests.get(
                'https://postgres-api.heroku.com/client/v11/databases',
                headers=self._postgres_headers(),
                timeout=60,
            )
            if resp.status_code != 200:
                return {'success': False, 'error': f'Client databases API failed: {resp.status_code} {resp.text}'}
            return {'success': True, 'items': resp.json() or []}
        except Exception as exc:  # pragma: no cover
            logger.error('Failed to list client databases: %s', exc)
            return {'success': False, 'error': str(exc)}

    def _resolve_client_db_name_for_app(self, app_name: str) -> Dict[str, Any]:
        """Try to resolve the client database identifier for the given app via Client API.

        Returns both 'client_id' (UUID) and 'client_name'.
        """
        listing = self._list_postgres_client_databases()
        if not listing.get('success'):
            return listing
        items: List[Dict[str, Any]] = listing.get('items', [])
        # Prefer exact app match
        for item in items:
            if item.get('app_name') == app_name:
                return {'success': True, 'client_name': item.get('name'), 'client_id': item.get('id')}
        # As fallback, return first Postgres DB
        if items:
            return {'success': True, 'client_name': items[0].get('name'), 'client_id': items[0].get('id')}
        return {'success': False, 'error': 'No Postgres databases visible to token'}

    def _get_postgres_db_identifier(self, app_name: str) -> Dict[str, Any]:
        """Resolve the identifier accepted by the Heroku Postgres API client endpoints.

        Priority:
        1) Use addon-attachment name (e.g., 'DATABASE' or 'HEROKU_POSTGRESQL_CYAN')
        2) Fallback to add-on name
        3) As last resort, add-on id
        """
        try:
            # First, try addon attachments to get canonical attachment name
            att_resp = requests.get(
                f'https://api.heroku.com/apps/{app_name}/addon-attachments',
                headers=self._heroku_headers(),
                timeout=30,
            )
            if att_resp.status_code == 200:
                attachments = att_resp.json()
                pg_attachments = [a for a in attachments if a.get('addon', {}).get('plan', {}).get('name', '').startswith('heroku-postgresql')]
                if pg_attachments:
                    # Prefer the primary 'DATABASE' attachment if present
                    primary = next((a for a in pg_attachments if a.get('name') == 'DATABASE'), None)
                    chosen = primary or pg_attachments[0]
                    return {
                        'success': True,
                        'db_identifier': chosen.get('name'),
                        'fallback_addon_id': chosen.get('addon', {}).get('id'),
                        'fallback_addon_name': chosen.get('addon', {}).get('name'),
                        'all_attachment_names': [a.get('name') for a in pg_attachments if a.get('name')],
                    }

            # Fallback to addons list
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
                    return {
                        'success': True,
                        'db_identifier': addon.get('name') or addon.get('id'),
                    }
            return {'success': False, 'error': 'No Heroku Postgres addon found'}
        except Exception as exc:  # pragma: no cover
            logger.error('Failed to resolve postgres identifier: %s', exc)
            return {'success': False, 'error': str(exc)}

    def create_backup(self, app_name: str) -> Dict[str, Any]:
        """Create a database backup via Heroku Postgres HTTP API."""
        # Try Client API first
        resolved = self._resolve_client_db_name_for_app(app_name)
        if resolved.get('success'):
            db_identifier = resolved.get('client_id') or resolved.get('client_name')
        else:
            addon = self._get_postgres_db_identifier(app_name)
            if not addon.get('success'):
                return addon
            db_identifier = addon.get('db_identifier') or addon.get('fallback_addon_name') or addon.get('fallback_addon_id')
        try:
            # Initiate capture
            resp = requests.post(
                f'https://postgres-api.heroku.com/client/v11/databases/{db_identifier}/backups',
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
        # Prefer Client API database name
        candidates: List[str] = []
        resolved = self._resolve_client_db_name_for_app(app_name)
        if resolved.get('success'):
            if resolved.get('client_id'):
                candidates.append(resolved['client_id'])
            if resolved.get('client_name'):
                candidates.append(resolved['client_name'])
        # Fallback: identifiers via app addons/attachments
        addon = self._get_postgres_db_identifier(app_name)
        if addon.get('success'):
            if addon.get('db_identifier'):
                candidates.append(addon['db_identifier'])
            if addon.get('all_attachment_names'):
                candidates.extend(addon['all_attachment_names'])
            if addon.get('fallback_addon_name'):
                candidates.append(addon['fallback_addon_name'])
            if addon.get('fallback_addon_id'):
                candidates.append(addon['fallback_addon_id'])
        # Common attachment/config var names
        if 'DATABASE' not in candidates:
            candidates.append('DATABASE')
        if 'DATABASE_URL' not in candidates:
            candidates.append('DATABASE_URL')

        errors: List[str] = []
        for cand in candidates:
            try:
                resp = requests.get(
                    f'https://postgres-api.heroku.com/client/v11/databases/{cand}/backups',
                    headers=self._postgres_headers(),
                    timeout=60,
                )
                if resp.status_code == 200:
                    items = resp.json() if resp.text else []
                    normalized = []
                    for b in items[:limit]:
                        normalized.append({
                            'id': b.get('name') or b.get('id'),
                            'created_at': b.get('created_at'),
                            'status': b.get('finished_at') and 'finished' or 'running',
                            'size': b.get('num_bytes'),
                        })
                    return {'success': True, 'backups': normalized, 'identifier_used': cand}
                errors.append(f"{cand}: {resp.status_code} {resp.text}")
            except Exception as exc:  # pragma: no cover
                errors.append(f"{cand}: {exc}")
        return {'success': False, 'error': 'Backups API failed for all candidates: ' + ' | '.join(errors)}

    # --------------------
    # pg_dump-based backup (works with any PostgreSQL DB)
    # --------------------
    def create_pg_dump_backup(self, database_url: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Create a PostgreSQL backup using pg_dump (works with RDS, Heroku Postgres, etc.).
        
        Args:
            database_url: PostgreSQL connection URL (defaults to DATABASE_URL env var)
            output_path: Where to save backup (defaults to /tmp/backup_<timestamp>.sql)
        
        Returns:
            Dict with success, backup_path, and size
        """
        db_url = database_url or os.getenv('DATABASE_URL')
        if not db_url:
            return {'success': False, 'error': 'No DATABASE_URL provided'}
        
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'/tmp/backup_{timestamp}.sql'
        
        try:
            # Run pg_dump
            result = subprocess.run(
                ['pg_dump', '--no-owner', '--no-acl', '-f', output_path, db_url],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
            )
            
            if result.returncode != 0:
                return {'success': False, 'error': f'pg_dump failed: {result.stderr}'}
            
            # Check file size
            if os.path.exists(output_path):
                size = os.path.getsize(output_path)
                return {
                    'success': True,
                    'backup_path': output_path,
                    'size_bytes': size,
                    'size_mb': round(size / (1024 * 1024), 2),
                }
            return {'success': False, 'error': 'Backup file not created'}
            
        except FileNotFoundError:
            return {'success': False, 'error': 'pg_dump not found. Install PostgreSQL client or add buildpack.'}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'pg_dump timed out after 5 minutes'}
        except Exception as exc:  # pragma: no cover
            logger.error('pg_dump backup failed: %s', exc)
            return {'success': False, 'error': str(exc)}

    def list_local_backups(self, backup_dir: str = '/tmp') -> Dict[str, Any]:
        """List pg_dump backups in the specified directory."""
        try:
            backups = []
            if not os.path.exists(backup_dir):
                return {'success': True, 'backups': []}
            
            for filename in os.listdir(backup_dir):
                if filename.startswith('backup_') and filename.endswith('.sql'):
                    filepath = os.path.join(backup_dir, filename)
                    stat = os.stat(filepath)
                    backups.append({
                        'filename': filename,
                        'path': filepath,
                        'size_bytes': stat.st_size,
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    })
            
            # Sort by creation time, newest first
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            return {'success': True, 'backups': backups}
            
        except Exception as exc:  # pragma: no cover
            logger.error('Failed to list local backups: %s', exc)
            return {'success': False, 'error': str(exc)}



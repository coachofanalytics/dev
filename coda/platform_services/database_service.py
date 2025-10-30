import logging
import shlex
import subprocess
from typing import Any, Dict, List

from .heroku_service import HerokuService


logger = logging.getLogger(__name__)


class DatabaseService(HerokuService):
    """Database backup and basic management using Heroku CLI.

    We invoke the official Heroku CLI for Postgres backups because the
    heroku3 library does not expose the `pg:backups` interface directly.
    """

    def _run_cli(self, args: List[str]) -> Dict[str, Any]:
        """Run a Heroku CLI command and return stdout/stderr safely."""
        try:
            process = subprocess.run(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
            )
            if process.returncode != 0:
                return {'success': False, 'error': process.stderr.strip() or process.stdout.strip()}
            return {'success': True, 'output': process.stdout}
        except Exception as exc:  # pragma: no cover
            logger.error('Heroku CLI failed: %s', exc)
            return {'success': False, 'error': str(exc)}

    def create_backup(self, app_name: str) -> Dict[str, Any]:
        """Create a database backup via Heroku CLI."""
        cmd = shlex.split(f"heroku pg:backups:capture --app {app_name}")
        result = self._run_cli(cmd)
        if not result.get('success'):
            return result
        # Best-effort parse backup ID from output
        backup_id = None
        for line in result.get('output', '').splitlines():
            if line.strip().startswith('Backing up '):
                # Example: Backing up DATABASE to b001... done
                parts = line.split('to ')
                if len(parts) == 2:
                    backup_id = parts[1].split()[0]
        return {'success': True, 'backup_id': backup_id, 'raw': result.get('output')}

    def list_backups(self, app_name: str, limit: int = 10) -> Dict[str, Any]:
        """List recent backups via Heroku CLI and return normalized rows."""
        cmd = shlex.split(f"heroku pg:backups --app {app_name}")
        result = self._run_cli(cmd)
        if not result.get('success'):
            return result
        rows = []
        for line in result.get('output', '').splitlines():
            # Skip headers and separators
            if not line.strip() or line.lower().startswith('id  '):
                continue
            if set(line.strip()) == {'-'}:
                continue
            rows.append(line)
        return {'success': True, 'backups': rows[:limit]}



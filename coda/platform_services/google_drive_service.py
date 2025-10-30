"""
Google Drive backup service for PostgreSQL database backups.

Uploads backups to Google Drive and maintains only the last 2 backups.
"""
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)


class GoogleDriveBackupService:
    """Service for uploading database backups to Google Drive with rotation."""

    def __init__(self, folder_id: Optional[str] = None):
        """
        Initialize Google Drive backup service.
        
        Args:
            folder_id: Google Drive folder ID (defaults to GOOGLE_DRIVE_BACKUP_FOLDER env var)
        """
        self.folder_id = folder_id or os.getenv('GOOGLE_DRIVE_BACKUP_FOLDER')
        self._service = None

    def _get_credentials(self) -> Credentials:
        """Get Google Drive API credentials from environment variables."""
        return Credentials(
            token=os.getenv('GOOGLE_ACCESS_TOKEN'),
            refresh_token=os.getenv('GOOGLE_REFRESH_TOKEN'),
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            token_uri="https://oauth2.googleapis.com/token",
            scopes=['https://www.googleapis.com/auth/drive.file']
        )

    def _get_service(self):
        """Get or create Google Drive service instance."""
        if not self._service:
            try:
                creds = self._get_credentials()
                self._service = build('drive', 'v3', credentials=creds)
            except Exception as exc:  # pragma: no cover
                logger.error('Failed to initialize Google Drive service: %s', exc)
                raise
        return self._service

    def upload_backup(self, file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a backup file to Google Drive.
        
        Args:
            file_path: Local path to backup file
            filename: Optional custom filename (defaults to basename of file_path)
        
        Returns:
            Dict with success, file_id, and web_view_link
        """
        if not os.path.exists(file_path):
            return {'success': False, 'error': f'File not found: {file_path}'}

        if not filename:
            filename = os.path.basename(file_path)

        try:
            service = self._get_service()
            
            # File metadata
            file_metadata = {'name': filename}
            if self.folder_id:
                file_metadata['parents'] = [self.folder_id]

            # Upload file
            media = MediaFileUpload(file_path, mimetype='application/sql', resumable=True)
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size, webViewLink, createdTime'
            ).execute()

            logger.info(f"Backup uploaded to Google Drive: {filename} (ID: {file.get('id')})")
            
            return {
                'success': True,
                'file_id': file.get('id'),
                'filename': file.get('name'),
                'size': int(file.get('size', 0)),
                'web_view_link': file.get('webViewLink'),
                'created_time': file.get('createdTime'),
            }

        except Exception as exc:  # pragma: no cover
            logger.error(f'Failed to upload backup to Google Drive: {exc}')
            return {'success': False, 'error': str(exc)}

    def list_backups(self, limit: int = 10) -> Dict[str, Any]:
        """
        List backup files in the Google Drive folder.
        
        Args:
            limit: Maximum number of backups to list
        
        Returns:
            Dict with success and list of backups
        """
        try:
            service = self._get_service()
            
            # Build query
            query_parts = ["name contains 'backup_'", "name contains '.sql'"]
            if self.folder_id:
                query_parts.append(f"'{self.folder_id}' in parents")
            query_parts.append("trashed=false")
            query = " and ".join(query_parts)

            # List files
            results = service.files().list(
                q=query,
                pageSize=limit,
                fields='files(id, name, size, createdTime, webViewLink)',
                orderBy='createdTime desc'
            ).execute()

            backups = results.get('files', [])
            
            return {
                'success': True,
                'backups': [
                    {
                        'file_id': b['id'],
                        'filename': b['name'],
                        'size': int(b.get('size', 0)),
                        'size_mb': round(int(b.get('size', 0)) / (1024 * 1024), 2),
                        'created_time': b['createdTime'],
                        'web_view_link': b.get('webViewLink'),
                    }
                    for b in backups
                ]
            }

        except Exception as exc:  # pragma: no cover
            logger.error(f'Failed to list backups from Google Drive: {exc}')
            return {'success': False, 'error': str(exc)}

    def delete_backup(self, file_id: str) -> Dict[str, Any]:
        """
        Delete a backup file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
        
        Returns:
            Dict with success status
        """
        try:
            service = self._get_service()
            service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted backup from Google Drive: {file_id}")
            return {'success': True, 'file_id': file_id}

        except Exception as exc:  # pragma: no cover
            logger.error(f'Failed to delete backup from Google Drive: {exc}')
            return {'success': False, 'error': str(exc)}

    def cleanup_old_backups(self, keep_count: int = 2) -> Dict[str, Any]:
        """
        Delete old backups, keeping only the most recent N backups.
        
        Args:
            keep_count: Number of most recent backups to keep (default: 2)
        
        Returns:
            Dict with success, deleted_count, and list of deleted file IDs
        """
        try:
            # List all backups
            list_result = self.list_backups(limit=100)
            if not list_result.get('success'):
                return list_result

            backups = list_result.get('backups', [])
            
            # If we have fewer than keep_count, nothing to delete
            if len(backups) <= keep_count:
                return {
                    'success': True,
                    'deleted_count': 0,
                    'deleted_files': [],
                    'message': f'Only {len(backups)} backup(s) found, keeping all.'
                }

            # Delete old backups (beyond keep_count)
            backups_to_delete = backups[keep_count:]
            deleted_files = []
            
            for backup in backups_to_delete:
                delete_result = self.delete_backup(backup['file_id'])
                if delete_result.get('success'):
                    deleted_files.append({
                        'file_id': backup['file_id'],
                        'filename': backup['filename'],
                    })

            return {
                'success': True,
                'deleted_count': len(deleted_files),
                'deleted_files': deleted_files,
                'kept_count': keep_count,
                'message': f'Deleted {len(deleted_files)} old backup(s), kept {keep_count} most recent.'
            }

        except Exception as exc:  # pragma: no cover
            logger.error(f'Failed to cleanup old backups: {exc}')
            return {'success': False, 'error': str(exc)}

    def backup_and_upload(self, database_service, keep_count: int = 2) -> Dict[str, Any]:
        """
        Complete backup workflow: create pg_dump backup, upload to Drive, cleanup old backups.
        
        Args:
            database_service: DatabaseService instance for creating backups
            keep_count: Number of backups to keep (default: 2)
        
        Returns:
            Dict with complete workflow results
        """
        workflow_result = {
            'success': False,
            'backup_created': False,
            'uploaded': False,
            'cleanup_done': False,
        }

        try:
            # Step 1: Create pg_dump backup
            logger.info('Creating PostgreSQL backup...')
            backup_result = database_service.create_pg_dump_backup()
            
            if not backup_result.get('success'):
                workflow_result['error'] = f"Backup creation failed: {backup_result.get('error')}"
                return workflow_result
            
            workflow_result['backup_created'] = True
            workflow_result['backup_path'] = backup_result['backup_path']
            workflow_result['backup_size_mb'] = backup_result['size_mb']

            # Step 2: Upload to Google Drive
            logger.info('Uploading backup to Google Drive...')
            upload_result = self.upload_backup(backup_result['backup_path'])
            
            if not upload_result.get('success'):
                workflow_result['error'] = f"Upload failed: {upload_result.get('error')}"
                return workflow_result
            
            workflow_result['uploaded'] = True
            workflow_result['file_id'] = upload_result['file_id']
            workflow_result['web_view_link'] = upload_result['web_view_link']

            # Step 3: Cleanup old backups
            logger.info(f'Cleaning up old backups (keeping {keep_count})...')
            cleanup_result = self.cleanup_old_backups(keep_count=keep_count)
            
            if cleanup_result.get('success'):
                workflow_result['cleanup_done'] = True
                workflow_result['deleted_count'] = cleanup_result['deleted_count']

            # Step 4: Delete local temp file
            try:
                if os.path.exists(backup_result['backup_path']):
                    os.remove(backup_result['backup_path'])
                    logger.info(f"Deleted local temp file: {backup_result['backup_path']}")
            except Exception as e:
                logger.warning(f"Failed to delete local temp file: {e}")

            workflow_result['success'] = True
            return workflow_result

        except Exception as exc:  # pragma: no cover
            logger.error(f'Backup workflow failed: {exc}')
            workflow_result['error'] = str(exc)
            return workflow_result


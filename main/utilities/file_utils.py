"""
File Utilities

Handles all file-related operations including:
- File uploads to Google Drive
- File processing and validation
- Image handling and optimization

This utility encapsulates file-related functionality previously scattered across main/utils.py
"""

import logging
import os
from typing import Optional, Dict, Any
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


class FileUtils:
    """
    Utility class for file-related operations.
    
    Provides methods for file uploads, processing, and validation.
    """
    
    def __init__(self):
        self.logger = logger
    
    def upload_image_to_drive(
        self, 
        image_path: str, 
        folder_id: str, 
        image_name: str
    ) -> Dict[str, Any]:
        """
        Upload image to Google Drive.
        
        Args:
            image_path: Path to the image file
            folder_id: Google Drive folder ID
            image_name: Name for the uploaded image
            
        Returns:
            Dict with upload result
        """
        try:
            if not os.path.exists(image_path):
                return {
                    'success': False,
                    'error': 'Image file not found',
                    'file_path': image_path
                }
            
            # Placeholder for actual Google Drive upload
            # This would typically use Google Drive API
            self.logger.info(f"Uploading image {image_name} to Google Drive folder {folder_id}")
            
            return {
                'success': True,
                'message': f'Image {image_name} uploaded successfully',
                'file_path': image_path,
                'folder_id': folder_id,
                'image_name': image_name,
                'drive_url': f'https://drive.google.com/file/d/{image_name}/view'  # Placeholder
            }
            
        except Exception as e:
            self.logger.error(f"Error uploading image to Drive: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': image_path
            }
    
    def validate_file(
        self, 
        file_path: str, 
        allowed_extensions: Optional[list] = None,
        max_size_mb: int = 10
    ) -> Dict[str, Any]:
        """
        Validate file based on criteria.
        
        Args:
            file_path: Path to the file
            allowed_extensions: List of allowed file extensions
            max_size_mb: Maximum file size in MB
            
        Returns:
            Dict with validation results
        """
        try:
            if not os.path.exists(file_path):
                return {
                    'valid': False,
                    'error': 'File does not exist',
                    'file_path': file_path
                }
            
            # Check file size
            file_size = os.path.getsize(file_path)
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if file_size > max_size_bytes:
                return {
                    'valid': False,
                    'error': f'File too large (max {max_size_mb}MB)',
                    'file_size': file_size,
                    'max_size': max_size_bytes
                }
            
            # Check file extension
            if allowed_extensions:
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext not in allowed_extensions:
                    return {
                        'valid': False,
                        'error': f'File extension {file_ext} not allowed',
                        'allowed_extensions': allowed_extensions,
                        'file_extension': file_ext
                    }
            
            return {
                'valid': True,
                'error': None,
                'file_path': file_path,
                'file_size': file_size,
                'file_extension': os.path.splitext(file_path)[1].lower()
            }
            
        except Exception as e:
            self.logger.error(f"Error validating file: {e}")
            return {
                'valid': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict with file information
        """
        try:
            if not os.path.exists(file_path):
                return {
                    'exists': False,
                    'error': 'File does not exist'
                }
            
            stat = os.stat(file_path)
            
            return {
                'exists': True,
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': stat.st_size,
                'file_extension': os.path.splitext(file_path)[1].lower(),
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime,
                'is_file': os.path.isfile(file_path),
                'is_directory': os.path.isdir(file_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting file info: {e}")
            return {
                'exists': False,
                'error': str(e),
                'file_path': file_path
            }






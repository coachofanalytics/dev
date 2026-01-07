"""
File Scanner Service
Virus and malware scanning for uploaded files
"""
import os
import mimetypes
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import python-magic, but fallback to mimetypes if not available
# python-magic requires libmagic which is not available on Windows by default
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning(
        "python-magic not available. Using mimetypes fallback. "
        "For better MIME detection on Windows, install python-magic-bin: "
        "pip install python-magic-bin"
    )


class FileScannerService:
    """
    Service for scanning uploaded files for viruses and malware.

    Note: For production, install ClamAV:
    - Windows: https://www.clamav.net/downloads
    - Linux: sudo apt-get install clamav clamav-daemon
    - macOS: brew install clamav

    Then install Python client: pip install clamd
    """

    def __init__(self):
        """Initialize scanner with ClamAV if available."""
        self.clamav_available = False
        self.clamd = None

        try:
            import clamd
            self.clamd = clamd.ClamdUnixSocket()
            # Test connection
            self.clamd.ping()
            self.clamav_available = True
            logger.info("ClamAV scanner initialized successfully")
        except ImportError:
            logger.warning(
                "ClamAV not installed. Install with: pip install clamd\n"
                "File scanning will use basic validation only."
            )
        except Exception as e:
            logger.warning(f"ClamAV not available: {e}. Using basic validation.")

    def scan_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Scan a file for viruses and malware.

        Args:
            file_path: Path to file to scan

        Returns:
            Tuple of (is_clean, scan_result)
            - is_clean: True if file is safe
            - scan_result: Description of scan result
        """
        if not os.path.exists(file_path):
            return False, "File not found"

        # Basic file validation (always performed)
        basic_check = self._basic_file_validation(file_path)
        if not basic_check[0]:
            return basic_check

        # ClamAV scan if available
        if self.clamav_available:
            return self._clamav_scan(file_path)
        else:
            # If ClamAV not available, return success with note
            return True, "CLEAN (Basic validation only - ClamAV not installed)"

    def _basic_file_validation(self, file_path: str) -> Tuple[bool, str]:
        """
        Perform basic file validation without antivirus.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Check file size (max 10MB)
            file_size = os.path.getsize(file_path)
            max_size = 10 * 1024 * 1024  # 10MB

            if file_size > max_size:
                return False, f"File too large: {file_size} bytes"

            if file_size == 0:
                return False, "File is empty"

            # Check MIME type
            # Allowed MIME types for KYC documents
            allowed_types = [
                'application/pdf',
                'image/jpeg',
                'image/png',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            ]

            try:
                if MAGIC_AVAILABLE:
                    # Use python-magic for accurate MIME detection
                    mime = magic.Magic(mime=True)
                    file_type = mime.from_file(file_path)
                else:
                    # Fallback to mimetypes based on file extension
                    file_type, _ = mimetypes.guess_type(file_path)
                    if file_type is None:
                        file_type = 'application/octet-stream'

                if file_type not in allowed_types:
                    return False, f"Invalid file type: {file_type}"

            except Exception as e:
                logger.warning(f"Could not determine MIME type: {e}")
                # Continue without MIME check if detection fails

            # Check for suspicious content patterns
            with open(file_path, 'rb') as f:
                # Read first 1KB for signature check
                header = f.read(1024)

                # Check for script/executable signatures
                suspicious_patterns = [
                    b'<script',
                    b'<?php',
                    b'#!/bin/bash',
                    b'#!/usr/bin/python',
                    b'MZ',  # Windows executable
                ]

                for pattern in suspicious_patterns:
                    if pattern.lower() in header.lower():
                        return False, f"Suspicious content detected: {pattern.decode('utf-8', errors='ignore')}"

            return True, "Basic validation passed"

        except Exception as e:
            logger.error(f"Error during basic file validation: {e}")
            return False, f"Validation error: {str(e)}"

    def _clamav_scan(self, file_path: str) -> Tuple[bool, str]:
        """
        Scan file using ClamAV.

        Args:
            file_path: Path to file to scan

        Returns:
            Tuple of (is_clean, scan_result)
        """
        try:
            scan_result = self.clamd.scan(file_path)

            if scan_result is None:
                return True, "CLEAN"

            # ClamAV returns dict with file path as key
            for file, result in scan_result.items():
                status = result[0]
                if status == 'FOUND':
                    virus_name = result[1]
                    logger.warning(f"Virus detected in {file}: {virus_name}")
                    return False, f"INFECTED: {virus_name}"
                elif status == 'ERROR':
                    logger.error(f"ClamAV scan error for {file}")
                    return False, "SCAN ERROR"

            return True, "CLEAN"

        except Exception as e:
            logger.error(f"ClamAV scan error: {e}")
            # Return basic validation result if ClamAV fails
            return self._basic_file_validation(file_path)

    def scan_stream(self, file_stream) -> Tuple[bool, str]:
        """
        Scan a file stream for viruses.

        Args:
            file_stream: File-like object to scan

        Returns:
            Tuple of (is_clean, scan_result)
        """
        if not self.clamav_available:
            return True, "CLEAN (ClamAV not available)"

        try:
            result = self.clamd.instream(file_stream)

            if result['stream'][0] == 'FOUND':
                virus_name = result['stream'][1]
                return False, f"INFECTED: {virus_name}"
            elif result['stream'][0] == 'ERROR':
                return False, "SCAN ERROR"
            else:
                return True, "CLEAN"

        except Exception as e:
            logger.error(f"Stream scan error: {e}")
            return True, f"SCAN ERROR: {str(e)}"

    def get_scanner_info(self) -> dict:
        """
        Get information about the scanner.

        Returns:
            Dictionary with scanner information
        """
        info = {
            'clamav_available': self.clamav_available,
            'scanner_type': 'ClamAV' if self.clamav_available else 'Basic Validation',
        }

        if self.clamav_available:
            try:
                info['clamav_version'] = self.clamd.version()
            except Exception as e:
                info['clamav_version'] = f'Error: {e}'

        return info

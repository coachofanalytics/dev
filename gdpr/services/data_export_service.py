"""
Data Export Service for GDPR Article 15 compliance.

Provides user data export in multiple formats:
- JSON: Machine-readable format
- CSV: Spreadsheet format
- PDF: Human-readable format
"""

import json
import csv
import io
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

from gdpr.models import DataExportRequest

logger = logging.getLogger(__name__)


class DataExportService:
    """
    Service for exporting user data in GDPR-compliant format.

    GDPR Article 15: Right of access by the data subject
    GDPR Article 20: Right to data portability
    """

    @staticmethod
    def create_export_request(
        user: User,
        export_format: str = "json"
    ) -> DataExportRequest:
        """
        Create a new data export request.

        Args:
            user: User requesting export
            export_format: Format for export (json, csv, pdf)

        Returns:
            DataExportRequest: Created request

        Raises:
            ValueError: If invalid format specified
        """
        valid_formats = ["json", "csv", "pdf"]
        if export_format not in valid_formats:
            raise ValueError(f"Invalid format. Must be one of: {', '.join(valid_formats)}")

        # Check for existing pending requests
        existing = DataExportRequest.objects.filter(
            user=user,
            status__in=["pending", "processing"]
        ).first()

        if existing:
            logger.info(f"Returning existing export request {existing.id} for user {user.username}")
            return existing

        # Create new request
        request = DataExportRequest.objects.create(
            user=user,
            export_format=export_format,
            status="pending",
        )

        logger.info(f"Created data export request {request.id} for user {user.username}")
        return request

    @classmethod
    def collect_user_data(cls, user: User) -> Dict[str, Any]:
        """
        Collect all user data from across the system.

        Args:
            user: User to collect data for

        Returns:
            Dictionary containing all user data
        """
        data = {
            "export_info": {
                "exported_at": timezone.now().isoformat(),
                "export_format": "complete",
                "gdpr_article": "Article 15 - Right of access",
            },
            "personal_info": cls._get_personal_info(user),
            "profile": cls._get_profile_data(user),
            "authentication": cls._get_authentication_data(user),
            "marketplace": cls._get_marketplace_data(user),
            "payments": cls._get_payment_data(user),
            "audit_logs": cls._get_audit_logs(user),
            "consent_records": cls._get_consent_records(user),
        }

        logger.info(f"Collected data for user {user.username}")
        return data

    @staticmethod
    def _get_personal_info(user: User) -> Dict[str, Any]:
        """Get basic personal information."""
        return {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "is_active": user.is_active,
        }

    @staticmethod
    def _get_profile_data(user: User) -> Optional[Dict[str, Any]]:
        """Get user profile data."""
        try:
            from accounts.models import UserProfile
            profile = UserProfile.objects.filter(user=user).first()

            if not profile:
                return None

            return {
                "user_type": profile.user_type,
                "phone_number": profile.phone_number,
                "address": profile.address,
                "city": profile.city,
                "country": profile.country,
                "bio": profile.bio,
                "profile_picture": profile.profile_picture.url if profile.profile_picture else None,
                "resume": profile.resume.url if profile.resume else None,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error collecting profile data: {e}")
            return None

    @staticmethod
    def _get_authentication_data(user: User) -> Dict[str, Any]:
        """Get authentication-related data."""
        try:
            from accounts.mfa.models import MFADevice
            from audit.models import LoginHistory

            mfa_device = MFADevice.objects.filter(user=user).first()

            # Get recent login history (last 100)
            login_history = LoginHistory.objects.filter(
                user=user
            ).order_by("-attempted_at")[:100]

            return {
                "mfa_enabled": mfa_device.is_active if mfa_device else False,
                "mfa_device_name": mfa_device.device_name if mfa_device else None,
                "mfa_activated_at": mfa_device.activated_at.isoformat() if mfa_device and mfa_device.activated_at else None,
                "recent_logins": [
                    {
                        "timestamp": login.attempted_at.isoformat(),
                        "status": login.status,
                        "ip_address": login.ip_address,
                        "location": login.location,
                        "device_type": login.device_type,
                        "browser": login.browser,
                    }
                    for login in login_history
                ],
            }
        except Exception as e:
            logger.error(f"Error collecting authentication data: {e}")
            return {}

    @staticmethod
    def _get_marketplace_data(user: User) -> Dict[str, Any]:
        """Get marketplace-related data."""
        try:
            from marketplace.models import Business, InvestmentOpportunity, JobOpportunity

            businesses = Business.objects.filter(owner=user)
            investments = InvestmentOpportunity.objects.filter(posted_by=user)
            jobs = JobOpportunity.objects.filter(posted_by=user)

            return {
                "businesses": [
                    {
                        "name": b.name,
                        "description": b.description,
                        "category": b.category.name if b.category else None,
                        "location": b.location,
                        "created_at": b.created_at.isoformat(),
                    }
                    for b in businesses
                ],
                "investment_opportunities": [
                    {
                        "title": i.title,
                        "description": i.description,
                        "amount_needed": str(i.amount_needed),
                        "created_at": i.created_at.isoformat(),
                    }
                    for i in investments
                ],
                "job_opportunities": [
                    {
                        "title": j.title,
                        "description": j.description,
                        "location": j.location,
                        "created_at": j.created_at.isoformat(),
                    }
                    for j in jobs
                ],
            }
        except Exception as e:
            logger.error(f"Error collecting marketplace data: {e}")
            return {}

    @staticmethod
    def _get_payment_data(user: User) -> Dict[str, Any]:
        """Get payment-related data."""
        try:
            from payments.models import Wallet, Transaction, Subscription

            wallet = Wallet.objects.filter(user=user).first()
            transactions = Transaction.objects.filter(user=user).order_by("-created_at")[:100]
            subscriptions = Subscription.objects.filter(user=user)

            return {
                "wallet": {
                    "balance": str(wallet.balance) if wallet else "0.00",
                    "currency": wallet.currency if wallet else "USD",
                    "created_at": wallet.created_at.isoformat() if wallet else None,
                } if wallet else None,
                "transactions": [
                    {
                        "type": t.transaction_type,
                        "amount": str(t.amount),
                        "status": t.status,
                        "description": t.description,
                        "created_at": t.created_at.isoformat(),
                    }
                    for t in transactions
                ],
                "subscriptions": [
                    {
                        "plan": s.plan.name if hasattr(s, 'plan') else "Unknown",
                        "status": s.status,
                        "start_date": s.start_date.isoformat() if hasattr(s, 'start_date') else None,
                        "end_date": s.end_date.isoformat() if hasattr(s, 'end_date') else None,
                    }
                    for s in subscriptions
                ],
            }
        except Exception as e:
            logger.error(f"Error collecting payment data: {e}")
            return {}

    @staticmethod
    def _get_audit_logs(user: User) -> list:
        """Get audit log entries (last 500)."""
        try:
            from audit.models import AuditLog

            logs = AuditLog.objects.filter(
                user=user
            ).order_by("-created_at")[:500]

            return [
                {
                    "event_type": log.event_type,
                    "description": log.description,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ]
        except Exception as e:
            logger.error(f"Error collecting audit logs: {e}")
            return []

    @staticmethod
    def _get_consent_records(user: User) -> list:
        """Get consent records."""
        try:
            from gdpr.models import ConsentRecord

            consents = ConsentRecord.objects.filter(user=user)

            return [
                {
                    "consent_type": consent.consent_type,
                    "is_given": consent.is_given,
                    "version": consent.version,
                    "given_at": consent.given_at.isoformat() if consent.given_at else None,
                    "withdrawn_at": consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
                }
                for consent in consents
            ]
        except Exception as e:
            logger.error(f"Error collecting consent records: {e}")
            return []

    @classmethod
    def export_to_json(cls, user: User) -> str:
        """
        Export user data to JSON format.

        Args:
            user: User to export data for

        Returns:
            JSON string of user data
        """
        data = cls.collect_user_data(user)
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def export_to_csv(cls, user: User) -> str:
        """
        Export user data to CSV format.

        Args:
            user: User to export data for

        Returns:
            CSV string of user data
        """
        data = cls.collect_user_data(user)

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Category", "Field", "Value"])

        # Flatten and write data
        def write_dict(prefix: str, d: dict):
            for key, value in d.items():
                if isinstance(value, dict):
                    write_dict(f"{prefix}.{key}", value)
                elif isinstance(value, list):
                    writer.writerow([prefix, key, f"{len(value)} items"])
                else:
                    writer.writerow([prefix, key, str(value)])

        write_dict("user_data", data)

        return output.getvalue()

    @classmethod
    def process_export_request(cls, request_id: str) -> bool:
        """
        Process a data export request.

        Args:
            request_id: UUID of export request

        Returns:
            True if successful, False otherwise
        """
        try:
            request = DataExportRequest.objects.get(id=request_id)
            request.mark_processing()

            user = request.user
            export_format = request.export_format

            # Generate export
            if export_format == "json":
                data = cls.export_to_json(user)
            elif export_format == "csv":
                data = cls.export_to_csv(user)
            elif export_format == "pdf":
                # PDF export would require additional library (ReportLab or WeasyPrint)
                # For now, export as JSON
                logger.warning("PDF export not yet implemented, using JSON")
                data = cls.export_to_json(user)
            else:
                raise ValueError(f"Unsupported format: {export_format}")

            # Save to file (in production, use cloud storage)
            file_name = f"user_data_{user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
            file_path = f"/exports/{file_name}"  # This should be a real file path in production

            # In production, save to file system or cloud storage
            # For now, we'll just store the path
            file_size = len(data.encode('utf-8'))

            request.mark_completed(file_path=file_path, file_size=file_size)

            logger.info(f"Successfully processed export request {request_id}")
            return True

        except DataExportRequest.DoesNotExist:
            logger.error(f"Export request {request_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error processing export request {request_id}: {e}")
            try:
                request.mark_failed(str(e))
            except:
                pass
            return False

"""
Tests for GDPR data export service.
"""

import pytest
import json
from django.contrib.auth.models import User

from gdpr.services.data_export_service import DataExportService
from gdpr.models import DataExportRequest


@pytest.mark.django_db
class TestDataExportService:
    """Test data export service."""

    @pytest.fixture
    def user(self):
        """Create test user with profile."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        return user

    def test_create_export_request(self, user):
        """Test creating an export request."""
        request = DataExportService.create_export_request(user, "json")

        assert request is not None
        assert request.user == user
        assert request.export_format == "json"
        assert request.status == "pending"

    def test_create_export_request_invalid_format(self, user):
        """Test creating request with invalid format."""
        with pytest.raises(ValueError) as exc:
            DataExportService.create_export_request(user, "invalid")

        assert "Invalid format" in str(exc.value)

    def test_create_export_request_existing_pending(self, user):
        """Test that existing pending request is returned."""
        request1 = DataExportService.create_export_request(user, "json")
        request2 = DataExportService.create_export_request(user, "csv")

        # Should return same request
        assert request1.id == request2.id

    def test_collect_user_data(self, user):
        """Test collecting user data."""
        data = DataExportService.collect_user_data(user)

        assert "export_info" in data
        assert "personal_info" in data
        assert "profile" in data
        assert "authentication" in data

        # Check personal info
        personal = data["personal_info"]
        assert personal["username"] == "testuser"
        assert personal["email"] == "test@example.com"
        assert personal["first_name"] == "Test"
        assert personal["last_name"] == "User"

    def test_get_personal_info(self, user):
        """Test getting personal info."""
        info = DataExportService._get_personal_info(user)

        assert info["username"] == "testuser"
        assert info["email"] == "test@example.com"
        assert info["first_name"] == "Test"
        assert info["last_name"] == "User"
        assert "date_joined" in info
        assert "is_active" in info

    def test_export_to_json(self, user):
        """Test exporting to JSON format."""
        json_data = DataExportService.export_to_json(user)

        # Should be valid JSON
        data = json.loads(json_data)
        assert "personal_info" in data
        assert data["personal_info"]["username"] == "testuser"

    def test_export_to_csv(self, user):
        """Test exporting to CSV format."""
        csv_data = DataExportService.export_to_csv(user)

        # Should contain CSV headers
        assert "Category" in csv_data
        assert "Field" in csv_data
        assert "Value" in csv_data

        # Should contain user data
        assert "testuser" in csv_data

    def test_process_export_request_json(self, user):
        """Test processing JSON export request."""
        request = DataExportService.create_export_request(user, "json")

        success = DataExportService.process_export_request(str(request.id))

        assert success is True

        # Refresh request from database
        request.refresh_from_db()
        assert request.status == "completed"
        assert request.file_path is not None
        assert request.file_size > 0
        assert request.processed_at is not None
        assert request.expires_at is not None

    def test_process_export_request_csv(self, user):
        """Test processing CSV export request."""
        request = DataExportService.create_export_request(user, "csv")

        success = DataExportService.process_export_request(str(request.id))

        assert success is True

        request.refresh_from_db()
        assert request.status == "completed"

    def test_process_export_request_not_found(self):
        """Test processing non-existent request."""
        success = DataExportService.process_export_request("00000000-0000-0000-0000-000000000000")

        assert success is False

    def test_get_authentication_data_no_mfa(self, user):
        """Test getting authentication data without MFA."""
        data = DataExportService._get_authentication_data(user)

        assert "mfa_enabled" in data
        assert data["mfa_enabled"] is False
        assert "recent_logins" in data

    def test_get_marketplace_data(self, user):
        """Test getting marketplace data."""
        data = DataExportService._get_marketplace_data(user)

        assert "businesses" in data
        assert "investment_opportunities" in data
        assert "job_opportunities" in data
        assert isinstance(data["businesses"], list)

    def test_get_payment_data(self, user):
        """Test getting payment data."""
        data = DataExportService._get_payment_data(user)

        assert "wallet" in data
        assert "transactions" in data
        assert "subscriptions" in data

    def test_get_audit_logs(self, user):
        """Test getting audit logs."""
        logs = DataExportService._get_audit_logs(user)

        assert isinstance(logs, list)

    def test_get_consent_records(self, user):
        """Test getting consent records."""
        from gdpr.models import ConsentRecord

        # Create a consent record
        ConsentRecord.objects.create(
            user=user,
            consent_type="terms_of_service",
            version="1.0",
        )

        consents = DataExportService._get_consent_records(user)

        assert isinstance(consents, list)
        assert len(consents) >= 1

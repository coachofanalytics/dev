"""
Tests for password breach checking service.
"""

import pytest
from unittest.mock import patch, Mock

from accounts.security.services import PasswordBreachService


class TestPasswordBreachService:
    """Test password breach checking."""

    @patch('accounts.security.services.password_breach_service.requests.get')
    def test_check_password_not_breached(self, mock_get):
        """Test checking password that hasn't been breached."""
        # Mock API response with no matching hash
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "ABC123:5\nDEF456:10\nGHI789:3"
        mock_get.return_value = mock_response

        is_breached, count = PasswordBreachService.check_password("uniquepassword123")

        assert is_breached is False
        assert count == 0

    @patch('accounts.security.services.password_breach_service.requests.get')
    def test_check_password_breached(self, mock_get):
        """Test checking password that has been breached."""
        # For password "password", SHA-1 hash is 5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8
        # First 5 chars: 5BAA6
        # Remaining: 1E4C9B93F3F0682250B6CF8331B7EE68FD8

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "1E4C9B93F3F0682250B6CF8331B7EE68FD8:3730471\nOTHERHASH:100"
        mock_get.return_value = mock_response

        is_breached, count = PasswordBreachService.check_password("password")

        assert is_breached is True
        assert count == 3730471

    @patch('accounts.security.services.password_breach_service.requests.get')
    def test_check_password_api_error(self, mock_get):
        """Test handling API errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        is_breached, count = PasswordBreachService.check_password("testpassword")

        assert is_breached is False
        assert count is None

    @patch('accounts.security.services.password_breach_service.requests.get')
    def test_check_password_timeout(self, mock_get):
        """Test handling API timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        is_breached, count = PasswordBreachService.check_password("testpassword")

        assert is_breached is False
        assert count is None

    @patch('accounts.security.services.password_breach_service.requests.get')
    def test_check_password_disabled(self, mock_get):
        """Test when breach checking is disabled."""
        with patch.object(PasswordBreachService, 'ENABLED', False):
            is_breached, count = PasswordBreachService.check_password("password")

        assert is_breached is False
        assert count is None
        mock_get.assert_not_called()

    def test_get_breach_message_none(self):
        """Test message for non-breached password."""
        message = PasswordBreachService.get_breach_message(0)
        assert "secure" in message.lower()
        assert "not been found" in message.lower()

    def test_get_breach_message_few(self):
        """Test message for password with few breaches."""
        message = PasswordBreachService.get_breach_message(5)
        assert "5" in message
        assert "data breach" in message.lower()

    def test_get_breach_message_moderate(self):
        """Test message for password with moderate breaches."""
        message = PasswordBreachService.get_breach_message(50)
        assert "50" in message
        assert "commonly compromised" in message.lower()

    def test_get_breach_message_many(self):
        """Test message for password with many breaches."""
        message = PasswordBreachService.get_breach_message(500)
        assert "500" in message
        assert "very common" in message.lower()

    def test_get_breach_message_extremely_many(self):
        """Test message for password with extremely many breaches."""
        message = PasswordBreachService.get_breach_message(5000)
        assert "5000" in message
        assert "extremely common" in message.lower()

"""
Smart Collateral Service
Handles advanced collateral tracking and monitoring features
"""

import logging
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.files.base import ContentFile
from decimal import Decimal
import json

logger = logging.getLogger(__name__)


class SmartCollateralService:
    """Service for managing smart collateral features"""
    
    def __init__(self):
        self.gps_api_endpoint = "https://api.gpstracking.com"  # Placeholder
        self.land_registry_api = "https://api.landregistry.gov"  # Placeholder
    
    def enable_vehicle_gps_tracking(self, collateral, device_id, install_date=None):
        """
        Enable GPS tracking for vehicle collateral
        
        Args:
            collateral: LoanCollateral instance
            device_id: GPS device identifier
            install_date: Installation date (optional)
        
        Returns:
            tuple: (success, message)
        """
        try:
            if collateral.collateral_type != 'vehicle':
                return False, "GPS tracking only available for vehicle collateral"
            
            # Enable GPS tracking
            success, message = collateral.enable_gps_tracking(device_id, install_date)
            
            if success:
                # Register device with GPS service (placeholder)
                self._register_gps_device(device_id, collateral.id)
                
                # Set up monitoring
                collateral.monitoring_enabled = True
                collateral.monitoring_frequency = 'real_time'
                collateral.save()
                
                logger.info(f"GPS tracking enabled for collateral {collateral.id}")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error enabling GPS tracking: {e}")
            return False, f"Error enabling GPS tracking: {str(e)}"
    
    def update_vehicle_location(self, collateral, location_data):
        """
        Update vehicle location from GPS device
        
        Args:
            collateral: LoanCollateral instance
            location_data: dict with lat, lng, timestamp
        
        Returns:
            tuple: (success, message)
        """
        try:
            if not collateral.gps_tracking_enabled:
                return False, "GPS tracking not enabled for this collateral"
            
            # Format location string
            location_str = f"{location_data.get('lat', 0)}, {location_data.get('lng', 0)}"
            timestamp = location_data.get('timestamp')
            
            if timestamp:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Update location
            success, message = collateral.update_gps_location(location_str, timestamp)
            
            if success:
                # Check for geofence violations
                self._check_geofence_violations(collateral, location_data)
                
                # Update monitoring
                collateral.last_monitoring_check = timezone.now()
                collateral.save()
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error updating vehicle location: {e}")
            return False, f"Error updating location: {str(e)}"
    
    def verify_land_title_deed(self, collateral, deed_number, verification_data=None):
        """
        Verify land title deed with government registry
        
        Args:
            collateral: LoanCollateral instance
            deed_number: Official title deed number
            verification_data: Additional verification data
        
        Returns:
            tuple: (success, message)
        """
        try:
            if collateral.collateral_type != 'land_title':
                return False, "Title deed verification only available for land collateral"
            
            # Verify with land registry (placeholder API call)
            verification_result = self._verify_with_land_registry(deed_number, verification_data)
            
            if verification_result['valid']:
                # Update collateral
                success, message = collateral.verify_title_deed(deed_number)
                
                if success:
                    # Add verification details
                    collateral.verification_notes = verification_result.get('notes', '')
                    collateral.verification_status = 'verified'
                    collateral.save()
                    
                    logger.info(f"Title deed verified for collateral {collateral.id}")
                
                return success, message
            else:
                return False, f"Title deed verification failed: {verification_result.get('error', 'Unknown error')}"
            
        except Exception as e:
            logger.error(f"Error verifying title deed: {e}")
            return False, f"Error verifying title deed: {str(e)}"
    
    def add_land_survey_report(self, collateral, survey_file, survey_data):
        """
        Add professional land survey report
        
        Args:
            collateral: LoanCollateral instance
            survey_file: Uploaded survey file
            survey_data: Survey metadata
        
        Returns:
            tuple: (success, message)
        """
        try:
            if collateral.collateral_type != 'land_title':
                return False, "Land survey only available for land collateral"
            
            # Process survey file
            processed_file = self._process_survey_file(survey_file, survey_data)
            
            # Add to collateral
            success, message = collateral.add_land_survey(processed_file)
            
            if success:
                # Update verification status
                collateral.verification_status = 'verified'
                collateral.save()
                
                logger.info(f"Land survey added for collateral {collateral.id}")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error adding land survey: {e}")
            return False, f"Error adding land survey: {str(e)}"
    
    def setup_collateral_monitoring(self, collateral, monitoring_config):
        """
        Set up monitoring for collateral
        
        Args:
            collateral: LoanCollateral instance
            monitoring_config: dict with monitoring settings
        
        Returns:
            tuple: (success, message)
        """
        try:
            # Enable monitoring
            collateral.monitoring_enabled = True
            collateral.monitoring_frequency = monitoring_config.get('frequency', 'weekly')
            collateral.save()
            
            # Set up monitoring alerts based on collateral type
            if collateral.collateral_type == 'vehicle':
                self._setup_vehicle_monitoring(collateral, monitoring_config)
            elif collateral.collateral_type == 'land_title':
                self._setup_land_monitoring(collateral, monitoring_config)
            elif collateral.collateral_type == 'equipment':
                self._setup_equipment_monitoring(collateral, monitoring_config)
            
            logger.info(f"Monitoring setup for collateral {collateral.id}")
            return True, "Monitoring setup successfully"
            
        except Exception as e:
            logger.error(f"Error setting up monitoring: {e}")
            return False, f"Error setting up monitoring: {str(e)}"
    
    def calculate_collateral_risk_score(self, collateral):
        """
        Calculate comprehensive risk score for collateral
        
        Args:
            collateral: LoanCollateral instance
        
        Returns:
            int: Risk score (0-100)
        """
        try:
            # Calculate base risk score
            risk_score = collateral.calculate_risk_score()
            
            # Additional risk factors
            additional_risks = []
            
            # GPS tracking status
            if collateral.collateral_type == 'vehicle':
                if not collateral.gps_tracking_enabled:
                    additional_risks.append("No GPS tracking")
                elif collateral.gps_status == 'offline':
                    additional_risks.append("GPS offline")
                elif collateral.gps_status == 'tampered':
                    additional_risks.append("GPS tampered")
            
            # Title verification
            if collateral.collateral_type == 'land_title':
                if not collateral.title_deed_verified:
                    additional_risks.append("Title not verified")
                if not collateral.land_survey_done:
                    additional_risks.append("No land survey")
            
            # Monitoring status
            if collateral.monitoring_enabled:
                if collateral.last_monitoring_check:
                    days_since_check = (timezone.now() - collateral.last_monitoring_check).days
                    if days_since_check > 30:
                        additional_risks.append("Stale monitoring data")
                else:
                    additional_risks.append("No monitoring data")
            
            # Update risk factors
            collateral.risk_factors = additional_risks
            collateral.save()
            
            # Adjust risk score based on additional factors
            risk_adjustment = len(additional_risks) * 5  # 5 points per risk factor
            final_score = min(100, risk_score + risk_adjustment)
            
            collateral.risk_score = final_score
            collateral.save()
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 50  # Default medium risk
    
    def get_collateral_dashboard_data(self, collateral):
        """
        Get dashboard data for collateral monitoring
        
        Args:
            collateral: LoanCollateral instance
        
        Returns:
            dict: Dashboard data
        """
        try:
            smart_features = collateral.get_smart_features_status()
            
            dashboard_data = {
                'collateral_id': collateral.id,
                'type': collateral.collateral_type,
                'value': float(collateral.estimated_value),
                'verification_status': collateral.verification_status,
                'risk_score': collateral.risk_score,
                'smart_features': smart_features,
                'last_updated': collateral.updated_at.isoformat(),
                'monitoring_status': self._get_monitoring_status(collateral),
                'alerts': collateral.monitoring_alerts or []
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}
    
    def _register_gps_device(self, device_id, collateral_id):
        """Register GPS device with tracking service (placeholder)"""
        # In real implementation, this would call GPS service API
        logger.info(f"GPS device {device_id} registered for collateral {collateral_id}")
    
    def _check_geofence_violations(self, collateral, location_data):
        """Check for geofence violations (placeholder)"""
        # In real implementation, this would check against defined geofences
        pass
    
    def _verify_with_land_registry(self, deed_number, verification_data):
        """Verify title deed with land registry (placeholder)"""
        # In real implementation, this would call land registry API
        return {
            'valid': True,
            'notes': 'Title deed verified with land registry',
            'verification_date': timezone.now().isoformat()
        }
    
    def _process_survey_file(self, survey_file, survey_data):
        """Process land survey file (placeholder)"""
        # In real implementation, this would process the survey file
        return survey_file
    
    def _setup_vehicle_monitoring(self, collateral, config):
        """Set up vehicle-specific monitoring"""
        # Set up geofencing, speed monitoring, etc.
        pass
    
    def _setup_land_monitoring(self, collateral, config):
        """Set up land-specific monitoring"""
        # Set up boundary monitoring, encroachment detection, etc.
        pass
    
    def _setup_equipment_monitoring(self, collateral, config):
        """Set up equipment-specific monitoring"""
        # Set up condition monitoring, usage tracking, etc.
        pass
    
    def _get_monitoring_status(self, collateral):
        """Get current monitoring status"""
        if not collateral.monitoring_enabled:
            return 'disabled'
        
        if not collateral.last_monitoring_check:
            return 'never_checked'
        
        days_since_check = (timezone.now() - collateral.last_monitoring_check).days
        
        if days_since_check == 0:
            return 'current'
        elif days_since_check <= 7:
            return 'recent'
        elif days_since_check <= 30:
            return 'stale'
        else:
            return 'outdated'


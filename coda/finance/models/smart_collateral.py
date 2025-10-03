"""
Smart Collateral System - Revolutionary Technology Integration
============================================================

This module implements a comprehensive smart collateral system that combines:
- IoT sensors and tracking
- Blockchain verification
- Smart contracts for automatic enforcement
- AI-powered risk assessment
- Real-time monitoring and alerts

The system makes it extremely difficult for borrowers to default while providing
seamless experience for legitimate borrowers.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import json
import uuid

User = get_user_model()


class SmartCollateralType(models.Model):
    """Types of smart collateral with specific IoT requirements"""
    
    COLLATERAL_TYPES = [
        ('vehicle', 'Smart Vehicle'),
        ('land', 'Smart Land/Property'),
        ('equipment', 'Smart Equipment'),
        ('livestock', 'Smart Livestock'),
        ('crops', 'Smart Crops'),
        ('machinery', 'Smart Machinery'),
        ('jewelry', 'Smart Jewelry Vault'),
        ('art', 'Smart Art Collection'),
        ('crypto', 'Smart Crypto Assets'),
        ('savings', 'Smart Savings Account'),
    ]
    
    name = models.CharField(max_length=100, choices=COLLATERAL_TYPES)
    description = models.TextField()
    required_iot_sensors = models.JSONField(default=list)  # List of required sensors
    blockchain_verification_required = models.BooleanField(default=True)
    smart_contract_template = models.TextField(blank=True)  # Solidity contract template
    risk_score_weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_name_display()} - Smart Collateral"


class IoTDevice(models.Model):
    """IoT devices used for collateral monitoring"""
    
    DEVICE_TYPES = [
        ('gps_tracker', 'GPS Tracker'),
        ('camera', 'Smart Camera'),
        ('sensor', 'Environmental Sensor'),
        ('lock', 'Smart Lock'),
        ('scale', 'Smart Scale'),
        ('rfid', 'RFID Tag'),
        ('nfc', 'NFC Tag'),
        ('blockchain_node', 'Blockchain Node'),
        ('ai_camera', 'AI-Powered Camera'),
        ('biometric', 'Biometric Scanner'),
    ]
    
    device_id = models.UUIDField(default=uuid.uuid4, unique=True)
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPES)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=200, unique=True)
    firmware_version = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    battery_level = models.IntegerField(null=True, blank=True)  # For battery-powered devices
    signal_strength = models.IntegerField(null=True, blank=True)  # For wireless devices
    
    # Device capabilities
    capabilities = models.JSONField(default=dict)  # GPS, camera, sensors, etc.
    configuration = models.JSONField(default=dict)  # Device-specific settings
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_device_type_display()} - {self.serial_number}"
    
    def is_online(self):
        """Check if device is online based on last heartbeat"""
        if not self.last_heartbeat:
            return False
        return timezone.now() - self.last_heartbeat < timezone.timedelta(minutes=5)


class SmartCollateral(models.Model):
    """Smart collateral with IoT monitoring and blockchain verification"""
    
    STATUS_CHOICES = [
        ('pending_verification', 'Pending Verification'),
        ('active', 'Active Monitoring'),
        ('warning', 'Warning - Attention Required'),
        ('breach', 'Security Breach Detected'),
        ('released', 'Released'),
        ('forfeited', 'Forfeited'),
    ]
    
    # Basic collateral information
    loan_application = models.OneToOneField('finance.LoanApplication', on_delete=models.CASCADE, related_name='smart_collateral')
    collateral_type = models.ForeignKey(SmartCollateralType, on_delete=models.CASCADE)
    description = models.TextField()
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2)
    location = models.CharField(max_length=500)
    coordinates = models.JSONField(null=True, blank=True)  # GPS coordinates
    
    # Smart features
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending_verification')
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    blockchain_hash = models.CharField(max_length=64, blank=True)  # Blockchain verification hash
    smart_contract_address = models.CharField(max_length=42, blank=True)  # Ethereum contract address
    
    # IoT devices attached to this collateral
    iot_devices = models.ManyToManyField(IoTDevice, through='CollateralDevice')
    
    # Monitoring settings
    monitoring_frequency = models.IntegerField(default=60)  # Check every X minutes
    alert_thresholds = models.JSONField(default=dict)  # Custom alert settings
    auto_enforcement_enabled = models.BooleanField(default=True)
    
    # Timestamps
    verified_at = models.DateTimeField(null=True, blank=True)
    last_monitoring_check = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Smart {self.collateral_type.get_name_display()} - {self.loan_application.application_number}"
    
    def calculate_risk_score(self):
        """Calculate dynamic risk score based on multiple factors"""
        score = 0.0
        
        # Base score from collateral type
        score += float(self.collateral_type.risk_score_weight) * 20
        
        # Device connectivity score
        online_devices = sum(1 for device in self.iot_devices.all() if device.is_online())
        total_devices = self.iot_devices.count()
        if total_devices > 0:
            connectivity_score = (online_devices / total_devices) * 30
            score += connectivity_score
        
        # Location stability (if GPS tracking)
        # This would be calculated based on movement patterns
        
        # Blockchain verification status
        if self.blockchain_hash:
            score += 20
        
        # Recent monitoring activity
        if self.last_monitoring_check:
            time_since_check = timezone.now() - self.last_monitoring_check
            if time_since_check < timezone.timedelta(hours=1):
                score += 10
        
        self.risk_score = min(score, 100.0)  # Cap at 100
        return self.risk_score


class CollateralDevice(models.Model):
    """Many-to-many relationship between collateral and IoT devices"""
    
    collateral = models.ForeignKey(SmartCollateral, on_delete=models.CASCADE)
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE)
    installation_date = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False)  # Primary monitoring device
    configuration = models.JSONField(default=dict)  # Device-specific config for this collateral
    
    class Meta:
        unique_together = ['collateral', 'device']


class CollateralMonitoringEvent(models.Model):
    """Events captured by IoT devices monitoring collateral"""
    
    EVENT_TYPES = [
        ('location_change', 'Location Change'),
        ('unauthorized_access', 'Unauthorized Access'),
        ('device_offline', 'Device Offline'),
        ('environmental_alert', 'Environmental Alert'),
        ('movement_detected', 'Movement Detected'),
        ('security_breach', 'Security Breach'),
        ('maintenance_required', 'Maintenance Required'),
        ('value_change', 'Value Change'),
        ('blockchain_verification', 'Blockchain Verification'),
        ('smart_contract_trigger', 'Smart Contract Trigger'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('emergency', 'Emergency'),
    ]
    
    collateral = models.ForeignKey(SmartCollateral, on_delete=models.CASCADE, related_name='monitoring_events')
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='info')
    
    # Event data
    title = models.CharField(max_length=200)
    description = models.TextField()
    data = models.JSONField(default=dict)  # Raw sensor data, GPS coordinates, etc.
    
    # Location and context
    location = models.CharField(max_length=500, blank=True)
    coordinates = models.JSONField(null=True, blank=True)
    
    # Response actions
    auto_response_triggered = models.BooleanField(default=False)
    manual_review_required = models.BooleanField(default=False)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.collateral} - {self.timestamp}"


class SmartContract(models.Model):
    """Smart contracts for automatic loan enforcement"""
    
    CONTRACT_TYPES = [
        ('collateral_lien', 'Collateral Lien'),
        ('automatic_repossession', 'Automatic Repossession'),
        ('payment_enforcement', 'Payment Enforcement'),
        ('insurance_claim', 'Insurance Claim'),
        ('value_verification', 'Value Verification'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('deployed', 'Deployed'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('terminated', 'Terminated'),
    ]
    
    # Contract identification
    contract_id = models.UUIDField(default=uuid.uuid4, unique=True)
    contract_type = models.CharField(max_length=50, choices=CONTRACT_TYPES)
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Blockchain details
    blockchain_network = models.CharField(max_length=50, default='ethereum')  # ethereum, polygon, etc.
    contract_address = models.CharField(max_length=42, unique=True)
    abi = models.JSONField()  # Contract ABI
    bytecode = models.TextField()  # Contract bytecode
    
    # Contract state
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    deployed_at = models.DateTimeField(null=True, blank=True)
    gas_used = models.BigIntegerField(null=True, blank=True)
    
    # Associated collateral and loans
    collateral = models.ForeignKey(SmartCollateral, on_delete=models.CASCADE, null=True, blank=True)
    loan_application = models.ForeignKey('finance.LoanApplication', on_delete=models.CASCADE, null=True, blank=True)
    
    # Contract parameters
    parameters = models.JSONField(default=dict)  # Contract-specific parameters
    auto_execute = models.BooleanField(default=True)
    
    # Monitoring
    last_execution = models.DateTimeField(null=True, blank=True)
    execution_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_contract_type_display()}"


class CollateralInsurance(models.Model):
    """Insurance policies for smart collateral"""
    
    POLICY_TYPES = [
        ('comprehensive', 'Comprehensive Coverage'),
        ('theft', 'Theft Protection'),
        ('damage', 'Damage Protection'),
        ('depreciation', 'Depreciation Coverage'),
        ('cyber', 'Cyber Security'),
    ]
    
    collateral = models.ForeignKey(SmartCollateral, on_delete=models.CASCADE, related_name='insurance_policies')
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPES)
    insurance_provider = models.CharField(max_length=200)
    policy_number = models.CharField(max_length=100)
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2)
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deductible = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Policy details
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    # Smart features
    auto_claim_filing = models.BooleanField(default=True)
    blockchain_verification = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_policy_type_display()} - {self.collateral}"


class CollateralValuation(models.Model):
    """Dynamic valuation of collateral using AI and market data"""
    
    VALUATION_METHODS = [
        ('ai_analysis', 'AI Market Analysis'),
        ('blockchain_oracle', 'Blockchain Oracle'),
        ('manual_appraisal', 'Manual Appraisal'),
        ('market_comparison', 'Market Comparison'),
        ('depreciation_model', 'Depreciation Model'),
    ]
    
    collateral = models.ForeignKey(SmartCollateral, on_delete=models.CASCADE, related_name='valuations')
    valuation_method = models.CharField(max_length=50, choices=VALUATION_METHODS)
    current_value = models.DecimalField(max_digits=12, decimal_places=2)
    previous_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    value_change_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Valuation details
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)  # AI confidence in valuation
    market_data = models.JSONField(default=dict)  # Raw market data used
    ai_analysis = models.JSONField(default=dict)  # AI analysis results
    
    # Blockchain integration
    oracle_verification = models.BooleanField(default=False)
    blockchain_tx_hash = models.CharField(max_length=64, blank=True)
    
    # Timestamps
    valuation_date = models.DateTimeField(auto_now_add=True)
    next_valuation_due = models.DateTimeField()
    
    def __str__(self):
        return f"Valuation - {self.collateral} - ${self.current_value}"


class SmartCollateralAlert(models.Model):
    """AI-powered alerts for collateral monitoring"""
    
    ALERT_TYPES = [
        ('risk_increase', 'Risk Level Increase'),
        ('value_decrease', 'Value Decrease'),
        ('security_breach', 'Security Breach'),
        ('device_failure', 'Device Failure'),
        ('payment_missed', 'Payment Missed'),
        ('location_anomaly', 'Location Anomaly'),
        ('environmental_damage', 'Environmental Damage'),
        ('market_volatility', 'Market Volatility'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    collateral = models.ForeignKey(SmartCollateral, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS)
    
    # Alert content
    title = models.CharField(max_length=200)
    message = models.TextField()
    recommended_actions = models.JSONField(default=list)
    
    # AI analysis
    ai_confidence = models.DecimalField(max_digits=5, decimal_places=2)
    risk_factors = models.JSONField(default=list)
    predicted_outcome = models.TextField(blank=True)
    
    # Response tracking
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Notifications
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    push_notification_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.collateral} - {self.priority}"

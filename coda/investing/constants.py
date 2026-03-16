"""
Constants for the investing app - Single source of truth
Created: November 5, 2025
Purpose: Consolidate strategy choices, source choices, and status choices across all models
"""

# ============================================================================
# OPTIONS STRATEGY CHOICES
# ============================================================================



STRATEGY_CHOICES = [
    # Core Strategies (Phase 1-9)
    ('short_put', 'Cash-Secured Short Put'),
    ('covered_call', 'Covered Call'),
    ('short_call', 'Naked Short Call'),
    
    # Spread Strategies (Phase 9)
    ('bull_put_spread', 'Bull Put Spread'),
    ('bear_call_spread', 'Bear Call Spread'),
    
    # Advanced Spreads (Phase 10B) 
    ('bull_call_spread', 'Bull Call Spread'),  # ✨ NEW: Phase 10B
    ('bear_put_spread', 'Bear Put Spread'),
    
    # Complex Strategies
    ('iron_condor', 'Iron Condor'),
    ('iron_butterfly', 'Iron Butterfly'),
    ('calendar_spread', 'Calendar Spread'),
    ('diagonal_spread', 'Diagonal Spread'),
    
    # Long Options
    ('long_call', 'Long Call'),
    ('long_put', 'Long Put'),
    
    # Volatility Strategies
    ('straddle', 'Long Straddle'),
    ('strangle', 'Long Strangle'),
    ('short_straddle', 'Short Straddle'),
    ('short_strangle', 'Short Strangle'),
    
    # Other
    ('other', 'Other Strategy'),
]

# Strategy categories for filtering/grouping
STRATEGY_CATEGORIES = {
    'bullish': ['short_put', 'bull_put_spread', 'bull_call_spread', 'long_call'],
    'bearish': ['bear_call_spread', 'bear_put_spread', 'long_put', 'short_call'],
    'neutral': ['iron_condor', 'iron_butterfly', 'short_straddle', 'short_strangle'],
    'volatility': ['straddle', 'strangle', 'long_call', 'long_put'],
    'spreads': ['bull_put_spread', 'bear_call_spread', 'bull_call_spread', 'bear_put_spread', 
                'iron_condor', 'iron_butterfly', 'calendar_spread', 'diagonal_spread'],
}

# ============================================================================
# DATA SOURCE CHOICES
# ============================================================================

SOURCE_CHOICES = [
    ('optionplay', 'OptionPlay API'),
    ('thinkorswim', 'Thinkorswim/TD Ameritrade'),
    ('unusual_whales', 'Unusual Whales'),
    ('manual', 'Manual Entry'),
    ('imported', 'CSV Import'),
    ('ai_generated', 'AI Generated'),
]

# ============================================================================
# POSITION STATUS CHOICES
# ============================================================================

POSITION_STATUS_CHOICES = [
    # Pending States
    ('pending', 'Pending Review'),
    ('reviewing', 'Under Review'),
    
    # Approval States
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('converted', 'Converted to Position'),
    
    # Active States
    ('open', 'Open'),
    ('monitoring', 'Monitoring'),
    
    # Closed States
    ('closed', 'Closed'),
    ('expired', 'Expired'),
    ('assigned', 'Assigned'),
    ('rolled', 'Rolled to New Position'),
    
    # Error States
    ('error', 'Error'),
    ('cancelled', 'Cancelled'),
]

# ============================================================================
# SUGGESTED POSITION STATUS CHOICES (Subset for SuggestedPosition model)
# ============================================================================

SUGGESTED_POSITION_STATUS_CHOICES = [
    ('pending', 'Pending Review'),
    ('reviewing', 'Under Review'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('converted', 'Converted to Position'),
    ('expired', 'Expired'),
]

# ============================================================================
# RISK LEVEL CHOICES
# ============================================================================

RISK_LEVEL_CHOICES = [
    ('low', 'Low Risk'),
    ('medium', 'Medium Risk'),
    ('high', 'High Risk'),
    ('very_high', 'Very High Risk'),
]

# ============================================================================
# APPROVAL METHOD CHOICES
# ============================================================================

APPROVAL_METHOD_CHOICES = [
    ('batch', 'Batch Approval'),
    ('session', 'Session Pre-Approved'),
    ('manual', 'Manual Staff Approval'),
    ('auto', 'Auto-Approved'),
]

# ============================================================================
# ACCOUNT TYPE CHOICES
# ============================================================================

ACCOUNT_TYPE_CHOICES = [
    ('individual', 'Individual Account'),
    ('joint', 'Joint Account'),
    ('ira', 'IRA'),
    ('roth_ira', 'Roth IRA'),
    ('trust', 'Trust Account'),
    ('corporate', 'Corporate Account'),
]

# ============================================================================
# CONTRACT MANAGEMENT STATUS
# ============================================================================

CONTRACT_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('pending_signature', 'Pending Signature'),
    ('active', 'Active'),
    ('suspended', 'Suspended'),
    ('terminated', 'Terminated'),
    ('expired', 'Expired'),
]

# ============================================================================
# TRADING SESSION STATUS
# ============================================================================

SESSION_STATUS_CHOICES = [
    ('scheduled', 'Scheduled'),
    ('active', 'Active'),
    ('paused', 'Paused'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_strategy_display_name(strategy_code):
    """Get human-readable name for strategy code"""
    strategy_dict = dict(STRATEGY_CHOICES)
    return strategy_dict.get(strategy_code, strategy_code.replace('_', ' ').title())


def get_source_display_name(source_code):
    """Get human-readable name for source code"""
    source_dict = dict(SOURCE_CHOICES)
    return source_dict.get(source_code, source_code.replace('_', ' ').title())


def is_spread_strategy(strategy_code):
    """Check if strategy is a spread"""
    return strategy_code in STRATEGY_CATEGORIES.get('spreads', [])


def is_bullish_strategy(strategy_code):
    """Check if strategy is bullish"""
    return strategy_code in STRATEGY_CATEGORIES.get('bullish', [])


def is_bearish_strategy(strategy_code):
    """Check if strategy is bearish"""
    return strategy_code in STRATEGY_CATEGORIES.get('bearish', [])


def get_strategy_category(strategy_code):
    """Get category for a strategy (returns first matching category)"""
    for category, strategies in STRATEGY_CATEGORIES.items():
        if strategy_code in strategies:
            return category
    return 'other'


# ============================================================================
# VALIDATION CONSTANTS
# ============================================================================

# Maximum number of legs in a position
MAX_POSITION_LEGS = 4

# Maximum DTE (Days to Expiration) for standard positions
MAX_DTE_STANDARD = 60

# Maximum DTE for LEAPS (Long-term Equity Anticipation Securities)
MAX_DTE_LEAPS = 365

# LEAPS threshold (positions with DTE >= this are considered LEAPS)
LEAPS_THRESHOLD_DTE = 60

# Minimum capital required for managed account
MIN_MANAGED_ACCOUNT_CAPITAL = 10000  # $10,000

# Default max positions per batch
DEFAULT_BATCH_SIZE = 10

# Default scoring threshold for auto-approval
DEFAULT_AUTO_APPROVAL_THRESHOLD = 75  # 75 out of 100

# ============================================================================
# NOTIFICATION PREFERENCES
# ============================================================================

NOTIFICATION_CHANNEL_CHOICES = [
    ('email', 'Email'),
    ('sms', 'SMS'),
    ('whatsapp', 'WhatsApp'),
    ('telegram', 'Telegram'),
    ('push', 'Push Notification'),
]

NOTIFICATION_TYPE_CHOICES = [
    ('position_opened', 'Position Opened'),
    ('position_closed', 'Position Closed'),
    ('batch_ready', 'Batch Ready for Review'),
    ('batch_approved', 'Batch Approved'),
    ('batch_rejected', 'Batch Rejected'),
    ('risk_alert', 'Risk Alert'),
    ('margin_call', 'Margin Call'),
    ('performance_report', 'Performance Report'),
]

# ============================================================================
# MARKET CONDITION INDICATORS
# ============================================================================

MARKET_CONDITION_CHOICES = [
    ('bullish', 'Bullish'),
    ('bearish', 'Bearish'),
    ('neutral', 'Neutral'),
    ('volatile', 'Volatile'),
    ('calm', 'Calm'),
]

VIX_LEVEL_CHOICES = [
    ('low', 'Low (VIX < 15)'),
    ('medium', 'Medium (VIX 15-25)'),
    ('high', 'High (VIX 25-35)'),
    ('extreme', 'Extreme (VIX > 35)'),
]

# ============================================================================
# EXPORT FORMATS
# ============================================================================

EXPORT_FORMAT_CHOICES = [
    ('csv', 'CSV'),
    ('excel', 'Excel'),
    ('pdf', 'PDF'),
    ('json', 'JSON'),
]

# ============================================================================
# METADATA
# ============================================================================

__version__ = '1.0.0'
__last_updated__ = '2025-11-05'
__author__ = 'CODA Development Team'
__purpose__ = 'Single source of truth for all investing app constants'

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class InvestingConfig(AppConfig):
    name = "investing"
    
    def ready(self):
        """
        Initialize app: load signals for automation
        
        Signals loaded:
        - Position history auto-collection (ML training data)
        """
        try:
            # Import signals (auto-registers via @receiver decorator)
            from investing.signals import position_history_signals
            position_history_signals.load_position_history_signals()
            logger.info("✅ Investing app signals loaded successfully")
        except Exception as e:
            logger.error(f"❌ Error loading investing signals: {e}", exc_info=True)

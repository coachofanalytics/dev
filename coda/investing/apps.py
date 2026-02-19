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
        - WhatsApp/Telegram notifications (Phase 3)
        - Shareholders auto-calculation and audit trails (Phase 3)
        """
        try:
            # Import signals (auto-registers via @receiver decorator)
            from investing.signals import position_history_signals
            from investing.signals import whatsapp_notifications
            from investing.signals import shareholders_signals  # Phase 3
            
            position_history_signals.load_position_history_signals()
            logger.info("✅ Investing app signals loaded successfully")
            logger.info("📱 WhatsApp/Telegram notification signals active")
            logger.info("👥 Shareholders auto-calculation signals active")
        except Exception as e:
            logger.error(f"❌ Error loading investing signals: {e}", exc_info=True)

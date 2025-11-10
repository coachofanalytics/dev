# Twilio Alert Smoke Test Runbook

_Updated: November 2025_

Use this guide to verify SMS and WhatsApp alerts after updating credentials or deploying notification changes.

---

## 1. Prerequisites

- Twilio config vars set in Heroku (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `TWILIO_WHATSAPP_FROM`, `TRADER_ALERT_PHONES`).  
- Numbers in `TRADER_ALERT_PHONES` must be E.164 formatted (`+1...`) and enrolled in the WhatsApp sandbox if applicable.  
- Deployment includes the latest notification service (Nov 2025 release).

---

## 2. Trigger a Test SMS

1. Open a Heroku one-off shell:
   ```bash
   heroku run python manage.py shell --app codatrainingapp
   ```
2. Execute the snippet:
   ```python
   from django.conf import settings
   from investing.services.notification_service import NotificationService
   phones = getattr(settings, "TRADER_ALERT_PHONES", "").split(",")
   service = NotificationService()
   for phone in [p.strip() for p in phones if p.strip()]:
       service.send_sms_notification(phone, "CODA test: SMS alert wiring successful.")
   exit()
   ```
3. Confirm receipt on each phone and note the message SID in Heroku logs (`heroku logs --tail --app codatrainingapp`).

---

## 3. Trigger a Test WhatsApp Message

1. Ensure `WHATSAPP_ENABLED=true` and `TWILIO_WHATSAPP_FROM=whatsapp:+1##########` are set.  
2. From the same shell session:
   ```python
   from django.conf import settings
   from investing.services.notification_service import NotificationService
   phones = getattr(settings, "TRADER_ALERT_PHONES", "").split(",")
   service = NotificationService()
   for phone in [p.strip() for p in phones if p.strip()]:
       service.send_whatsapp_message(
           phone,
           "auto_suggestions",
           {"summary": "Test message", "count": 0}
       )
   exit()
   ```
3. Verify the WhatsApp messages arrive and check Twilio logs for delivery status.

---

## 4. Production Regression Check

- Run `python manage.py process_batch_approvals` in a one-off dyno to ensure automated flows still send alerts.  
- Watch logs for `✅ SMS sent` / `✅ WhatsApp sent` entries.  
- If any phone misses alerts, confirm Twilio’s messaging console for delivery errors (e.g., opt-in required).

---

## 5. Rollback Procedure

If alerts fail after deployment:

1. Revert the deployment or set `TRADER_ALERT_PHONES` to blank to suppress sends.  
2. Restore previous Twilio credentials if the token changed.  
3. Re-run the smoke test after fixes.

---

Document test results in the operations checklist (`/Shared/Ops/Twilio-Smoke-Tests.md`) for compliance.




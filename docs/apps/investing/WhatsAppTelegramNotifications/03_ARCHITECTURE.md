# WhatsApp/Telegram Notifications - Architecture
**Phase 3: Real-Time Client Alerts**  
**Date**: November 2, 2025

---

## 1. SYSTEM OVERVIEW

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    CODA Investment Platform                      │
│                                                                  │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │ OptionsPosition│ ──────>│ Django Signals│                     │
│  │   (Model)     │         │              │                     │
│  └──────────────┘         └───────┬──────┘                     │
│                                    │                             │
│                                    v                             │
│                          ┌─────────────────┐                    │
│                          │ NotificationService                  │
│                          │  (Business Logic)                     │
│                          └────────┬────────┘                    │
│                                   │                              │
│             ┌─────────────────────┼────────────────────┐        │
│             v                     v                     v        │
│      ┌──────────┐        ┌──────────┐         ┌──────────┐    │
│      │ WhatsApp │        │ Telegram │         │  Email   │    │
│      │  (Twilio)│        │ (Bot API)│         │(Existing)│    │
│      └────┬─────┘        └────┬─────┘         └──────────┘    │
└───────────┼───────────────────┼───────────────────────────────┘
            │                   │
            v                   v
     ┌────────────┐      ┌────────────┐
     │ Client's   │      │ Client's   │
     │ WhatsApp   │      │ Telegram   │
     └────────────┘      └────────────┘
```

---

## 2. COMPONENT ARCHITECTURE

### **2.1 Models Layer**

**File**: `coda/investing/models.py`

```python
class ManagedTradingAccount(TimeStampedModel):
    """
    Client account with notification preferences
    """
    # Existing fields...
    
    # Phase 3: WhatsApp/Telegram Notifications
    whatsapp_enabled = BooleanField(default=False)
    whatsapp_phone = CharField(max_length=20, blank=True)
    telegram_enabled = BooleanField(default=False)
    telegram_chat_id = CharField(max_length=50, blank=True)
```

**Responsibilities**:
- Store notification preferences
- Link to client user
- Provide enable/disable flags

---

### **2.2 Signals Layer**

**File**: `coda/investing/signals/whatsapp_notifications.py`

```python
@receiver(post_save, sender=OptionsPosition)
def notify_position_status_change(sender, instance, created, **kwargs):
    """
    Automatic notification when position status changes
    """
    if created and instance.status == 'open':
        # Send position opened notification
    elif instance.status == 'closed':
        # Send position closed notification (win/loss)
```

**Responsibilities**:
- Listen for model changes
- Determine notification type
- Call NotificationService
- Handle errors gracefully

**Design Pattern**: Observer Pattern (Django Signals)

---

### **2.3 Service Layer**

**File**: `coda/investing/services/notification_service.py`

```python
class NotificationService:
    """
    Centralized notification sending service
    """
    
    def send_whatsapp_message(phone, template_name, params):
        """Send WhatsApp via Twilio"""
    
    def send_telegram_message(chat_id, message):
        """Send Telegram via Bot API"""
    
    def _format_whatsapp_template(template_name, params):
        """Format message from template"""
```

**Responsibilities**:
- Send WhatsApp messages (Twilio)
- Send Telegram messages (Bot API)
- Format messages from templates
- Handle API errors
- Log all activity

**Design Pattern**: Service Layer + Template Method

---

### **2.4 Admin Layer**

**File**: `coda/investing/admin.py`

```python
class ManagedTradingAccountAdmin(admin.ModelAdmin):
    fieldsets = (
        # ... existing fieldsets ...
        ('Notification Preferences (WhatsApp/Telegram)', {
            'fields': (
                'whatsapp_enabled', 'whatsapp_phone',
                'telegram_enabled', 'telegram_chat_id'
            )
        }),
    )
```

**Responsibilities**:
- Provide UI for staff configuration
- Validate phone numbers
- Enable/disable per account

---

## 3. DATA FLOW

### **3.1 Position Opened Flow**

```
1. Staff creates OptionsPosition with status='open'
   │
   v
2. Django saves to database
   │
   v
3. post_save signal fires
   │
   v
4. Signal handler checks: created=True AND status='open'
   │
   v
5. Signal calls NotificationService.send_whatsapp_message()
   │
   v
6. NotificationService checks: account.whatsapp_enabled?
   │
   ├─ YES → Format message from template
   │         Call Twilio API
   │         Log success/failure
   │
   └─ NO  → Skip, log "WhatsApp disabled"
   │
   v
7. Client receives WhatsApp message (2-5 seconds)
```

---

### **3.2 Position Closed Flow**

```
1. Staff updates OptionsPosition:
   - status = 'closed'
   - realized_pnl = 150.00  (or negative for loss)
   │
   v
2. Django saves to database
   │
   v
3. post_save signal fires (created=False)
   │
   v
4. Signal handler checks: status='closed' AND realized_pnl is not None
   │
   v
5. Signal determines: Win or Loss?
   │
   ├─ Win (realized_pnl > 0)
   │   └─> Template: 'position_profit'
   │       Message: "✅ WINNER! +$150 (15%)"
   │
   └─ Loss (realized_pnl < 0)
       └─> Template: 'position_loss'
           Message: "⚠️ Position Closed -$50"
   │
   v
6. NotificationService sends WhatsApp/Telegram
   │
   v
7. Client receives instant P&L notification
```

---

## 4. MESSAGE TEMPLATES

### **4.1 Template Structure**

```python
templates = {
    'position_opened': """
🟢 *NEW POSITION OPENED*

Symbol: {symbol}
Strategy: {strategy}
Premium: ${premium}
DTE: {dte} days

Your position is now active!
    """,
    
    'position_profit': """
✅ *WINNER!*

{symbol} closed at +${profit} ({roi}% return)

Premium: ${premium}
Days held: {days_held}
Annualized: {annualized_return}%

Great trade! 🎉
    """,
    
    # ... more templates ...
}
```

**Template Variables**:
- Injected at runtime from OptionsPosition data
- Type-safe (all converted to strings)
- Error handling for missing variables

---

## 5. EXTERNAL INTEGRATIONS

### **5.1 Twilio WhatsApp Integration**

**API Endpoint**: `https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages.json`

**Request**:
```python
client.messages.create(
    from_='whatsapp:+14155238886',  # Twilio sandbox
    body=message_body,
    to=f'whatsapp:{phone_number}'   # Client phone
)
```

**Authentication**: HTTP Basic Auth (SID + Token)

**Response**:
```json
{
    "sid": "SMxxxxxxxxxxxxxxx",
    "status": "queued",
    "to": "whatsapp:+14174137966"
}
```

**Error Handling**:
- Connection errors → Log and skip
- Invalid phone → Log error
- API errors → Retry once, then log

---

### **5.2 Telegram Bot Integration**

**API Endpoint**: `https://api.telegram.org/bot{TOKEN}/sendMessage`

**Request**:
```python
requests.post(
    f"https://api.telegram.org/bot{bot_token}/sendMessage",
    json={
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
)
```

**Authentication**: Bot token in URL

**Response**:
```json
{
    "ok": true,
    "result": {
        "message_id": 123,
        "chat": {"id": 123456789}
    }
}
```

---

## 6. SECURITY ARCHITECTURE

### **6.1 Credential Management**

**Storage**:
```
Heroku Config Vars (Environment Variables)
├─ TWILIO_ACCOUNT_SID (encrypted by Heroku)
├─ TWILIO_AUTH_TOKEN (encrypted by Heroku)
├─ TELEGRAM_BOT_TOKEN (encrypted by Heroku)
└─ WHATSAPP_ENABLED (boolean flag)
```

**Access Control**:
- Never committed to git
- Only accessible via Heroku CLI or dashboard
- Injected at runtime via `os.environ`

---

### **6.2 Phone Number Security**

**Database**:
- Stored in `ManagedTradingAccount.whatsapp_phone`
- PostgreSQL encrypted at rest (Heroku default)
- SSL connection to database

**Access Control**:
- Admin-only access
- No API exposure
- Audit logging (Django admin history)

---

### **6.3 API Security**

**Twilio**:
- HTTPS only
- Token-based authentication
- Rate limiting (Twilio-side)

**Telegram**:
- HTTPS only
- Bot token authentication
- No webhooks (polling not used)

---

## 7. ERROR HANDLING

### **7.1 Error Scenarios**

| Error | Handling Strategy |
|-------|------------------|
| **Twilio API down** | Log error, skip WhatsApp, don't crash |
| **Invalid phone number** | Log error, continue processing |
| **Telegram bot blocked** | Log error, skip Telegram |
| **Network timeout** | Retry once (5s timeout), then skip |
| **No credentials set** | Log "WhatsApp disabled", skip gracefully |

---

### **7.2 Logging Strategy**

```python
# Success
logger.info(f"✅ WhatsApp sent to {phone} for {position.symbol}")

# Warning (disabled)
logger.warning(f"WhatsApp disabled - would send to {phone}")

# Error (failed)
logger.error(f"❌ WhatsApp failed to {phone}: {error}")
```

**Log Destination**: Heroku logs (`heroku logs --tail`)

---

## 8. SCALABILITY

### **8.1 Current Capacity**

**Target**: 10 clients  
**Max Throughput**: 100 messages/minute (Twilio limit)  
**Expected Load**: ~40 messages/day (10 clients × 4 positions/day)

**Bottlenecks**: None (API-based, async-capable)

---

### **8.2 Scaling Strategy**

**0-50 Clients**:
- Current architecture sufficient
- Twilio sandbox OK
- No changes needed

**50-100 Clients**:
- Upgrade to production WhatsApp (templates)
- Consider Celery for async sending
- Add rate limiting

**100+ Clients**:
- Celery required (async task queue)
- Redis for queue management
- Load balancing across Twilio numbers

---

## 9. DEPLOYMENT ARCHITECTURE

### **9.1 Environment Configuration**

```
Development (Local)
├─ SQLite or PostgreSQL clone
├─ Twilio sandbox
├─ Test phone numbers
└─ Debug logging

UAT (Heroku)
├─ PostgreSQL (Heroku Postgres)
├─ Twilio sandbox
├─ Staff phone numbers
└─ Info logging

Production (Future)
├─ PostgreSQL (Heroku Postgres)
├─ Twilio production WhatsApp
├─ Client phone numbers
└─ Warning logging
```

---

### **9.2 Migration Strategy**

**File**: `investing/migrations/0011_add_whatsapp_telegram_notifications.py`

```python
operations = [
    migrations.AddField(
        model_name='managedtradingaccount',
        name='whatsapp_enabled',
        field=models.BooleanField(default=False),
    ),
    # ... other fields ...
]
```

**Backward Compatibility**: ✅ Safe (all fields have defaults)

---

## 10. MONITORING & OBSERVABILITY

### **10.1 Metrics to Track**

**Delivery Metrics**:
- Messages sent (count)
- Delivery rate (%)
- Average latency (seconds)
- Error rate (%)

**Business Metrics**:
- Clients with WhatsApp enabled
- Clients with Telegram enabled
- Messages per client per day

**Technical Metrics**:
- API response time
- Error types
- Retry attempts

---

### **10.2 Logging Points**

```
1. Signal fired → "📱 Sending notification for {position}"
2. Service called → "Calling WhatsApp API for {phone}"
3. API success → "✅ WhatsApp sent: {message_sid}"
4. API error → "❌ WhatsApp failed: {error}"
```

---

## 11. TESTING ARCHITECTURE

### **11.1 Test Infrastructure**

**Management Command**: `test_whatsapp_notifications`

**Test Flow**:
```
1. Create test account (TEST-WHATSAPP-001)
2. Create position → Trigger 'opened' signal
3. Close position (win) → Trigger 'profit' signal
4. Close position (loss) → Trigger 'loss' signal
5. Direct service call → Test API directly
```

**Test Coverage**:
- ✅ Signal handlers
- ✅ Service methods
- ✅ Template formatting
- ✅ Error handling

---

## 12. FUTURE ENHANCEMENTS

### **12.1 Phase 4 (Future)**

- [ ] Celery async task queue
- [ ] Redis for caching
- [ ] Custom templates per client
- [ ] Multi-language support
- [ ] Metrics dashboard
- [ ] Automated retries
- [ ] Delivery confirmation tracking

---

**Architecture Status**: ✅ Complete and Production-Ready  
**Last Updated**: November 2, 2025  
**Version**: 1.0


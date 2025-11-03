# WhatsApp/Telegram Setup Guide
## Real-Time Position Alerts for Clients

**Phase 3 Implementation - November 2, 2025**

---

## 🎯 **Overview**

Enable instant WhatsApp and Telegram notifications for:
- ✅ Position opened alerts
- ✅ Position closed (win/loss) with P&L
- ✅ Batch approval requests
- ✅ Batch reminders

**Client receives**: Instant push notifications on their phone!

---

## 📱 **WHATSAPP SETUP**

### **Option 1: Twilio WhatsApp Sandbox (FREE - Testing)**

**Best for**: Testing, UAT, small deployments

**Steps**:
1. Create Twilio account: https://www.twilio.com/try-twilio
2. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
3. Send "join <your-sandbox-code>" to Twilio WhatsApp number
4. Get credentials:
   - Account SID: `ACxxxxxxxxxxxxxxxxxx`
   - Auth Token: `your_auth_token`
   - WhatsApp From: `whatsapp:+14155238886`

**Heroku Config**:
```bash
heroku config:set WHATSAPP_ENABLED=True --app codamakutano
heroku config:set TWILIO_ACCOUNT_SID=ACxxxxxxxxx --app codamakutano
heroku config:set TWILIO_AUTH_TOKEN=your_token --app codamakutano
heroku config:set TWILIO_WHATSAPP_FROM="whatsapp:+14155238886" --app codamakutano
```

**Limitations**:
- Only works with phones that join sandbox
- "join <code>" message required first
- Good for testing only

---

### **Option 2: Twilio WhatsApp Business API (PRODUCTION)**

**Best for**: Production with many clients

**Steps**:
1. Apply for WhatsApp Business API: https://www.twilio.com/whatsapp
2. Get approved WhatsApp Business profile
3. Submit message templates for approval
4. Get production credentials

**Message Templates to Submit**:
```
Template Name: position_opened
Language: English
Category: Account Update
Body:
NEW POSITION OPENED
Symbol: {{1}}
Strategy: {{2}}
Premium: ${{3}}
Max Profit: ${{4}}
DTE: {{5}} days
Your position is now active!

---

Template Name: position_closed_win
Language: English
Category: Account Update
Body:
WINNER!
{{1}} closed at +${{2}} ({{3}}% return)
Premium collected: ${{4}}
Held for: {{5}} days
Annualized: {{6}}%
Great trade! 🎉

---

Template Name: position_closed_loss
Language: English
Category: Account Update
Body:
Position Closed
{{1}}: ${{2}} loss ({{3}}%)
This position didn't work out, but it's part of the strategy.
Overall portfolio performance remains strong.
Next positions coming soon!

---

Template Name: batch_approval
Language: English
Category: Account Update
Body:
NEW POSITIONS READY
{{1}} positions need your approval!
Total Capital: ${{2}}
Approval Deadline: {{3}}
Click to review: {{4}}
Approve within 24 hours!
```

**Cost**: ~$0.005/message (very affordable!)

---

## 💬 **TELEGRAM SETUP**

### **Step 1: Create Bot**

1. Open Telegram app
2. Search for `@BotFather`
3. Send `/newbot`
4. Follow prompts:
   - Bot name: `CODA Investment Alerts`
   - Username: `coda_investment_bot` (must end in 'bot')
5. Copy the bot token: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### **Step 2: Get Chat ID**

**For Direct Messages**:
1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find `"chat":{"id":123456789}`
4. That's your chat ID!

**For Group Chats**:
1. Add bot to group
2. Send a message in group
3. Visit same URL
4. Look for `"chat":{"id":-123456789}` (negative for groups)

### **Step 3: Configure Heroku**

```bash
heroku config:set TELEGRAM_ENABLED=True --app codamakutano
heroku config:set TELEGRAM_BOT_TOKEN=123456789:ABCdefGHI --app codamakutano
```

**Cost**: FREE! ✅

---

## ⚙️ **HEROKU CONFIGURATION**

### **Full Config Vars**:
```bash
# WhatsApp (Twilio)
WHATSAPP_ENABLED=True
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Telegram
TELEGRAM_ENABLED=True
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Site URL (for links in messages)
SITE_URL=https://codamakutano.herokuapp.com
```

### **Set on Heroku**:
```bash
# Copy-paste this entire block
heroku config:set \
  WHATSAPP_ENABLED=True \
  TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxx \
  TWILIO_AUTH_TOKEN=your_token \
  TWILIO_WHATSAPP_FROM="whatsapp:+14155238886" \
  TELEGRAM_ENABLED=True \
  TELEGRAM_BOT_TOKEN=123456789:ABCdefGHI \
  SITE_URL=https://codamakutano.herokuapp.com \
  --app codamakutano
```

---

## 🧪 **TESTING**

### **Local Testing**:
```bash
cd coda

# Test WhatsApp only
python manage.py test_whatsapp_notifications --phone "+1234567890"

# Test Telegram only
python manage.py test_whatsapp_notifications --telegram 123456789

# Test both
python manage.py test_whatsapp_notifications --phone "+1234567890" --telegram 123456789

# Dry run (no actual messages)
python manage.py test_whatsapp_notifications --phone "+1234567890" --dry-run
```

### **What Happens**:
1. Creates test account `TEST-WHATSAPP-001`
2. Creates test position (AAPL) → **Position Opened alert sent**
3. Closes position with profit → **WIN alert sent**
4. Creates/closes TSLA with loss → **LOSS alert sent**
5. Tests direct NotificationService calls

**Check your phone!** 📱

---

## 🔧 **ENABLE FOR CLIENTS**

### **Admin Interface**:
1. Go to: http://localhost:8080/admin/investing/managedtradingaccount/
2. Select client account
3. Scroll to "Notification Preferences (WhatsApp/Telegram)"
4. Check boxes:
   - ☑️ `whatsapp_enabled`
   - Enter `whatsapp_phone`: `+1234567890`
   - ☑️ `telegram_enabled`
   - Enter `telegram_chat_id`: `123456789`
5. Save

**Done!** Client will now receive alerts!

---

## 📊 **NOTIFICATION TRIGGERS**

### **Automatic Notifications** (via signals):

| Event | Trigger | Message Type |
|-------|---------|--------------|
| **Position Opened** | `OptionsPosition` created with `status='open'` | `position_opened` |
| **Position Closed (Win)** | `OptionsPosition.status` → `'closed'` with `realized_pnl > 0` | `position_profit` |
| **Position Closed (Loss)** | `OptionsPosition.status` → `'closed'` with `realized_pnl < 0` | `position_loss` |
| **Batch Created** | `PositionBatch` created | `batch_approval` |

**All automatic!** No manual intervention needed!

---

## 🎨 **MESSAGE EXAMPLES**

### **Position Opened**:
```
🟢 NEW POSITION OPENED

Symbol: AAPL
Strategy: Bull Put Spread
Contracts: 1
Premium: $250.00
Max Profit: $250.00
DTE: 45 days

Your position is now active!
```

### **Position Closed (Win)**:
```
✅ WINNER!

AAPL closed at +$150.00 (15.0% return)

Premium collected: $250.00
Held for: 30 days
Annualized: 182%

Great trade! 🎉
```

### **Position Closed (Loss)**:
```
⚠️ Position Closed

TSLA: $50.00 loss (-5.0%)

This position didn't work out, but it's part of the strategy.
Overall portfolio performance remains strong.

Next positions coming soon!
```

### **Batch Approval**:
```
📦 NEW POSITIONS READY

5 positions need your approval!

Total Capital: $2,500.00
Approval Deadline: November 3 at 5:00 PM

Click to review:
https://codamakutano.herokuapp.com/investing/managed/portal/approvals/batch/5/

Approve within 24 hours!
```

---

## 🐛 **TROUBLESHOOTING**

### **WhatsApp Not Sending**:
1. Check Heroku logs: `heroku logs --tail --app codamakutano`
2. Verify config: `heroku config --app codamakutano | grep WHATSAPP`
3. Check Twilio console for errors
4. Ensure phone joined sandbox (for testing)

### **Telegram Not Sending**:
1. Check logs for errors
2. Verify bot token is correct
3. Ensure bot is not blocked by user
4. Test with: `curl https://api.telegram.org/bot<TOKEN>/getMe`

### **No Notifications**:
1. Check `whatsapp_enabled` / `telegram_enabled` in admin
2. Verify phone/chat_id is correct
3. Check signals are loaded: Look for "📱 WhatsApp/Telegram notification signals active" in logs
4. Run test command: `python manage.py test_whatsapp_notifications`

---

## 💰 **COST ANALYSIS**

### **WhatsApp (Twilio)**:
- **Sandbox**: FREE (testing only)
- **Production**: ~$0.005/message
- **Example**: 100 clients × 10 messages/month = 1,000 messages = **$5/month**

### **Telegram**:
- **Always FREE!** ✅
- Unlimited messages
- No cost ever

**Recommendation**: Use Telegram for cost-free alerts, WhatsApp for premium clients!

---

## 🚀 **DEPLOYMENT CHECKLIST**

- [ ] Twilio account created
- [ ] WhatsApp sandbox joined (for testing)
- [ ] Telegram bot created
- [ ] Bot token obtained
- [ ] Heroku config vars set
- [ ] Test command run successfully
- [ ] Messages received on phone
- [ ] Client accounts configured
- [ ] Production WhatsApp templates submitted (optional)
- [ ] Documentation updated

---

## 📚 **CODE REFERENCE**

**Models**: `coda/investing/models.py`
- `ManagedTradingAccount.whatsapp_enabled`
- `ManagedTradingAccount.whatsapp_phone`
- `ManagedTradingAccount.telegram_enabled`
- `ManagedTradingAccount.telegram_chat_id`

**Services**: `coda/investing/services/notification_service.py`
- `send_whatsapp_message(phone, template, params)`
- `send_telegram_message(chat_id, message)`

**Signals**: `coda/investing/signals/whatsapp_notifications.py`
- `notify_position_status_change` - Position open/close
- `notify_batch_created` - Batch approval

**Admin**: `coda/investing/admin.py`
- `ManagedTradingAccountAdmin` - Notification preferences fieldset

---

## 🎯 **NEXT STEPS**

1. **Set up Twilio sandbox** (5 min)
2. **Create Telegram bot** (5 min)
3. **Configure Heroku** (2 min)
4. **Run test command** (1 min)
5. **Verify messages received** (instant!)
6. **Enable for first client** (2 min)
7. **Deploy to production** (5 min)

**Total time**: 20 minutes to go live! 🚀

---

**Phase 3: WhatsApp/Telegram Alerts**  
**Status**: Ready for deployment!  
**Date**: November 2, 2025


# WhatsApp/Telegram Notifications - Maintenance
**Phase 3: Real-Time Client Alerts**  
**Date**: November 2, 2025

---

## 1. ROUTINE MAINTENANCE

### **1.1 Weekly Tasks**
- Check Heroku logs for errors
- Verify message delivery rate (>99%)
- Monitor Twilio usage/costs
- Review client feedback

### **1.2 Monthly Tasks**
- Update Twilio credentials if changed
- Review and optimize message templates
- Check for API updates
- Verify sandbox renewals (72hr expiry)

---

## 2. MONITORING

### **2.1 Key Metrics**
- Messages sent/day
- Delivery success rate
- Average latency
- Error rate
- Cost per month

### **2.2 Heroku Logs**
```bash
heroku logs --tail --app codamakutano | findstr "WhatsApp"
```

**Look for**:
- ✅ "WhatsApp sent successfully"
- ⚠️ "WhatsApp disabled"
- ❌ "WhatsApp failed"

---

## 3. COMMON MAINTENANCE TASKS

### **3.1 Update Twilio Credentials**
```bash
heroku config:set TWILIO_ACCOUNT_SID=new_sid TWILIO_AUTH_TOKEN=new_token --app codamakutano
```

### **3.2 Update Message Templates**
- Edit `notification_service.py`
- Update template strings
- Test with dry-run
- Deploy

### **3.3 Add New Client**
1. Admin → Managed Trading Accounts
2. Select account
3. Enable WhatsApp, enter phone
4. Instruct client to join sandbox
5. Test with first position

---

## 4. TROUBLESHOOTING GUIDE

### **4.1 Messages Not Sending**
1. Check Heroku config vars set
2. Check Twilio credentials valid
3. Check account WhatsApp enabled
4. Check phone number format
5. Check Heroku logs

### **4.2 Sandbox Expiry**
- **Issue**: Client stops receiving messages after 72 hours
- **Fix**: Client sends "join <code>" again
- **Prevention**: Document renewal process

### **4.3 API Rate Limits**
- **Issue**: Too many messages too fast
- **Limit**: 100 messages/minute (Twilio)
- **Fix**: Implement rate limiting or Celery queue

---

## 5. BACKUP & RECOVERY

### **5.1 Configuration Backup**
```bash
heroku config --app codamakutano > heroku_config_backup.txt
```

### **5.2 Code Backup**
- All code in git (already backed up)
- No local-only configurations

---

## 6. SCALING CONSIDERATIONS

### **6.1 Current Capacity**
- 10 clients
- ~40 messages/day
- Free sandbox

### **6.2 Future Scaling**
- 50+ clients → Consider production WhatsApp
- 100+ clients → Implement Celery async queue
- 500+ clients → Load balancing, multiple Twilio numbers

---

## 7. COST MANAGEMENT

### **7.1 Current Costs**
- Sandbox: FREE
- Telegram: FREE forever
- Total: $0/month

### **7.2 Production Costs** (if upgraded)
- WhatsApp: ~$0.005/message
- 10 clients × 4 messages/day × 30 days = 1,200 messages = $6/month

---

## 8. SECURITY MAINTENANCE

### **8.1 Credential Rotation**
- Rotate Twilio credentials quarterly
- Update Heroku config vars
- Test after rotation

### **8.2 Access Control**
- Only admins can enable WhatsApp
- Only admins can see phone numbers
- Review admin access monthly

---

## 9. DOCUMENTATION UPDATES

### **9.1 When to Update Docs**
- New template added
- New trigger added
- API changes
- Cost structure changes

### **9.2 Documentation Location**
- `docs/apps/investing/WhatsAppTelegramNotifications/`
- `coda/docs/` (temporary guides)

---

## 10. SUPPORT CONTACTS

### **10.1 Twilio Support**
- Dashboard: https://console.twilio.com/
- Docs: https://www.twilio.com/docs/whatsapp
- Support: https://support.twilio.com/

### **10.2 Telegram Support**
- Bot docs: https://core.telegram.org/bots/api
- @BotSupport on Telegram

---

**Maintenance Status**: ✅ Low-effort (mostly automated)  
**Last Updated**: November 2, 2025


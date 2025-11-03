# ⚡ Quick Twilio Setup - 3 Minutes!

**Your Account**: coachofanalytics@gmail.com  
**Password**: @ZK321sebe  

---

## 🚀 **3-MINUTE SETUP**

### **1. Get Credentials** (1 min)

**Go to**: https://console.twilio.com/

**What to copy**:
1. **Account SID**: Starts with `AC...` (under "Account Info")
2. **Auth Token**: Click "Show" then copy

---

### **2. Join WhatsApp Sandbox** (1 min)

**Go to**: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn

**What to do**:
1. You'll see: "Send `join <your-code>` to `+1 415 523 8886`"
2. Open WhatsApp
3. Send that exact message to `+1 415 523 8886`
4. You'll get a confirmation!

---

### **3. Set Heroku Config** (1 min)

**Copy this command** (replace `ACxxx` and `your_token` with YOUR values):

```bash
heroku config:set WHATSAPP_ENABLED=True TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxx TWILIO_AUTH_TOKEN=your_actual_token TWILIO_WHATSAPP_FROM="whatsapp:+14155238886" --app codamakutano
```

---

### **4. Test!** (30 sec)

```bash
heroku run "cd coda && python manage.py test_whatsapp_notifications --phone '+YOUR_PHONE'" --app codamakutano
```

Replace `+YOUR_PHONE` with your phone number (e.g., `+254712345678`)

**Check WhatsApp** - you should get messages! 📱

---

## ✅ **DONE!**

WhatsApp alerts are now LIVE! 🎉

**Next**: Enable for first client in admin!


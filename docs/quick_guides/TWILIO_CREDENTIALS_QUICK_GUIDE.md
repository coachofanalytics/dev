# Twilio Credentials - Quick Setup Guide
## Get Your WhatsApp Credentials in 3 Minutes!

**Account**: coachofanalytics@gmail.com  
**Goal**: Get credentials for WhatsApp notifications  

---

## 🚀 **STEP-BY-STEP GUIDE**

### **Step 1: Login to Twilio** (30 seconds)
1. Go to: https://www.twilio.com/login
2. Email: `coachofanalytics@gmail.com`
3. Password: `@ZK321sebe`
4. Click "Log In"

---

### **Step 2: Get Account Credentials** (1 minute)

**Once logged in, you'll see the Dashboard:**

1. **Look for the top section** that says **"Account Info"**
2. You'll see:
   - **Account SID**: Starts with `AC...` (e.g., `ACxxxxxxxxxxxxxxxxxxxxxxxx`)
   - **Auth Token**: Click "Show" to reveal (long string of letters/numbers)

**Copy these two values!**

**Example**:
```
Account SID: AC1234567890abcdef1234567890abcd
Auth Token: 1234567890abcdef1234567890abcdef
```

---

### **Step 3: Set Up WhatsApp Sandbox** (1 minute)

**For Testing (FREE)**:

1. In Twilio Console, go to: **Messaging** → **Try it out** → **Send a WhatsApp message**
   
   Or direct link: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn

2. You'll see:
   - **Sandbox phone number**: `+1 415 523 8886` (Twilio's WhatsApp number)
   - **Your sandbox code**: Something like `join happy-tiger`

3. **Join the sandbox**:
   - Open WhatsApp on your phone
   - Send a message to: `+1 415 523 8886`
   - Message content: `join happy-tiger` (use YOUR code from step 2)
   - You'll get a confirmation!

**WhatsApp From Number**: `whatsapp:+14155238886`

---

### **Step 4: Configure Heroku** (1 minute)

**Copy-paste this command** (replace with YOUR values):

```bash
heroku config:set \
  WHATSAPP_ENABLED=True \
  TWILIO_ACCOUNT_SID=AC1234567890abcdef1234567890abcd \
  TWILIO_AUTH_TOKEN=1234567890abcdef1234567890abcdef \
  TWILIO_WHATSAPP_FROM="whatsapp:+14155238886" \
  --app codamakutano
```

**Replace**:
- `AC1234567890abcdef1234567890abcd` → Your actual Account SID
- `1234567890abcdef1234567890abcdef` → Your actual Auth Token

---

### **Step 5: Test!** (30 seconds)

**Get your phone number** (the one you used to join sandbox):
- Format: `+1234567890` (international format)

**Run test command**:
```bash
heroku run "cd coda && python manage.py test_whatsapp_notifications --phone '+1234567890'" --app codamakutano
```

**Replace** `+1234567890` with YOUR phone number!

**Check your WhatsApp** - you should receive test messages! 📱

---

## 📋 **QUICK CHECKLIST**

- [ ] Login to Twilio Console
- [ ] Copy Account SID (starts with `AC...`)
- [ ] Copy Auth Token (click "Show")
- [ ] Join WhatsApp sandbox (send message to +1 415 523 8886)
- [ ] Configure Heroku with credentials
- [ ] Test with your phone number
- [ ] Receive WhatsApp messages! ✅

---

## 🔍 **WHERE TO FIND CREDENTIALS**

### **Twilio Console Dashboard** (https://console.twilio.com/)

```
┌────────────────────────────────────────────┐
│  Account Info                              │
│  ────────────────────                      │
│  Account SID:  AC1234567... [Copy]         │ ← COPY THIS!
│  Auth Token:   ************ [Show]         │ ← CLICK "SHOW", THEN COPY!
└────────────────────────────────────────────┘
```

### **WhatsApp Sandbox** (https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn)

```
┌────────────────────────────────────────────┐
│  Try WhatsApp                              │
│  ────────────                              │
│  Your Sandbox Phone Number:                │
│  +1 415 523 8886                           │
│                                            │
│  To connect, send:                         │
│  join happy-tiger                          │ ← YOUR CODE (will be different!)
└────────────────────────────────────────────┘
```

---

## ⚡ **SUPER QUICK VERSION**

1. **Login**: https://www.twilio.com/login
2. **Copy SID + Token** from dashboard
3. **Join sandbox**: Send "join <code>" to `+1 415 523 8886` on WhatsApp
4. **Set Heroku vars**: 
   ```bash
   heroku config:set WHATSAPP_ENABLED=True TWILIO_ACCOUNT_SID=ACxxx TWILIO_AUTH_TOKEN=xxx --app codamakutano
   ```
5. **Test**: 
   ```bash
   heroku run "cd coda && python manage.py test_whatsapp_notifications --phone '+YOUR_NUMBER'" --app codamakutano
   ```

**Done!** 🎉

---

## 💡 **TIPS**

- **Account SID**: Always starts with `AC`
- **Auth Token**: Long random string (keep secret!)
- **Phone Format**: Must be international (e.g., `+1234567890`)
- **Sandbox**: FREE but requires users to join first
- **Production**: Need to apply for WhatsApp Business API (not needed for testing!)

---

## 🐛 **TROUBLESHOOTING**

**Can't find Account SID/Token?**
- Go to: https://console.twilio.com/
- Look for "Account Info" panel (usually top right)
- Click "Show" next to Auth Token

**WhatsApp message not received?**
- Did you join the sandbox? (send "join <code>")
- Is your phone number in international format? (`+1...`)
- Check Twilio Console → Monitor → Logs for errors

**Heroku config not working?**
- Verify vars are set: `heroku config --app codamakutano | grep TWILIO`
- Restart dynos: `heroku restart --app codamakutano`

---

## 🎯 **WHAT YOU NEED**

| Item | Where to Find | Example |
|------|---------------|---------|
| **Account SID** | Twilio Dashboard → Account Info | `AC1234567890abcdef...` |
| **Auth Token** | Twilio Dashboard → Account Info → Show | `1234567890abcdef...` |
| **WhatsApp From** | WhatsApp Sandbox page | `whatsapp:+14155238886` |
| **Your Phone** | Your phone! | `+1234567890` |

---

## ✅ **READY TO GO!**

**Once you have**:
- ✅ Account SID
- ✅ Auth Token
- ✅ Joined WhatsApp sandbox
- ✅ Set Heroku config

**You can**:
- Send WhatsApp notifications to clients
- Test position alerts
- Enable for managed accounts
- **Go live!** 🚀

---

**Total Time**: 3 minutes  
**Cost**: FREE (sandbox)  
**Result**: Instant WhatsApp alerts! 📱

**Good luck!** 🎉


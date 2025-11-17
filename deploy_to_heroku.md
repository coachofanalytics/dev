# 🚀 Heroku Deployment Commands - Quick Reference

## ✅ Your project is now Heroku-ready!

All necessary files have been configured:
- ✅ Procfile
- ✅ runtime.txt
- ✅ requirements.txt (with dj-database-url)
- ✅ settings.py (WhiteNoise, Heroku database, static files)
- ✅ .gitignore

---

## 📝 Step-by-Step Commands

### 1. Login to Heroku

```bash
heroku login
```

Press any key to open browser and login.

---

### 2. Create Heroku App

```bash
cd C:\Users\Mwongela\projects\biashara_bridges
heroku create biashara-bridges
```

**Note the app URL** that Heroku provides (e.g., `https://biashara-bridges.herokuapp.com`)

---

### 3. Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:essential-0
```

This adds a PostgreSQL database to your app.

---

### 4. Set Environment Variables

```bash
heroku config:set DEBUG=False
heroku config:set SECRET_KEY="your-random-secret-key-change-this-in-production"
heroku config:set ALLOWED_HOSTS=".herokuapp.com"
heroku config:set ENABLE_STRIPE=True
heroku config:set ENABLE_PAYPAL=True
heroku config:set ENABLE_MPESA=False
heroku config:set ENABLE_WALLET_PAYMENTS=True
```

**Optional - Add payment gateway keys later:**
```bash
heroku config:set STRIPE_PUBLIC_KEY="pk_test_your_key"
heroku config:set STRIPE_SECRET_KEY="sk_test_your_key"
heroku config:set PAYPAL_CLIENT_ID="your_id"
heroku config:set PAYPAL_CLIENT_SECRET="your_secret"
```

---

### 5. Initialize Git (if not already done)

```bash
git init
git add .
git commit -m "Initial Heroku deployment"
```

---

### 6. Deploy to Heroku

```bash
git push heroku main
```

**If your branch is called master:**
```bash
git push heroku master
```

---

### 7. Run Migrations

```bash
heroku run python manage.py migrate
```

---

### 8. Create Superuser

```bash
heroku run python manage.py createsuperuser
```

Enter:
- **Username**: biasharaadmin
- **Email**: admin@biasharabridges.com
- **Password**: (create a secure password)

---

### 9. Collect Static Files

```bash
heroku run python manage.py collectstatic --noinput
```

---

### 10. Open Your App! 🎉

```bash
heroku open
```

Or visit: `https://biashara-bridges.herokuapp.com`

---

## 🔍 Useful Commands

### View Logs
```bash
heroku logs --tail
```

### Check App Status
```bash
heroku ps
```

### Restart App
```bash
heroku restart
```

### View Environment Variables
```bash
heroku config
```

### Access Django Shell
```bash
heroku run python manage.py shell
```

### View Database Info
```bash
heroku pg:info
```

---

## 🐛 Troubleshooting

### If deployment fails:
1. Check logs: `heroku logs --tail`
2. Verify all files committed: `git status`
3. Check requirements.txt has all dependencies
4. Verify Procfile exists and is correct

### If site shows error:
1. Check logs: `heroku logs --tail`
2. Verify migrations ran: `heroku run python manage.py showmigrations`
3. Check environment variables: `heroku config`

### If static files don't load:
1. Run: `heroku run python manage.py collectstatic --noinput`
2. Check `STATIC_ROOT` in settings.py
3. Verify WhiteNoise middleware is installed

---

## 📱 Test Your Deployed App

1. **Homepage**: `https://your-app.herokuapp.com/`
2. **Admin**: `https://your-app.herokuapp.com/admin/`
3. **Login**: Test user authentication
4. **Wallet**: Test wallet functionality

---

## 🔐 Security Checklist

- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY set
- [ ] ALLOWED_HOSTS configured
- [ ] Database backups enabled
- [ ] SSL enabled (automatic on Heroku)
- [ ] Environment variables for sensitive data

---

## 💰 Heroku Pricing

- **Free Tier**: App sleeps after 30 min inactivity
- **Hobby**: $7/month - Always on
- **PostgreSQL Essential**: $5/month
- **PostgreSQL Mini**: Free (limited)

---

## 🎯 Next Steps After Deployment

1. **Configure Payment Webhooks**:
   - Stripe: `https://your-app.herokuapp.com/webhooks/stripe/`
   - PayPal: `https://your-app.herokuapp.com/webhooks/paypal/`

2. **Test All Features**:
   - User registration/login
   - Wallet deposits
   - Payment processing
   - Admin panel

3. **Monitor Application**:
   - Use `heroku logs --tail`
   - Set up error tracking (Sentry, etc.)
   - Monitor performance

---

Good luck with your deployment! 🚀

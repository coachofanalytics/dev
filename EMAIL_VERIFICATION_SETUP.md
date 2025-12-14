# Email Verification Setup Guide

Complete guide for setting up and configuring email verification for user registration in Biashara Bridges.

## Table of Contents
1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Email Service Providers](#email-service-providers)
4. [Development Setup](#development-setup)
5. [Production Setup](#production-setup)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Customization](#customization)

---

## Overview

Biashara Bridges now requires email verification for all new user registrations. This ensures:
- Valid email addresses
- Reduced spam and fake accounts
- Secure account activation
- Better user engagement

### Key Features
- ✅ Mandatory email verification
- ✅ Beautiful HTML email templates
- ✅ 3-day verification link expiration
- ✅ Customizable email content
- ✅ Multiple SMTP provider support
- ✅ Console backend for development

---

## How It Works

### Registration Flow

1. **User Registers**
   - User fills out registration form
   - Provides email, username, password, and category

2. **Verification Email Sent**
   - System sends verification email to user's email address
   - User sees "Check Your Email" page
   - Verification link expires in 3 days

3. **User Clicks Verification Link**
   - User receives email
   - Clicks verification link
   - Redirected to confirmation page

4. **Email Confirmed**
   - User confirms email address
   - Account activated
   - Redirected to login page

5. **User Logs In**
   - User can now login with verified credentials
   - Full access to platform features

### Email Verification States

| State | Description | User Can Login? |
|-------|-------------|-----------------|
| **Unverified** | Just registered, email not verified | ❌ No |
| **Pending** | Verification email sent, waiting for confirmation | ❌ No |
| **Verified** | Email confirmed, account active | ✅ Yes |
| **Expired** | Verification link expired (>3 days) | ❌ No (must request new link) |

---

## Email Service Providers

### Option 1: Console Backend (Development Only)

**Best for:** Local development and testing

**Configuration:**
```bash
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**Behavior:**
- Emails printed to console/terminal
- No actual emails sent
- Perfect for testing without SMTP setup

---

### Option 2: Gmail SMTP (Recommended for Small Projects)

**Best for:** Small projects, personal use, testing production emails

**Requirements:**
- Gmail account
- 2-Step Verification enabled
- App Password generated

**Setup Steps:**

1. **Enable 2-Step Verification:**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable 2-Step Verification

2. **Generate App Password:**
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and "Other (Custom name)"
   - Name it "Biashara Bridges"
   - Copy the 16-character password

3. **Update .env:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_16_char_app_password
DEFAULT_FROM_EMAIL=Biashara Bridges <your_email@gmail.com>
```

**Limitations:**
- Gmail sending limit: 500 emails/day
- May be flagged as spam if sending too many
- Not recommended for high-volume production

---

### Option 3: SendGrid (Recommended for Production)

**Best for:** Production environments, high volume

**Features:**
- Free tier: 100 emails/day
- Paid plans for higher volume
- Better deliverability
- Analytics and tracking

**Setup Steps:**

1. **Create SendGrid Account:**
   - Sign up at [SendGrid](https://signup.sendgrid.com/)
   - Verify your email
   - Complete sender verification

2. **Create API Key:**
   - Go to Settings > API Keys
   - Click "Create API Key"
   - Name it "Biashara Bridges"
   - Select "Full Access"
   - Copy the API key

3. **Update .env:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_api_key_here
DEFAULT_FROM_EMAIL=Biashara Bridges <noreply@yourdomain.com>
```

---

### Option 4: Mailgun (Alternative Production Option)

**Best for:** Production, developers who prefer Mailgun

**Features:**
- Free tier: 5,000 emails/month
- Good deliverability
- Easy DNS setup

**Setup Steps:**

1. **Create Mailgun Account:**
   - Sign up at [Mailgun](https://signup.mailgun.com/)
   - Add and verify your domain

2. **Get SMTP Credentials:**
   - Go to Sending > Domain Settings
   - Find SMTP credentials
   - Copy username and password

3. **Update .env:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=postmaster@your-domain.mailgun.org
EMAIL_HOST_PASSWORD=your_mailgun_password
DEFAULT_FROM_EMAIL=Biashara Bridges <noreply@yourdomain.com>
```

---

### Option 5: Amazon SES (Enterprise Option)

**Best for:** Large-scale production, AWS users

**Features:**
- Pay-as-you-go pricing
- Extremely scalable
- Requires AWS account

**Setup Steps:**

1. **Setup AWS SES:**
   - Create AWS account
   - Go to Amazon SES
   - Verify email address or domain
   - Request production access (important!)

2. **Create SMTP Credentials:**
   - Go to SMTP Settings
   - Create SMTP credentials
   - Copy username and password

3. **Update .env:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your_ses_smtp_username
EMAIL_HOST_PASSWORD=your_ses_smtp_password
DEFAULT_FROM_EMAIL=Biashara Bridges <noreply@yourdomain.com>
```

---

## Development Setup

### Quick Start (Console Backend)

1. **Ensure .env is configured:**
```bash
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run migrations:**
```bash
python manage.py migrate
```

4. **Start development server:**
```bash
python manage.py runserver
```

5. **Register a new user:**
   - Go to http://localhost:8000/register/
   - Fill out the form
   - Click "Create Account"

6. **Check console for email:**
   - Look at your terminal/console
   - You'll see the email content printed
   - Copy the verification link

7. **Verify email:**
   - Paste the link in your browser
   - Click "Confirm Email Address"
   - Login!

---

## Production Setup

### Step 1: Choose Email Provider

Select one of the production SMTP providers (SendGrid, Mailgun, Gmail, AWS SES).

### Step 2: Configure Environment Variables

Update your production `.env` file:

```bash
# Change backend to SMTP
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Add your SMTP credentials
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_username
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=Biashara Bridges <noreply@yourdomain.com>
```

### Step 3: Verify Domain (Recommended)

For better deliverability:

1. **Add SPF Record:**
```
v=spf1 include:sendgrid.net ~all
```

2. **Add DKIM Record:**
   - Provided by your email service
   - Add to DNS

3. **Add DMARC Record:**
```
v=DMARC1; p=none; rua=mailto:postmaster@yourdomain.com
```

### Step 4: Test Email Sending

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test email from Biashara Bridges.',
    'noreply@yourdomain.com',
    ['your-email@example.com'],
    fail_silently=False,
)
```

### Step 5: Monitor Email Delivery

- Check your SMTP provider's dashboard
- Monitor bounce rates
- Watch for spam complaints
- Review delivery statistics

---

## Testing

### Test Registration Flow

1. **Register New User:**
```bash
# Navigate to registration page
http://localhost:8000/register/

# Fill form with:
- Username: testuser
- Email: test@example.com
- Password: SecurePass123!
- Category: Individual
```

2. **Verify Email Sent:**
   - Check console (development)
   - Check email inbox (production)
   - Verify email content

3. **Click Verification Link:**
   - Should redirect to confirmation page
   - Click "Confirm Email Address"

4. **Verify Confirmation:**
   - Should see success message
   - Should redirect to login

5. **Test Login:**
   - Login with username/email and password
   - Should successfully authenticate

### Test Edge Cases

**Expired Link:**
```bash
# Create user
# Wait 4 days (or manually expire in database)
# Try clicking verification link
# Should show expired message
```

**Duplicate Email:**
```bash
# Register user A with email@example.com
# Try registering user B with same email
# Should show error
```

**Invalid Link:**
```bash
# Modify verification link URL
# Try accessing
# Should show invalid link message
```

---

## Troubleshooting

### Issue: Emails Not Sending

**Symptoms:**
- No email in inbox
- No email in console

**Solutions:**
1. Check EMAIL_BACKEND setting
2. Verify SMTP credentials
3. Check spam/junk folder
4. Review server logs:
```bash
python manage.py runserver --verbosity 2
```

---

### Issue: "SMTPAuthenticationError"

**Symptoms:**
- Error when sending email
- Authentication failed

**Solutions:**
1. **Gmail:**
   - Use App Password, not regular password
   - Enable 2-Step Verification
   - Check "Less secure app access" (legacy)

2. **SendGrid/Mailgun:**
   - Verify API key is correct
   - Check account is active
   - Ensure API key has permissions

---

### Issue: Emails Go to Spam

**Symptoms:**
- Emails delivered but in spam folder

**Solutions:**
1. Add SPF, DKIM, DMARC records
2. Use verified domain
3. Avoid spam trigger words
4. Use professional email content
5. Warm up new domain/IP slowly

---

### Issue: Verification Link Doesn't Work

**Symptoms:**
- Click link, nothing happens
- 404 error

**Solutions:**
1. Check SITE_ID in settings.py
2. Verify Site domain in admin:
```bash
python manage.py shell
```
```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
print(site.domain)  # Should match your domain
# Update if needed:
site.domain = 'yourdomain.com'
site.name = 'Biashara Bridges'
site.save()
```

---

### Issue: "Site matching query does not exist"

**Solution:**
```bash
python manage.py migrate sites
python manage.py shell
```
```python
from django.contrib.sites.models import Site
Site.objects.create(id=1, domain='localhost:8000', name='Biashara Bridges')
```

---

## Customization

### Customize Email Templates

Email templates are located in:
```
templates/account/email/
├── email_confirmation_subject.txt
├── email_confirmation_message.txt
└── email_confirmation_message.html
```

**Edit Subject:**
```
templates/account/email/email_confirmation_subject.txt
```

**Edit Text Version:**
```
templates/account/email/email_confirmation_message.txt
```

**Edit HTML Version:**
```
templates/account/email/email_confirmation_message.html
```

### Change Verification Link Expiration

In `config/settings.py`:
```python
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3  # Change to desired days
```

### Customize Redirect URLs

In `config/settings.py`:
```python
# After email confirmation
LOGIN_URL = 'login'

# After successful login
LOGIN_REDIRECT_URL = 'home'
```

### Disable Email Verification (Not Recommended)

In `config/settings.py`:
```python
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # or 'none'
```

---

## Email Template Variables

Available variables in email templates:

| Variable | Description |
|----------|-------------|
| `{{ user }}` | User object |
| `{{ user.username }}` | Username |
| `{{ user.email }}` | Email address |
| `{{ user.get_full_name }}` | Full name (first + last) |
| `{{ activate_url }}` | Verification link URL |
| `{{ current_site }}` | Site object |
| `{{ current_site.domain }}` | Domain name |
| `{{ current_site.name }}` | Site name |
| `{{ key }}` | Verification key |

---

## Security Best Practices

1. **Use HTTPS in Production:**
   - Set `ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'`

2. **Secure SMTP Credentials:**
   - Never commit credentials to Git
   - Use environment variables
   - Rotate credentials regularly

3. **Rate Limiting:**
   - Limit verification email requests
   - Prevent email flooding

4. **Monitor Suspicious Activity:**
   - Track failed verification attempts
   - Alert on unusual patterns

5. **Email Content Security:**
   - Don't include sensitive data in emails
   - Use secure links (HTTPS)
   - Warn users about phishing

---

## Support

For issues or questions:
1. Check this documentation
2. Review Django-allauth documentation
3. Check server logs
4. Test with console backend first

---

## Quick Reference

### Development (Console)
```bash
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Production (Gmail)
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

### Production (SendGrid)
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_api_key
```

---

**Last Updated:** December 2024
**Version:** 1.0

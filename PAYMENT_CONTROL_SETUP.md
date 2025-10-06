# Payment Control System Setup for Heroku

This guide explains how to set up payment control for client sites hosted on Heroku, allowing you to suspend access when payments are not made.

## Overview

The payment control system uses Django middleware to check environment variables on Heroku. When `PAYMENT_MADE=false`, the site becomes inaccessible to regular users (admin/staff can still access).

## Quick Setup Commands

### 1. Enable Payment Control (Block Access)
```bash
# Set payment status to false (blocks access)
heroku config:set PAYMENT_MADE=false --app your-client-app-name

# Set client name for personalized messages
heroku config:set CLIENT_NAME="Acme Corporation" --app your-client-app-name

# Set payment due date (optional)
heroku config:set PAYMENT_DUE_DATE="December 15, 2024" --app your-client-app-name

# Set grace period in days (optional)
heroku config:set PAYMENT_GRACE_DAYS=7 --app your-client-app-name
```

### 2. Restore Access (Allow Access)
```bash
# Set payment status to true (allows access)
heroku config:set PAYMENT_MADE=true --app your-client-app-name
```

### 3. Check Current Payment Status
```bash
# View all payment-related config vars
heroku config --app your-client-app-name | grep -E "(PAYMENT|CLIENT)"

# Check payment status via API endpoint
curl https://your-client-app-name.herokuapp.com/payment-status/
```

## Environment Variables Reference

| Variable | Purpose | Example Values | Required |
|----------|---------|----------------|----------|
| `PAYMENT_MADE` | Primary payment control | `true`, `false`, `1`, `0`, `yes`, `no` | Yes |
| `PAYMENT_STATUS` | Alternative payment status | `active`, `suspended`, `paid`, `overdue` | No |
| `CLIENT_NAME` | Client name for messages | `"Acme Corporation"` | No |
| `PAYMENT_DUE_DATE` | Payment due date | `"December 15, 2024"` | No |
| `PAYMENT_GRACE_DAYS` | Grace period in days | `7` | No |

## Deployment Steps

### 1. Deploy the Payment Control Code
```bash
# Commit your changes
git add -A
git commit -m "Add payment control middleware for client access management"

# Deploy to Heroku
git push heroku main
```

### 2. Test the System
```bash
# Test with payment enabled (should work normally)
heroku config:set PAYMENT_MADE=true --app your-client-app-name
curl https://your-client-app-name.herokuapp.com/

# Test with payment disabled (should show payment required page)
heroku config:set PAYMENT_MADE=false --app your-client-app-name
curl https://your-client-app-name.herokuapp.com/
```

## Usage Scenarios

### Scenario 1: Client Payment Overdue
```bash
# Block access immediately
heroku config:set PAYMENT_MADE=false --app client-site
heroku config:set CLIENT_NAME="ABC Company" --app client-site
heroku config:set PAYMENT_DUE_DATE="November 30, 2024" --app client-site

# Send email to client about payment
# Client contacts you for payment
# After payment received, restore access
heroku config:set PAYMENT_MADE=true --app client-site
```

### Scenario 2: Grace Period
```bash
# Set grace period for client
heroku config:set PAYMENT_MADE=false --app client-site
heroku config:set PAYMENT_GRACE_DAYS=5 --app client-site
heroku config:set PAYMENT_DUE_DATE="December 1, 2024" --app client-site

# Client has 5 days to make payment before complete suspension
```

### Scenario 3: Maintenance Mode
```bash
# Temporarily suspend for maintenance
heroku config:set PAYMENT_MADE=false --app client-site
heroku config:set CLIENT_NAME="Maintenance Mode" --app client-site

# After maintenance, restore
heroku config:set PAYMENT_MADE=true --app client-site
```

## Admin Access

**Important**: Admin and staff users can always access the site, even when `PAYMENT_MADE=false`. This allows you to:
- Access the admin panel
- Make necessary updates
- Monitor the site status
- Restore access after payment

## Monitoring and Alerts

### Check Payment Status via API
```bash
# Get JSON response with payment status
curl https://your-client-app-name.herokuapp.com/payment-status/

# Example response:
{
  "payment_made": false,
  "client_name": "ABC Company",
  "payment_due": "November 30, 2024",
  "status": "suspended",
  "timestamp": "2024-11-15T10:30:00"
}
```

### Log Monitoring
```bash
# Monitor Heroku logs for payment control events
heroku logs --tail --app your-client-app-name | grep -i payment

# Look for these log entries:
# "Payment not made - blocking access to /"
# "Admin user accessing system despite payment status"
```

## Troubleshooting

### Site Still Accessible After Setting PAYMENT_MADE=false
1. Check if you're logged in as admin/staff
2. Verify the environment variable is set:
   ```bash
   heroku config:get PAYMENT_MADE --app your-client-app-name
   ```
3. Check if middleware is properly loaded in settings
4. Restart the Heroku dyno:
   ```bash
   heroku restart --app your-client-app-name
   ```

### Payment Required Page Not Showing
1. Check if the template exists: `/templates/payment_required.html`
2. Verify middleware is in MIDDLEWARE list in settings.py
3. Check Heroku logs for errors:
   ```bash
   heroku logs --tail --app your-client-app-name
   ```

### Admin Can't Access Site
1. Ensure you're logged in as staff or superuser
2. Check user permissions in Django admin
3. Try accessing `/admin/` directly

## Security Considerations

1. **Environment Variables**: Payment status is stored in Heroku config vars (secure)
2. **Admin Access**: Only authenticated admin/staff users can bypass payment checks
3. **Logging**: All payment control actions are logged for audit trail
4. **Graceful Degradation**: System defaults to allowing access if there are errors

## Integration with Billing Systems

You can integrate this with external billing systems:

```bash
# Example: Integration with Stripe webhook
# When payment fails, set PAYMENT_MADE=false
# When payment succeeds, set PAYMENT_MADE=true

# Webhook script example:
if payment_failed:
    subprocess.run(['heroku', 'config:set', 'PAYMENT_MADE=false', '--app', app_name])
elif payment_succeeded:
    subprocess.run(['heroku', 'config:set', 'PAYMENT_MADE=true', '--app', app_name])
```

## Best Practices

1. **Always test** payment control in staging before production
2. **Set client names** for personalized error messages
3. **Use grace periods** for better client relationships
4. **Monitor logs** regularly for payment control events
5. **Have backup access** (admin accounts) in case of issues
6. **Document client agreements** about payment suspension policies

## Support

For issues with the payment control system:
1. Check Heroku logs first
2. Verify environment variables are set correctly
3. Test in staging environment
4. Contact CODA support team

---

**Note**: This system gives you complete control over client site access. Use responsibly and in accordance with your service agreements.



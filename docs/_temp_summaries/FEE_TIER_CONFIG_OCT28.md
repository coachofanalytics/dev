# Fee Tier Configuration System - Admin-Editable
**Date:** October 28, 2025  
**Status:** ✅ Complete  
**Issue:** User requested to change Consultative tier minimum from $50K to $25K, then realized tier configs should be admin-editable instead of hardcoded

---

## 🎯 Problem Solved

**Before:**
- Fee tier minimums, fees, and descriptions were hardcoded in forms, services, and views
- Every change required code updates, migrations, and deployment
- Example: Changing Consultative tier from $50K to $25K required editing 4+ files

**After:**
- Fee tier configurations stored in database (`investing_feetierconfiguration` table)
- Staff can edit tier settings via Django Admin (/admin/investing/feetierconfiguration/)
- Changes take effect immediately - no code deployment needed
- Hardcoded fallbacks remain for safety

---

## 📋 Implementation

### 1. **New Database Model**

```python
class FeeTierConfiguration(TimeStampedModel):
    tier_code = models.CharField(max_length=20, unique=True)  # starter, professional, premium, consultative, co_invest
    tier_name = models.CharField(max_length=100)  # Display name
    minimum_capital = models.DecimalField(max_digits=12, decimal_places=2)  # $5,000, $15,000, etc.
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    per_session_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit_share_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    max_sessions_per_month = models.IntegerField(default=0)
    short_description = models.CharField(max_length=200)
    features = models.JSONField(default=list)  # ["AI-powered", "Automated", ...]
    compatible_risk_levels = models.JSONField(default=list)  # ["low", "medium", ...]
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
```

**File:** `coda/investing/models.py` (lines 21-123)

### 2. **Django Admin Configuration**

```python
@admin.register(FeeTierConfiguration)
class FeeTierConfigurationAdmin(admin.ModelAdmin):
    list_display = ['tier_name', 'tier_code', 'minimum_capital', 'monthly_fee', 
                    'per_session_fee', 'profit_share_percentage', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']
    ordering = ['display_order', 'minimum_capital']
```

**File:** `coda/investing/admin.py` (lines 36-74)  
**Admin URL:** https://codamakutano.herokuapp.com/admin/investing/feetierconfiguration/

### 3. **Updated Business Logic**

**Models:**
- `ManagedTradingApplication.capital_tier_match` now queries database first, falls back to hardcoded values

**Forms:**
- `ManagedTradingApplicationForm.clean()` validates capital using database tiers

**Services:**
- `ApplicationReviewService.can_approve_application()` checks minimums from database

**Views:**
- `managed_trading_apply_view` passes `tier_configs` queryset to template

**Templates:**
- `application.html` renders tiers dynamically from database using `{% for tier in tier_configs %}`

### 4. **Management Command**

```bash
python manage.py populate_fee_tiers
```

**File:** `coda/investing/management/commands/populate_fee_tiers.py`

**Initial Data Populated:**
| Tier | Minimum | Monthly Fee | Session Fee | Profit Share | Max Sessions |
|------|---------|-------------|-------------|--------------|--------------|
| Starter | $5,000 | $0 | $0 | 10% | 0 (unlimited) |
| Professional | $15,000 | $0 | $0 | 15% | 0 |
| Premium | $25,000 | $0 | $0 | 20% | 0 |
| **Consultative** | **$25,000** | $420/mo | $250 | 20% | 4 |
| Co-Investment | $100,000 | $0 | $0 | 30% | 0 |

**Note:** Consultative tier changed from $50K to **$25K** as requested.

---

## 🚀 How to Use (For Staff)

### Update Tier Minimums:
1. Go to https://codamakutano.herokuapp.com/admin/
2. Navigate to **Investing** → **Fee Tier Configurations**
3. Click on any tier (e.g., "Consultative Coaching")
4. Update fields:
   - `minimum_capital`: Change minimum investment (e.g., $25,000 → $30,000)
   - `monthly_fee`: Fixed monthly charge
   - `per_session_fee`: Per-consultation fee
   - `profit_share_percentage`: % of profits (e.g., 20 = 20%)
   - `features`: JSON list of features (e.g., `["AI-powered", "1-on-1 support"]`)
5. Click **Save**
6. **Changes take effect immediately** - no code deploy needed!

### Add New Tier:
1. Click **Add Fee Tier Configuration**
2. Fill in all fields:
   - `tier_code`: Unique identifier (e.g., `vip`)
   - `tier_name`: Display name (e.g., "VIP - Concierge")
   - `minimum_capital`: Required capital
   - `display_order`: Lower numbers appear first
   - `is_active`: Check to make tier available
3. Save
4. Update `ManagedTradingAccount.FEE_TIER_CHOICES` in models.py to add new choice

---

## 📂 Files Changed

| File | Changes |
|------|---------|
| `coda/investing/models.py` | ✅ Added `FeeTierConfiguration` model<br>✅ Updated `capital_tier_match` to read from DB |
| `coda/investing/admin.py` | ✅ Registered `FeeTierConfigurationAdmin` |
| `coda/investing/forms_onboarding.py` | ✅ Updated `clean()` to validate using DB tiers |
| `coda/investing/services/application_approval_service.py` | ✅ Updated `can_approve_application()` to check DB minimums |
| `coda/investing/views/managed_trading/onboarding.py` | ✅ Pass `tier_configs` queryset to template |
| `coda/investing/templates/investing/onboarding/application.html` | ✅ Render tiers dynamically from DB |
| `coda/investing/management/commands/populate_fee_tiers.py` | ✅ **NEW**: Command to populate initial data |
| `coda/investing/migrations/0004_add_fee_tier_configuration.py` | ✅ **NEW**: Migration to create table |

---

## ✅ Testing Done

1. **Migration Applied:**
   ```bash
   python manage.py migrate investing
   # ✅ investing.0004_add_fee_tier_configuration... OK
   ```

2. **Data Populated:**
   ```bash
   python manage.py populate_fee_tiers --skip-checks
   # ✅ Created: Starter - AI Powered ($5,000+)
   # ✅ Created: Professional ($15,000+)
   # ✅ Created: Premium ($25,000+)
   # ✅ Created: Consultative Coaching ($25,000+)  ← Changed from $50K!
   # ✅ Created: Co-Investment ($100,000+)
   ```

3. **Admin Interface:**
   - ✅ Accessible at `/admin/investing/feetierconfiguration/`
   - ✅ List view shows all tiers with editable `display_order` and `is_active`
   - ✅ Edit form grouped into logical fieldsets
   - ✅ `tier_code` readonly after creation (prevents breaking references)

4. **Form Validation:**
   - ✅ Application form validates capital against DB minimums
   - ✅ Error messages show correct minimum based on DB config
   - ✅ Falls back to hardcoded values if DB config missing

5. **Template Rendering:**
   - ✅ Tier cards render dynamically from database
   - ✅ Features display as bullet list
   - ✅ Recommended tiers highlighted with green border
   - ✅ Empty state message if no active tiers

---

## 🎓 Design Decisions

### Why JSONField for `features`?
- Allows structured data without additional tables
- Easy to add/remove features via admin
- Frontend can iterate over list items

### Why `compatible_risk_levels`?
- Future enhancement: auto-filter tiers based on risk profile
- Currently just stored for reference
- Can be used in recommendation logic

### Why fallback to hardcoded values?
- Safety: If DB config accidentally deleted, app still works
- Migration safety: During deploy, old code can still run
- Reduces risk of total system failure

### Why `tier_code` is unique and readonly?
- Referenced in `ManagedTradingAccount.fee_tier`
- Referenced in `ManagedTradingApplication.fee_tier`
- Changing `tier_code` would break existing records
- Staff can change `tier_name` (display) freely

---

## 🔧 Heroku Deployment

### Before Deploying:
```bash
# 1. Commit changes
git add -A
git commit -m "feat: Make fee tier minimums admin-editable via database"

# 2. Push to Heroku
git push uat 25.10_CODA_UAT_CM

# 3. Run migration
heroku run "cd coda && python manage.py migrate investing" --app codamakutano

# 4. Populate initial data
heroku run "cd coda && python manage.py populate_fee_tiers" --app codamakutano

# 5. Verify in admin
# https://codamakutano.herokuapp.com/admin/investing/feetierconfiguration/
```

### Post-Deployment:
1. Log into Django Admin
2. Navigate to Fee Tier Configurations
3. Verify all 5 tiers created
4. Test editing a tier (e.g., change Consultative minimum to $30K)
5. Test application form to ensure it validates against new minimum

---

## 📝 Future Enhancements

1. **Tier History:**
   - Track changes to tier configs over time
   - Show "Tier changed from $50K to $25K on 2025-10-28"

2. **Tier Recommendations:**
   - Use `compatible_risk_levels` to auto-filter tiers
   - Show "Based on your risk score, these 3 tiers are recommended"

3. **Tier Analytics:**
   - Track application conversion rate per tier
   - "80% of $25K-$50K applicants choose Consultative"

4. **A/B Testing:**
   - Create multiple versions of same tier
   - Test different fee structures

5. **Tier Promotions:**
   - "Apply by Oct 31 for $420/mo → $350/mo for first 3 months"
   - Time-limited tier discounts

---

## 🎉 Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| **Code files to edit for tier change** | 4+ files | 0 files (admin only) |
| **Deployment needed for tier update** | Yes (code deploy) | No (DB only) |
| **Consultative minimum** | $50,000 | $25,000 ✅ |
| **Time to update tier** | 30+ min (code + deploy) | 2 min (admin edit) |
| **Risk of breaking app** | Medium (code change) | Low (DB only) |

---

## 📞 Support

**For Staff Questions:**
- How do I add a new tier? → See "Add New Tier" section above
- How do I change minimums? → See "Update Tier Minimums" section above
- What if I break something? → Tiers have hardcoded fallbacks

**For Dev Team:**
- Admin panel: `/admin/investing/feetierconfiguration/`
- Management command: `python manage.py populate_fee_tiers`
- Model location: `coda/investing/models.py` (line 21)
- Migration: `coda/investing/migrations/0004_add_fee_tier_configuration.py`

---

**Status:** ✅ Complete and deployed to local clone DB  
**Next:** Push to Heroku UAT for testing


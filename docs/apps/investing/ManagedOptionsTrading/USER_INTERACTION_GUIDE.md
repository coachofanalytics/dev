# Managed Options Trading - User Interaction Guide

## **System Overview: Two Distinct User Types**

### **CLIENT (aamiruk in your screenshot)**
- **Role:** Individual investor who gives money to CODA to manage
- **Access:** Client portal - can only VIEW their accounts and positions
- **Cannot:** Create positions, modify trades, or access other clients' data

### **STAFF/MANAGER (CODA employees)**
- **Role:** Account managers who execute trades on behalf of clients
- **Access:** Admin interface - can CREATE, MODIFY, and MANAGE all accounts
- **Can:** Create positions, close trades, manage client accounts, view all data

---

## **Complete User Journey Maps**

### **🎯 CLIENT JOURNEY (What aamiruk sees)**

#### **Step 1: Login & Dashboard**
```
URL: /accounts/login/
User: aamiruk (password: MANAGER2030)
↓
URL: /investing/dashboard/
Shows: BOTH investment systems
```

**What Client Sees:**
- **System 1:** Their equity investments in CODA (if any)
- **System 2:** Their managed trading accounts (NEW!)
  - Account count, total balance, total P&L
  - Cards for each managed account
  - "View All Managed Accounts" button

#### **Step 2: View All Managed Accounts**
```
Click: "View All Managed Accounts"
URL: /investing/managed/portal/
Shows: List of all client's managed accounts
```

**What Client Sees:**
- Table of all their managed accounts
- Account numbers, balances, P&L, open positions
- "View Details" button for each account

#### **Step 3: View Specific Account Details** ⭐ **(Your Screenshot)**
```
Click: "View Details" on CODA-OPT-002
URL: /investing/managed/portal/accounts/2/
Shows: Detailed account view
```

**What Client Sees (Your Screenshot):**
- **Account Summary:** Balance ($50,000), P&L ($0), Open Positions (3)
- **Open Positions Table:**
  - MSFT Cash-Secured Short Put (P&L: $0)
  - TSLA Cash-Secured Short Put (P&L: -$90)
  - AAPL Cash-Secured Short Put (P&L: $120)
- **Actions:** "Back to Portal" button

#### **Step 4: Client Actions Available**
- ✅ **VIEW** account details
- ✅ **VIEW** position details
- ✅ **VIEW** trading history
- ✅ **VIEW** session history (if consultative tier)
- ❌ **CANNOT** create positions
- ❌ **CANNOT** modify trades
- ❌ **CANNOT** access other clients' data

---

### **👨‍💼 STAFF/MANAGER JOURNEY**

#### **Step 1: Admin Login**
```
URL: /admin/
User: Staff account with investing permissions
Shows: Django admin interface
```

#### **Step 2: Manage Trading Accounts**
```
Navigate: Investing → Managed Trading Accounts
Shows: List of ALL client accounts
```

**What Staff Sees:**
- All managed accounts across all clients
- Account details, status, performance
- "Add" button to create new accounts
- "Change" button to modify accounts

#### **Step 3: Create New Account**
```
Click: "Add Managed Trading Account"
Form: Account creation form
```

**Staff Can Set:**
- Client selection
- Account name and number
- Initial capital ($5,000 minimum)
- Fee tier (consultative, professional, starter, premium, co-invest)
- Risk parameters
- Account manager assignment

#### **Step 4: Manage Positions**
```
Navigate: Investing → Options Positions
Shows: All positions across all accounts
```

**Staff Can:**
- ✅ **CREATE** new positions
- ✅ **CLOSE** existing positions
- ✅ **MODIFY** position details
- ✅ **VIEW** all client positions
- ✅ **MONITOR** risk alerts

#### **Step 5: Create New Position**
```
Click: "Add Options Position"
Form: Position creation form
```

**Staff Can Set:**
- Account selection (which client)
- Symbol (AAPL, TSLA, MSFT, etc.)
- Strategy (Cash-Secured Short Put, Covered Call, etc.)
- Strike price, premium, expiration
- Capital required
- Greeks (Delta, Theta, etc.)

#### **Step 6: Monitor & Alerts**
```
Navigate: Investing → Trading Activities
Shows: All trading activities and alerts
```

**Staff Can See:**
- Position alerts (profit targets, expiration warnings)
- Risk alerts (exposure limits, loss limits)
- Account alerts (low balance, high risk)
- Trading activities (opens, closes, modifications)

---

## **Position Entry Process (How Positions Get Created)**

### **Current Test Data (What You're Seeing)**
The 3 positions in your screenshot were created by our test command:
```python
# This created the test data you see
python manage.py comprehensive_managed_trading_test
```

### **Real-World Position Entry**

#### **Method 1: Staff Admin Interface**
1. Staff logs into `/admin/`
2. Goes to "Options Positions"
3. Clicks "Add Options Position"
4. Fills out form:
   - Account: CODA-OPT-002 (aamiruk's account)
   - Symbol: MSFT
   - Strategy: Cash-Secured Short Put
   - Strike: $400
   - Premium: $2.50
   - Expiration: Oct 25, 2025
5. Saves position
6. Position appears in client's account

#### **Method 2: API Integration (Future)**
- OptionPlay API integration
- Automated position creation based on AI analysis
- Webhook triggers for position updates

#### **Method 3: Bulk Import (Future)**
- CSV upload for multiple positions
- Excel import for account managers
- API integration with trading platforms

---

## **User Permission Matrix**

| Action | Client (aamiruk) | Staff/Manager | Admin |
|--------|------------------|---------------|-------|
| View own accounts | ✅ | ✅ | ✅ |
| View all accounts | ❌ | ✅ | ✅ |
| Create accounts | ❌ | ✅ | ✅ |
| Create positions | ❌ | ✅ | ✅ |
| Close positions | ❌ | ✅ | ✅ |
| View alerts | ✅ (own only) | ✅ (all) | ✅ (all) |
| Modify account settings | ❌ | ✅ | ✅ |
| View trading history | ✅ (own only) | ✅ (all) | ✅ (all) |

---

## **Next Steps for Testing**

### **Test Client Experience (aamiruk)**
1. ✅ Login as aamiruk - DONE
2. ✅ View dashboard with both systems - DONE  
3. ✅ View managed accounts list - DONE
4. ✅ View account details (your screenshot) - DONE
5. 🔄 Test position details view
6. 🔄 Test session history (if consultative tier)

### **Test Staff Experience**
1. 🔄 Login as staff user
2. 🔄 Access admin interface
3. 🔄 Create new managed account
4. 🔄 Create new position for aamiruk
5. 🔄 Verify position appears in client view
6. 🔄 Test position closing
7. 🔄 Test monitoring and alerts

### **Test Integration Points**
1. 🔄 Verify dashboard shows both systems
2. 🔄 Test navigation between systems
3. 🔄 Test data consistency across views
4. 🔄 Test responsive design on mobile

---

## **Current System Status**

✅ **Working:**
- Client portal (what you're seeing)
- Account details view
- Position display
- Dashboard integration
- Database structure
- Test data

🔄 **Ready for Testing:**
- Staff admin interface
- Position creation
- Position closing
- Alert system
- Session management

🚀 **Future Enhancements:**
- API integrations
- Automated trading
- Advanced analytics
- Mobile app
- Real-time updates

---

**Your screenshot shows the system working perfectly! aamiruk is a client viewing their managed trading account details, and the positions were created by our test data. The system is ready for both client and staff testing.**

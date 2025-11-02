# Budget System User Guide - Step by Step

**Last Updated:** October 28, 2025  
**Purpose:** Walkthrough for new users on how to create, edit, and submit budgets for approval in the CODA Budget System

---

## 🎯 Overview: What is the Budget System?

The CODA Budget System helps you plan and track spending across your organization. You can:
- Create budgets for **weekly**, **monthly**, or **yearly** periods
- Enter amounts in **Kenyan Shillings (KSH)** - it automatically shows USD equivalent
- Get budget items **approved** before spending
- Track actual vs estimated spending
- Edit and **reassign items to subcategories** if miscategorized

---

## 📝 Core Concept: Bottom-Up Budgeting

**The budget flows from specific items → subcategories → categories:**

```
ITEM LEVEL (What you buy)
  ↓
SUBCATEGORY LEVEL (Groups of items)
  ↓
CATEGORY LEVEL (Summary)
  ↓
APPROVAL (Management review)
```

**Example:**
- **Item:** "Office WiFi Router"
- **Subcategory:** "IT Infrastructure"
- **Category:** "Operations"
- **Amount:** KES 15,000 (≈ $117 USD)

---

## 🚀 Complete Workflow: Creating and Getting a Budget Approved

### **Scenario:** You need a budget for monthly internet expenses

---

### **STEP 1: Navigate to Budget Dashboard**

1. Log into the CODA system
2. Go to **Finance** → **Budget Dashboard**
3. You'll see tabs: Overview, Approvals, Requests, Projections, Analytics, Estimation, Planning, Editing

---

### **STEP 2: Find or Create Your Budget Category**

**Option A: Budget Already Exists (Quick Edit)**

1. Click the **"Overview"** tab
2. Find your category in the "Budget by Category" table (e.g., "Utilities")
3. Click **"View"** to see details
4. You'll see:
   - **Category totals** (KES and USD)
   - **Subcategories** with budget items
   - **Uncategorized items** (shown in yellow warning box)

5. **To categorize an uncategorized item:**
   - Click **"Edit"** button on the item row
   - Select the correct **Subcategory** from dropdown
   - Fill in **Unit Price** (KES), **Quantity**, and **Cases**
   - Click **"Save"**

**Option B: No Budget Yet (Create New)**

1. Click **"New Budget Request"** button
2. Fill in the budget request form (see Step 3)

---

### **STEP 3: Create a Budget Request**

1. Click **"New Budget Request"** button (top right)
2. Fill in the form:
   
   **Basic Information:**
   - **Category:** Select from dropdown (e.g., "Utilities")
   - **Subcategory:** Select from dropdown (e.g., "Internet & Airtime")
   - **Item Name:** Type description (e.g., "Safaricom Home Fiber Internet")
   - **Description:** Optional details
   
   **Amount Information:**
   - **Unit Price (KES):** Enter amount (e.g., 5000)
   - **Currency:** Defaults to KSH (can change to USD, EUR, GBP)
   - **Quantity:** Enter quantity (e.g., 1)
   - **Cases:** Enter number of cases/periods (e.g., 12 for yearly)
   - **USD Equivalent:** Automatically calculated (e.g., $39)
   
   **Timeframe:**
   - **Timeframe:** Select **Weekly**, **Monthly**, **Quarterly**, or **Yearly**
   - For monthly internet: Select **"Monthly"**
   
   **Additional Fields:**
   - **Budget Type:** General Budget, Website Development, etc.
   - **Project Name:** Optional
   - **Priority:** Low, Medium, High, Urgent

3. Click **"Submit Budget Request"**

---

### **STEP 4: Understanding the Estimated Amount**

The system automatically calculates:
```
Estimated Amount = Unit Price × Quantity × Cases
```

**Examples:**

| Item | Unit Price | Quantity | Cases | Total KSH | Total USD |
|------|------------|----------|-------|-----------|-----------|
| Monthly Internet | 5,000 | 1 | 1 | 5,000 | $39 |
| **Yearly Internet** | 5,000 | 1 | **12** | **60,000** | **$468** |
| Office Supplies (yearly) | 10,000 | 1 | 12 | 120,000 | $937 |

---

### **STEP 5: Submit for Approval**

After creating your budget request, it needs approval before you can spend.

**Submit Individual Item:**
1. Go to the item edit page
2. Click **"Submit Budget Request"**

**Submit Entire Category:**
1. Go to category detail page
2. Click **"Submit for Approval"** button (blue button at top)
3. Confirm in popup
4. System creates a budget request for the entire category

---

### **STEP 6: Approval Process**

Your budget request goes through an approval workflow:

1. **Status:** Pending → Under Review → Approved/Rejected
2. **Who approves:** Based on category tier
   - **Tier A:** Auto-approved (recurring expenses)
   - **Tier B:** Department Manager or Finance Manager
   - **Tier C:** Senior Manager or Executive
3. **Notification:** You'll receive updates on the status

**Check Status:**
1. Go to **"Requests"** tab in Budget Dashboard
2. View all your submitted requests
3. See status, amount, and approver comments

---

### **STEP 7: Tracking Actual vs Estimated**

Once approved and you start spending:

1. Go to **"Overview"** tab
2. Click **"View"** on your category
3. You'll see:
   - **Estimated Amount:** What you planned
   - **Actual Spent:** What you actually spent
   - **Variance:** Difference (positive = overspent, negative = under budget)

---

## 🔧 Editing and Categorizing Budgets

### **Problem:** Budget item is in wrong subcategory

**Solution:** Reassign it!

1. Go to category detail page
2. Find the item (check "Uncategorized" section if needed)
3. Click **"Edit"** on the item
4. **Change Subcategory:** Select the correct subcategory from dropdown
5. Click **"Save"**
6. Item is now properly categorized!

---

### **Problem:** Need to change timeframe (weekly → monthly)

1. Click **"Edit"** on the budget item
2. Change **"Timeframe"** dropdown (Weekly, Monthly, Quarterly, Yearly)
3. Click **"Save"**

---

## 📊 Multi-Currency Support

### **Entering Amounts:**

- **Default:** Kenyan Shillings (KSH)
- **Options:** USD, EUR, GBP
- **Converter:** Automatic, uses current exchange rates

### **Display:**

All amounts show:
- **Primary:** KSH (what you enter)
- **Secondary:** USD (for reporting)

Example:
```
KES 60,000.00
≈ $ 468.00 USD
```

---

## 🎯 Common Use Cases

### **Use Case 1: Monthly Recurring Expense (Internet)**

1. Category: "Utilities"
2. Subcategory: "Internet & Airtime"
3. Item: "Safaricom Fiber - Monthly"
4. Amount: KES 5,000
5. Timeframe: **Monthly**
6. Cases: 1

### **Use Case 2: Yearly Project Budget (Website Development)**

1. Category: "Marketing"
2. Subcategory: "Website Development"
3. Item: "New Company Website"
4. Amount: KES 500,000
5. Timeframe: **Yearly**
6. Cases: 1 (one-time project)

### **Use Case 3: Weekly Operations (Transport)**

1. Category: "Transport"
2. Subcategory: "Fuel"
3. Item: "Vehicle Fuel - Weekly"
4. Amount: KES 3,000
5. Timeframe: **Weekly**
6. Cases: 1 (every week)

---

## 🚨 Troubleshooting

### **Issue:** "Subcategory cannot be edited"

**Fixed!** ✅ Subcategories are now editable. Click "Edit" on any budget item to change subcategory.

### **Issue:** Category shows "$0.00" amounts

**Solution:** 
1. Click "Edit" on budget items
2. Ensure Unit Price, Quantity, and Cases are filled
3. Estimated amount will auto-calculate

### **Issue:** Want to edit a category amount

**Solution:**
1. Go to category detail → Click "Edit Category Budget"
2. Change amounts for individual items
3. Totals auto-calculate
4. Click "Submit Budget Request" to request approval

### **Issue:** Transaction/Projection errors in dashboard

**Fixed!** ✅ Database queries now use correct relationships (`budget__company`, `department__company`).

---

## 📌 Summary Checklist

**To create a budget:**
- [ ] Navigate to Budget Dashboard
- [ ] Click "New Budget Request"
- [ ] Fill in Category, Subcategory, Item Name
- [ ] Enter amounts (Unit Price, Quantity, Cases)
- [ ] Select timeframe (Weekly/Monthly/Yearly)
- [ ] Click "Submit"
- [ ] Wait for approval

**To edit/categorize:**
- [ ] Find item in category detail
- [ ] Click "Edit"
- [ ] Change subcategory if needed
- [ ] Update amounts
- [ ] Click "Save"

**To track spending:**
- [ ] Go to Overview tab
- [ ] Click "View" on category
- [ ] Compare Estimated vs Actual
- [ ] Check variance percentage

---

## 🎓 Key Takeaways

1. **Budgets are item-level:** Enter specific items, subcategories and categories auto-calculate
2. **Multi-currency:** Enter in KSH, USD always shown for reference
3. **Timeframes:** Weekly, Monthly, Quarterly, Yearly - pick what makes sense
4. **Approval required:** Submit budgets for approval before spending
5. **Editable:** You can always reassign items to correct subcategories
6. **Real-time tracking:** Compare estimated vs actual spending anytime

---

**Questions?** Check the Budget Dashboard help text or contact your Finance Manager.

**Happy Budgeting!** 💰📊




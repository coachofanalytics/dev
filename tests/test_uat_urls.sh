#!/bin/bash
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        TESTING UAT ENDPOINTS (v834)                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

BASE_URL="https://codamakutano.herokuapp.com"

# Function to test URL
test_url() {
    local url=$1
    local name=$2
    printf "Testing: %-50s " "$name"
    status=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$url" 2>/dev/null || echo "TIMEOUT")
    if [ "$status" = "200" ]; then
        echo "✅ $status"
    elif [ "$status" = "302" ] || [ "$status" = "301" ]; then
        echo "↪️  $status (redirect)"
    elif [ "$status" = "TIMEOUT" ]; then
        echo "⏱️  TIMEOUT"
    else
        echo "❌ $status"
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "NEW FEATURES (v834 - Just Deployed)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_url "$BASE_URL/admin/finance/budgetestimateprojection/" "Admin: Budget Projections"
test_url "$BASE_URL/admin/finance/transaction/" "Admin: Transactions"
test_url "$BASE_URL/admin/finance/budgetcategory/" "Admin: Budget Categories"
test_url "$BASE_URL/admin/finance/budgetsubcategory/" "Admin: Budget Subcategories"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SMART FORM & APIs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_url "$BASE_URL/finance/transaction/smart-entry/" "Smart Transaction Form"
test_url "$BASE_URL/finance/api/predict-all/?receiver=KPLC" "API: Predict All Fields"
test_url "$BASE_URL/finance/api/subcategories/?category_id=1" "API: Subcategories"
test_url "$BASE_URL/finance/api/items/?subcategory_id=1" "API: Items"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "BUDGET DASHBOARD"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_url "$BASE_URL/finance/budget-dashboard/coda/" "Main Budget Dashboard"
test_url "$BASE_URL/finance/budget-dashboard/coda/?tab=overview" "Dashboard: Overview Tab"
test_url "$BASE_URL/finance/budget-dashboard/coda/?tab=estimation" "Dashboard: Estimation Tab"
test_url "$BASE_URL/finance/budget-dashboard/coda/?tab=planning" "Dashboard: Planning Tab"
test_url "$BASE_URL/finance/budget-dashboard/coda/?tab=analytics" "Dashboard: Analytics Tab"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Done! Check for any ❌ errors above."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

#!/bin/bash
# Deployment script for loan product type fixes
# Deploys to: PROD (code only), UAT (code only), DEV (code + docs + script)

set -e  # Exit on error

BRANCH_PROD="25.12_CODA_PROD_CM"
BRANCH_UAT="25.12_CODA_UAT_CM"
BRANCH_DEV="25.12_CODA_DEV_CM"

CODE_FILE="coda/finance/views.py"
DOC_FILE="DEPLOYMENT_SUMMARY_LOAN_PRODUCTS.md"
SCRIPT_FILE="update_prod_loan_products.py"

COMMIT_MSG="Fix loan product type filters - remove invalid 'external' type, fix kcc/staff type references"

echo "=========================================="
echo "Deploying Loan Product Type Fixes"
echo "=========================================="
echo ""

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"
echo ""

# Check if code file has changes
if ! git diff --quiet $CODE_FILE; then
    echo "✓ Code file has changes: $CODE_FILE"
else
    echo "✗ No changes in $CODE_FILE"
    exit 1
fi

# 1. Deploy to PROD (code only)
echo "----------------------------------------"
echo "1. Deploying to PROD: $BRANCH_PROD"
echo "----------------------------------------"
git checkout $BRANCH_PROD
git add $CODE_FILE
git commit -m "$COMMIT_MSG" || echo "No new changes to commit (may already be committed)"
echo "✓ PROD branch updated"
echo ""

# 2. Deploy to UAT (code only)
echo "----------------------------------------"
echo "2. Deploying to UAT: $BRANCH_UAT"
echo "----------------------------------------"
git checkout $BRANCH_UAT
git add $CODE_FILE
git commit -m "$COMMIT_MSG" || echo "No new changes to commit (may already be committed)"
echo "✓ UAT branch updated"
echo ""

# 3. Deploy to DEV (code + docs + script)
echo "----------------------------------------"
echo "3. Deploying to DEV: $BRANCH_DEV"
echo "----------------------------------------"
git checkout $BRANCH_DEV
git add $CODE_FILE
if [ -f "$DOC_FILE" ]; then
    git add $DOC_FILE
    echo "✓ Added documentation: $DOC_FILE"
fi
if [ -f "$SCRIPT_FILE" ]; then
    git add $SCRIPT_FILE
    echo "✓ Added script: $SCRIPT_FILE"
fi
git commit -m "$COMMIT_MSG" || echo "No new changes to commit (may already be committed)"
echo "✓ DEV branch updated (code + docs + script)"
echo ""

# Return to original branch
echo "----------------------------------------"
echo "Returning to original branch: $CURRENT_BRANCH"
echo "----------------------------------------"
git checkout $CURRENT_BRANCH

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review changes: git log --oneline -1 on each branch"
echo "2. Push branches:"
echo "   - git push origin $BRANCH_PROD"
echo "   - git push origin $BRANCH_UAT"
echo "   - git push origin $BRANCH_DEV"
echo "3. Deploy to UAT environment"
echo "4. Test on UAT"
echo "5. Deploy to Production environment"
echo "6. Run database update script on UAT and PROD"
echo ""















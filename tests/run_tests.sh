#!/bin/bash
# CODA Test Runner Script
# Purpose: Run comprehensive tests before deployment
# Usage: ./run_tests.sh [options]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 CODA Comprehensive Test Suite"
echo "=================================="
echo ""

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Change to coda directory for Django tests
cd "$PROJECT_ROOT/coda"

# Parse arguments
RUN_ALL=true
RUN_REGRESSION=false
RUN_UNIT=false
RUN_INTEGRATION=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --regression)
            RUN_REGRESSION=true
            RUN_ALL=false
            shift
            ;;
        --unit)
            RUN_UNIT=true
            RUN_ALL=false
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            RUN_ALL=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./run_tests.sh [--regression|--unit|--integration] [--verbose]"
            exit 1
            ;;
    esac
done

# Function to run tests
run_test() {
    local test_name=$1
    local test_path=$2
    
    echo -e "${YELLOW}Running: ${test_name}${NC}"
    
    if [ "$VERBOSE" = true ]; then
        python manage.py test $test_path --verbosity=2
    else
        python manage.py test $test_path
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASS: ${test_name}${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL: ${test_name}${NC}"
        return 1
    fi
}

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Run regression tests (CRITICAL - always run before deployment)
if [ "$RUN_ALL" = true ] || [ "$RUN_REGRESSION" = true ]; then
    echo ""
    echo "🔴 REGRESSION TESTS (Critical - Known Bugs)"
    echo "-------------------------------------------"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if run_test "Budget Approval Fields" "finance.tests.test_regressions.RegressionTests.test_budget_request_has_approval_fields"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if run_test "Loan Product Schema" "finance.tests.test_regressions.RegressionTests.test_loan_product_has_term_months_field"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if run_test "Staff Approval Permission" "finance.tests.test_regressions.PermissionRegressionTests.test_staff_can_approve_budgets"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
fi

# Unit tests (if requested)
if [ "$RUN_ALL" = true ] || [ "$RUN_UNIT" = true ]; then
    echo ""
    echo "🔵 UNIT TESTS"
    echo "-------------"
    echo "TODO: Implement unit tests for models, services, utils"
fi

# Integration tests (if requested)
if [ "$RUN_ALL" = true ] || [ "$RUN_INTEGRATION" = true ]; then
    echo ""
    echo "🟢 INTEGRATION TESTS"
    echo "--------------------"
    echo "TODO: Implement integration tests for views, APIs"
fi

# Summary
echo ""
echo "=================================="
echo "📊 TEST SUMMARY"
echo "=================================="
echo -e "Total Tests: ${TOTAL_TESTS}"
echo -e "${GREEN}Passed: ${PASSED_TESTS}${NC}"
echo -e "${RED}Failed: ${FAILED_TESTS}${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo "✨ Safe to deploy!"
    exit 0
else
    echo -e "${RED}❌ TESTS FAILED!${NC}"
    echo "🚫 DO NOT DEPLOY until all tests pass!"
    exit 1
fi


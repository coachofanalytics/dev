#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cd playwright
echo "Running Playwright tests..."
npx playwright test --reporter=list

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cd playwright
echo "Installing Playwright dependencies..."
npm ci
echo "Installing Playwright browsers..."
npx playwright install --with-deps
echo "Playwright setup complete."

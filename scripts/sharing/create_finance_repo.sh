#!/bin/bash
# Script to extract finance app into its own repository

echo "Creating separate finance repository..."

# 1. Create a new branch with only finance app
git subtree split --prefix=coda/finance -b finance-only

# 2. Create new directory for finance repo
mkdir -p ../coda-finance-app
cd ../coda-finance-app

# 3. Initialize new repo
git init
git pull ../DEV finance-only

# 4. Add README and setup files
cat > README.md << 'READMEEOF'
# CODA Finance App

Django finance application extracted from CODA platform.

## Features
- Budget Management
- Transaction Tracking  
- Payment Processing
- Loan Management
- AI-Powered Predictions

## Installation

\`\`\`bash
pip install -r requirements.txt
\`\`\`

## Usage

Add to your Django project's INSTALLED_APPS:

\`\`\`python
INSTALLED_APPS = [
    ...
    'finance',
]
\`\`\`

## Documentation

See docs/ folder for detailed documentation.
READMEEOF

# 5. Create requirements for just finance
cat > requirements.txt << 'REQEOF'
Django>=3.2,<4.0
psycopg2>=2.9
django-crispy-forms>=1.12
python-dateutil>=2.8
REQEOF

git add .
git commit -m "Initial finance app extraction"

echo "Finance repository created at: $(pwd)"
echo "You can now push this to GitHub"

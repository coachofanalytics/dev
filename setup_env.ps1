# CODA Development Environment Setup
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CODA Development Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Choose your database configuration:" -ForegroundColor Yellow
Write-Host "1. SQLite (Local development)" -ForegroundColor Green
Write-Host "2. PostgreSQL UAT (Heroku UAT)" -ForegroundColor Blue
Write-Host "3. PostgreSQL Production (Heroku Prod)" -ForegroundColor Red
Write-Host "4. Local PostgreSQL" -ForegroundColor Magenta
Write-Host ""

$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host "Setting up SQLite configuration..." -ForegroundColor Green
        $env:DB_TYPE = "sqlite"
        $env:USE_POSTGRESQL = "False"
        Write-Host "✅ SQLite configuration set" -ForegroundColor Green
    }
    "2" {
        Write-Host "Setting up UAT PostgreSQL configuration..." -ForegroundColor Blue
        $env:DB_TYPE = "uat"
        $env:USE_POSTGRESQL = "False"
        Write-Host "Please set UAT_DATABASE_URL environment variable with your Heroku UAT database URL" -ForegroundColor Yellow
        Write-Host "Example: `$env:UAT_DATABASE_URL = 'postgres://user:pass@host:port/dbname'" -ForegroundColor Gray
        Write-Host "✅ UAT PostgreSQL configuration set" -ForegroundColor Blue
    }
    "3" {
        Write-Host "Setting up Production PostgreSQL configuration..." -ForegroundColor Red
        $env:DB_TYPE = "prod"
        $env:USE_POSTGRESQL = "False"
        Write-Host "Please set PROD_DATABASE_URL environment variable with your Heroku Production database URL" -ForegroundColor Yellow
        Write-Host "Example: `$env:PROD_DATABASE_URL = 'postgres://user:pass@host:port/dbname'" -ForegroundColor Gray
        Write-Host "✅ Production PostgreSQL configuration set" -ForegroundColor Red
    }
    "4" {
        Write-Host "Setting up Local PostgreSQL configuration..." -ForegroundColor Magenta
        $env:DB_TYPE = "postgres"
        $env:USE_POSTGRESQL = "False"
        Write-Host "Please set LOCAL_POSTGRES_URL environment variable with your local PostgreSQL URL" -ForegroundColor Yellow
        Write-Host "Example: `$env:LOCAL_POSTGRES_URL = 'postgres://user:pass@localhost:5432/coda_local'" -ForegroundColor Gray
        Write-Host "✅ Local PostgreSQL configuration set" -ForegroundColor Magenta
    }
    default {
        Write-Host "Invalid choice. Using default SQLite configuration." -ForegroundColor Yellow
        $env:DB_TYPE = "sqlite"
        $env:USE_POSTGRESQL = "False"
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Stripe Configuration (Optional)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$setup_stripe = Read-Host "Do you want to set up Stripe for testing? (y/n)"

if ($setup_stripe -eq "y" -or $setup_stripe -eq "Y") {
    Write-Host "Please set the following Stripe environment variables:" -ForegroundColor Yellow
    Write-Host "`$env:STRIPE_PUBLISHABLE_KEY = 'pk_test_...'" -ForegroundColor Gray
    Write-Host "`$env:STRIPE_SECRET_KEY = 'sk_test_...'" -ForegroundColor Gray
    Write-Host "`$env:STRIPE_WEBHOOK_SECRET = 'whsec_...'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "You can get these from: https://dashboard.stripe.com/test/apikeys" -ForegroundColor Cyan
    Write-Host "✅ Stripe configuration ready" -ForegroundColor Green
} else {
    Write-Host "Stripe will use payment details fallback" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Environment Setup Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Current configuration:" -ForegroundColor Yellow
Write-Host "DB_TYPE = $env:DB_TYPE" -ForegroundColor White
Write-Host "USE_POSTGRESQL = $env:USE_POSTGRESQL" -ForegroundColor White
Write-Host ""
Write-Host "To start the development server:" -ForegroundColor Green
Write-Host "cd coda" -ForegroundColor Gray
Write-Host "python manage.py runserver 8000" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to continue"

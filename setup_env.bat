@echo off
echo ========================================
echo CODA Development Environment Setup
echo ========================================
echo.

echo Choose your database configuration:
echo 1. SQLite (Local development) - Default
echo 2. PostgreSQL UAT (Heroku UAT)
echo 3. PostgreSQL Production (Heroku Prod)
echo 4. Local PostgreSQL
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo Setting up SQLite configuration...
    set DB_TYPE=sqlite
    set USE_POSTGRESQL=False
    echo ✅ SQLite configuration set
) else if "%choice%"=="2" (
    echo Setting up UAT PostgreSQL configuration...
    set DB_TYPE=uat
    set USE_POSTGRESQL=False
    echo Please set UAT_DATABASE_URL environment variable with your Heroku UAT database URL
    echo Example: set UAT_DATABASE_URL=postgres://user:pass@host:port/dbname
    echo ✅ UAT PostgreSQL configuration set
) else if "%choice%"=="3" (
    echo Setting up Production PostgreSQL configuration...
    set DB_TYPE=prod
    set USE_POSTGRESQL=False
    echo Please set PROD_DATABASE_URL environment variable with your Heroku Production database URL
    echo Example: set PROD_DATABASE_URL=postgres://user:pass@host:port/dbname
    echo ✅ Production PostgreSQL configuration set
) else if "%choice%"=="4" (
    echo Setting up Local PostgreSQL configuration...
    set DB_TYPE=postgres
    set USE_POSTGRESQL=False
    echo Please set LOCAL_POSTGRES_URL environment variable with your local PostgreSQL URL
    echo Example: set LOCAL_POSTGRES_URL=postgres://user:pass@localhost:5432/coda_local
    echo ✅ Local PostgreSQL configuration set
) else (
    echo Invalid choice. Using default SQLite configuration.
    set DB_TYPE=sqlite
    set USE_POSTGRESQL=False
)

echo.
echo ========================================
echo Stripe Configuration (Optional)
echo ========================================
echo.
set /p setup_stripe="Do you want to set up Stripe for testing? (y/n): "

if /i "%setup_stripe%"=="y" (
    echo Please set the following Stripe environment variables:
    echo set STRIPE_PUBLISHABLE_KEY=pk_test_...
    echo set STRIPE_SECRET_KEY=sk_test_...
    echo set STRIPE_WEBHOOK_SECRET=whsec_...
    echo.
    echo You can get these from: https://dashboard.stripe.com/test/apikeys
    echo ✅ Stripe configuration ready
) else (
    echo Stripe will use payment details fallback
)

echo.
echo ========================================
echo Environment Setup Complete
echo ========================================
echo.
echo Current configuration:
echo DB_TYPE=%DB_TYPE%
echo USE_POSTGRESQL=%USE_POSTGRESQL%
echo.
echo To start the development server:
echo cd coda
echo python manage.py runserver 8000
echo.
pause

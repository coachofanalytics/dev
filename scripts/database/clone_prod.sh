#!/bin/bash
# Clone Production Database to Local
# Creates an exact copy of production PostgreSQL database locally

set -e  # Exit on error

echo "🗄️  CODA Database Cloning Tool"
echo "================================"
echo ""
echo "This will create an EXACT copy of production database locally."
echo "You can then work with real production data safely."
echo ""

# Configuration
PROD_APP="codatrainingapp"
LOCAL_DB_NAME="coda_prod_clone"
LOCAL_DB_USER="${USER}"
BACKUP_FILE="/tmp/coda_prod_latest.dump"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📋 Options:${NC}"
echo "  1. Full PostgreSQL clone (recommended for development)"
echo "  2. SQLite conversion (good for quick examination)"
echo ""
read -p "Choose option (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo -e "${BLUE}Option 1: Full PostgreSQL Clone${NC}"
    echo "================================"
    
    # Check if PostgreSQL is installed
    if ! command -v psql &> /dev/null; then
        echo -e "${RED}❌ PostgreSQL not installed locally${NC}"
        echo ""
        echo "Install PostgreSQL:"
        echo "  macOS: brew install postgresql@14"
        echo "  Ubuntu: sudo apt-get install postgresql postgresql-contrib"
        echo ""
        exit 1
    fi
    
    # Check if PostgreSQL is running
    if ! pg_isready -q; then
        echo -e "${YELLOW}⚠️  PostgreSQL not running. Starting...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start postgresql@14
        else
            sudo service postgresql start
        fi
        sleep 2
    fi
    
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
    
    # Step 1: Create Heroku backup
    echo ""
    echo -e "${YELLOW}Step 1: Creating Heroku backup...${NC}"
    echo "This may take a few minutes for large databases..."
    
    heroku pg:backups:capture --app $PROD_APP
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to create backup${NC}"
        echo "Make sure you're logged in: heroku login"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Backup created${NC}"
    
    # Step 2: Download backup
    echo ""
    echo -e "${YELLOW}Step 2: Downloading backup...${NC}"
    
    heroku pg:backups:download --app $PROD_APP --output $BACKUP_FILE
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to download backup${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Downloaded to ${BACKUP_FILE}${NC}"
    
    # Step 3: Drop existing local database (if exists)
    echo ""
    echo -e "${YELLOW}Step 3: Preparing local database...${NC}"
    
    # Check if database exists
    if psql -lqt | cut -d \| -f 1 | grep -qw $LOCAL_DB_NAME; then
        read -p "Database '$LOCAL_DB_NAME' exists. Drop and recreate? (y/N): " drop_confirm
        if [ "$drop_confirm" = "y" ]; then
            dropdb $LOCAL_DB_NAME
            echo "   Dropped existing database"
        else
            echo "Aborted."
            exit 1
        fi
    fi
    
    # Create fresh database
    createdb $LOCAL_DB_NAME
    echo -e "${GREEN}✅ Created database: ${LOCAL_DB_NAME}${NC}"
    
    # Step 4: Restore backup
    echo ""
    echo -e "${YELLOW}Step 4: Restoring backup to local database...${NC}"
    echo "This may take a few minutes..."
    
    pg_restore --verbose --clean --no-acl --no-owner -h localhost -d $LOCAL_DB_NAME $BACKUP_FILE
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database restored successfully!${NC}"
    else
        echo -e "${YELLOW}⚠️  Some warnings occurred but database was restored${NC}"
        echo "   (This is normal for some permission-related warnings)"
    fi
    
    # Step 5: Update Django settings
    echo ""
    echo -e "${YELLOW}Step 5: Configuring Django...${NC}"
    
    # Create local settings with PostgreSQL
    cat > "coda/coda_project/coda_settings/local_prod_clone_settings.py" <<EOF
"""
Local Settings - Production Clone
Uses cloned production database for safe local testing
"""

from .base_settings import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Use cloned production database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '${LOCAL_DB_NAME}',
        'USER': '${LOCAL_DB_USER}',
        'PASSWORD': '',  # No password for local
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable HTTPS redirects
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Celery synchronous
CELERY_TASK_ALWAYS_EAGER = True

print("✅ Using production clone database: ${LOCAL_DB_NAME}")
EOF
    
    echo -e "${GREEN}✅ Created Django settings: local_prod_clone_settings.py${NC}"
    
    # Step 6: Show summary
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ SUCCESS! Production database cloned locally${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}📊 Database Info:${NC}"
    echo "   Database name: ${LOCAL_DB_NAME}"
    echo "   Location: localhost:5432"
    echo "   Django settings: local_prod_clone_settings.py"
    echo ""
    
    # Get database size
    DB_SIZE=$(psql -d $LOCAL_DB_NAME -t -c "SELECT pg_size_pretty(pg_database_size('${LOCAL_DB_NAME}'));")
    echo "   Size: ${DB_SIZE}"
    
    # Get table count
    TABLE_COUNT=$(psql -d $LOCAL_DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    echo "   Tables: ${TABLE_COUNT}"
    
    echo ""
    echo -e "${BLUE}🎯 Next Steps:${NC}"
    echo ""
    echo "1. Connect with Django shell:"
    echo "   ${GREEN}cd coda${NC}"
    echo "   ${GREEN}python manage.py shell --settings=coda_project.coda_settings.local_prod_clone_settings${NC}"
    echo ""
    echo "2. Run Django server with production data:"
    echo "   ${GREEN}python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings${NC}"
    echo ""
    echo "3. Examine data in psql:"
    echo "   ${GREEN}psql $LOCAL_DB_NAME${NC}"
    echo "   ${GREEN}  \\dt  ${NC}  # List all tables"
    echo "   ${GREEN}  \\d+ finance_budgetcategory  ${NC}  # Describe table"
    echo "   ${GREEN}  SELECT * FROM finance_budgetcategory WHERE approval_tier = 'A';${NC}"
    echo ""
    echo "4. Run tests against production data:"
    echo "   ${GREEN}python manage.py test --settings=coda_project.coda_settings.local_prod_clone_settings${NC}"
    echo ""
    echo "5. Test migrations safely:"
    echo "   ${GREEN}python manage.py migrate --settings=coda_project.coda_settings.local_prod_clone_settings${NC}"
    echo ""
    
    echo -e "${YELLOW}⚠️  Important Notes:${NC}"
    echo "   • This is a SNAPSHOT - changes won't affect production"
    echo "   • Re-run this script to refresh with latest prod data"
    echo "   • Production database: ~${DB_SIZE}"
    echo "   • Backup file: ${BACKUP_FILE}"
    echo ""
    
elif [ "$choice" = "2" ]; then
    echo ""
    echo -e "${BLUE}Option 2: SQLite Conversion${NC}"
    echo "==========================="
    echo ""
    echo -e "${YELLOW}This requires pgloader (PostgreSQL to SQLite converter)${NC}"
    echo ""
    echo "Install pgloader:"
    echo "  macOS: brew install pgloader"
    echo "  Ubuntu: sudo apt-get install pgloader"
    echo ""
    echo "Then run the conversion manually:"
    echo "  1. Get DATABASE_URL from Heroku"
    echo "  2. Run: pgloader <DATABASE_URL> sqlite://coda_prod.db"
    echo ""
    echo "Or use our Python script for partial sync:"
    echo "  python scripts/pull_prod_data_to_local.py --database-url '<URL>'"
    echo ""
    
else
    echo "Invalid choice. Exiting."
    exit 1
fi


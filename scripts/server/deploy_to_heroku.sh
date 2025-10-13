#!/bin/bash

# CODA Heroku UAT Deployment Script
# This script automates the deployment of CODA to Heroku UAT environment

set -e  # Exit on any error

echo "🚀 Starting CODA Heroku UAT Deployment..."
echo "=========================================="

# Configuration
APP_NAME="codamakutano"
BRANCH="optimization/phase7-management-utilities"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Heroku CLI is installed
check_heroku_cli() {
    print_status "Checking Heroku CLI installation..."
    if ! command -v heroku &> /dev/null; then
        print_error "Heroku CLI is not installed. Please install it first:"
        echo "https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    print_success "Heroku CLI is installed"
}

# Check if logged in to Heroku
check_heroku_auth() {
    print_status "Checking Heroku authentication..."
    if ! heroku auth:whoami &> /dev/null; then
        print_error "Not logged in to Heroku. Please run: heroku login"
        exit 1
    fi
    print_success "Authenticated with Heroku"
}

# Create Heroku app if it doesn't exist
create_heroku_app() {
    print_status "Checking if Heroku app exists..."
    if ! heroku apps:info --app $APP_NAME &> /dev/null; then
        print_status "Creating Heroku app: $APP_NAME"
        heroku create $APP_NAME --region us
        print_success "Heroku app created: $APP_NAME"
    else
        print_success "Heroku app already exists: $APP_NAME"
    fi
}

# Add required addons
add_heroku_addons() {
    print_status "Adding required Heroku addons..."
    
    # Add PostgreSQL
    if ! heroku addons:info heroku-postgresql --app $APP_NAME &> /dev/null; then
        print_status "Adding PostgreSQL addon..."
        heroku addons:create heroku-postgresql:mini --app $APP_NAME
        print_success "PostgreSQL addon added"
    else
        print_success "PostgreSQL addon already exists"
    fi
    
    # Add Redis
    if ! heroku addons:info heroku-redis --app $APP_NAME &> /dev/null; then
        print_status "Adding Redis addon..."
        heroku addons:create heroku-redis:mini --app $APP_NAME
        print_success "Redis addon added"
    else
        print_success "Redis addon already exists"
    fi
    
    # Add Mailgun (optional)
    if ! heroku addons:info mailgun --app $APP_NAME &> /dev/null; then
        print_status "Adding Mailgun addon..."
        heroku addons:create mailgun:starter --app $APP_NAME
        print_success "Mailgun addon added"
    else
        print_success "Mailgun addon already exists"
    fi
}

# Configure environment variables
configure_environment() {
    print_status "Configuring environment variables..."
    
    # Set Django settings
    heroku config:set DJANGO_SETTINGS_MODULE=coda_project.heroku_settings --app $APP_NAME
    
    # Set environment
    heroku config:set ENVIRONMENT=heroku --app $APP_NAME
    
    # Set debug mode
    heroku config:set DEBUG=False --app $APP_NAME
    
    # Generate and set secret key if not exists
    if ! heroku config:get SECRET_KEY --app $APP_NAME &> /dev/null; then
        SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
        heroku config:set SECRET_KEY="$SECRET_KEY" --app $APP_NAME
        print_success "Secret key generated and set"
    else
        print_success "Secret key already exists"
    fi
    
    # Set default from email
    heroku config:set DEFAULT_FROM_EMAIL="noreply@$APP_NAME.herokuapp.com" --app $APP_NAME
    
    print_success "Environment variables configured"
}

# Deploy application
deploy_application() {
    print_status "Deploying application to Heroku..."
    
    # Add Heroku remote if not exists
    if ! git remote | grep -q heroku; then
        heroku git:remote --app $APP_NAME
        print_success "Heroku remote added"
    fi
    
    # Deploy to Heroku
    print_status "Pushing code to Heroku..."
    git push heroku $BRANCH:main
    
    print_success "Application deployed to Heroku"
}

# Run post-deployment tasks
post_deployment_tasks() {
    print_status "Running post-deployment tasks..."
    
    # Run database migrations
    print_status "Running database migrations..."
    heroku run python manage.py migrate --app $APP_NAME
    
    # Collect static files
    print_status "Collecting static files..."
    heroku run python manage.py collectstatic --noinput --app $APP_NAME
    
    # Create superuser (optional)
    print_warning "Do you want to create a superuser? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        heroku run python manage.py createsuperuser --app $APP_NAME
    fi
    
    print_success "Post-deployment tasks completed"
}

# Verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Check app status
    print_status "Checking app status..."
    heroku ps --app $APP_NAME
    
    # Test database connection
    print_status "Testing database connection..."
    heroku run python manage.py check --database default --app $APP_NAME
    
    # Open app in browser
    print_status "Opening app in browser..."
    heroku open --app $APP_NAME
    
    print_success "Deployment verification completed"
}

# Show deployment information
show_deployment_info() {
    echo ""
    echo "🎉 DEPLOYMENT COMPLETE!"
    echo "======================="
    echo ""
    echo "Application URL: https://$APP_NAME.herokuapp.com"
    echo "Admin Panel: https://$APP_NAME.herokuapp.com/admin/"
    echo "API Documentation: https://$APP_NAME.herokuapp.com/api/v1/schema/swagger-ui/"
    echo "Heroku Dashboard: https://dashboard.heroku.com/apps/$APP_NAME"
    echo ""
    echo "Useful Commands:"
    echo "  View logs: heroku logs --tail --app $APP_NAME"
    echo "  Run shell: heroku run python manage.py shell --app $APP_NAME"
    echo "  Check config: heroku config --app $APP_NAME"
    echo "  Scale dynos: heroku ps:scale web=2 --app $APP_NAME"
    echo ""
}

# Main deployment function
main() {
    echo "Starting deployment process..."
    echo ""
    
    check_heroku_cli
    check_heroku_auth
    create_heroku_app
    add_heroku_addons
    configure_environment
    deploy_application
    post_deployment_tasks
    verify_deployment
    show_deployment_info
    
    print_success "CODA UAT deployment completed successfully! 🚀"
}

# Run main function
main "$@"



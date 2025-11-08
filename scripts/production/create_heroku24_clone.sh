#!/bin/bash

# Prepare Heroku-24 staging clone for Managed Options UAT
# This script provisions codamakutano-24, copies configuration, and runs smoke tests.

set -euo pipefail

APP_SOURCE="codamakutano"
APP_CLONE="codamakutano-24"
STACK_TARGET="heroku-24"
PIPELINE_NAME="coda-managed-options"
BRANCH_DEFAULT="25.11_CODA_UAT_CM"
PROJECT_ROOT="/Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV"

log_step() {
    echo ""
    echo "═══════════════════════════════════════════════════"
    echo " $1"
    echo "═══════════════════════════════════════════════════"
}

ensure_heroku_cli() {
    if ! command -v heroku >/dev/null 2>&1; then
        echo "❌ Heroku CLI not found. Install it from https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    if ! heroku auth:whoami >/dev/null 2>&1; then
        echo "❌ You are not logged into Heroku. Run 'heroku login' and retry."
        exit 1
    fi
}

create_clone_app() {
    if heroku apps:info --app "$APP_CLONE" >/dev/null 2>&1; then
        echo "✅ App $APP_CLONE already exists. Skipping creation."
        return
    fi
    log_step "Creating Heroku-24 clone app: $APP_CLONE"
    heroku apps:create "$APP_CLONE" --stack "$STACK_TARGET"
    heroku pipelines:add "$PIPELINE_NAME" --app "$APP_CLONE" --stage staging
}

copy_config() {
    log_step "Copying config vars, add-ons, and buildpacks from $APP_SOURCE"
    heroku addons --app "$APP_SOURCE" --json | jq -r '.[].name' | while read -r addon; do
        if ! heroku addons:attach "$addon" --app "$APP_CLONE" >/dev/null 2>&1; then
            echo "ℹ️  Add-on $addon could not be attached automatically. Please attach manually if required."
        fi
    done

    local config_json
    config_json=$(heroku config --app "$APP_SOURCE" --json)
    echo "$config_json" | jq -r 'to_entries[] | @base64' | while read -r entry; do
        local decoded key value
        decoded=$(echo "$entry" | base64 --decode)
        key=$(echo "$decoded" | jq -r '.key')
        value=$(echo "$decoded" | jq -r '.value')
        heroku config:set "$key=$value" --app "$APP_CLONE"
    done

    heroku buildpacks:clear --app "$APP_CLONE"
    heroku buildpacks --app "$APP_SOURCE" --json | jq -r '.[].url' | while read -r buildpack; do
        heroku buildpacks:add --app "$APP_CLONE" "$buildpack"
    done
}

push_code() {
    log_step "Pushing latest code to $APP_CLONE"
    cd "$PROJECT_ROOT"
    if ! git remote | grep -q "^$APP_CLONE$"; then
        heroku git:remote --app "$APP_CLONE" --remote "$APP_CLONE"
    fi
    git push "$APP_CLONE" "$BRANCH_DEFAULT":main --force
}

run_migrations() {
    log_step "Running migrations and collectstatic on $APP_CLONE"
    heroku run "cd coda && python manage.py migrate" --app "$APP_CLONE"
    heroku run "cd coda && python manage.py collectstatic --noinput" --app "$APP_CLONE"
}

run_smoke_tests() {
    log_step "Running smoke tests against $APP_CLONE"
    cd "$PROJECT_ROOT"
    BASE_URL="https://$APP_CLONE.herokuapp.com" ./tests/test_uat_urls.sh
}

post_checks() {
    log_step "Checking dyno status and recent logs"
    heroku ps --app "$APP_CLONE"
    heroku logs --tail --num 100 --app "$APP_CLONE"
}

main() {
    log_step "Validating prerequisites"
    ensure_heroku_cli
    command -v jq >/dev/null 2>&1 || { echo "❌ jq is required. Install it (brew install jq) and retry."; exit 1; }
    command -v base64 >/dev/null 2>&1 || { echo "❌ base64 utility is required. Install coreutils if missing."; exit 1; }

    create_clone_app
    copy_config
    push_code
    run_migrations
    run_smoke_tests
    post_checks

    log_step "Heroku-24 staging clone ready: https://$APP_CLONE.herokuapp.com"
    echo "Next steps:"
    echo "1. Perform manual UI sanity checks in browser."
    echo "2. Record results in docs/05_DEPLOYMENT/README.md checklist."
    echo "3. Schedule production stack swap once smoke tests pass."
}

main "$@"


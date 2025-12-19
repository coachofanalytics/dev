# Branch Management & Repository Linking Strategy

## Overview
This document outlines the strategy for managing multiple minimal branches and linking DEV and UAT repositories for seamless integration.

## Current Branch Structure

### Main Branches
- `25.12_CODA_DEV_CM` - Main development branch
- `25.12_CODA_UAT_CM` - UAT/staging branch
- `25.12_CODA_PROD_CM` - Production branch

### Minimal Branches (Need Updates)
- `25.12_AI_SERVICES_DEV_CM`
- `25.12_MANAGEMENT_DEV_CM`
- (Additional minimal branches as needed)

## Strategy 1: Shared Repository with Feature Branches (Recommended)

### Approach
Keep all branches in a single repository with clear naming conventions.

### Implementation Steps

#### 1. Update Minimal Branches to Match Main Branches

```bash
# For each minimal branch (AI_SERVICES, MANAGEMENT, etc.)
git checkout 25.12_AI_SERVICES_DEV_CM
git merge 25.12_CODA_DEV_CM --no-edit
# Resolve conflicts if any
git push origin 25.12_AI_SERVICES_DEV_CM
```

#### 2. Create Sync Script

Create `scripts/sync_branches.sh`:

```bash
#!/bin/bash
# Sync minimal branches with main DEV branch

MAIN_BRANCH="25.12_CODA_DEV_CM"
MINIMAL_BRANCHES=(
    "25.12_AI_SERVICES_DEV_CM"
    "25.12_MANAGEMENT_DEV_CM"
    # Add more as needed
)

for branch in "${MINIMAL_BRANCHES[@]}"; do
    echo "🔄 Syncing $branch with $MAIN_BRANCH..."
    git checkout $branch
    git merge $MAIN_BRANCH --no-edit
    if [ $? -eq 0 ]; then
        echo "✅ $branch synced successfully"
    else
        echo "❌ Conflicts in $branch - manual resolution needed"
    fi
done

git checkout $MAIN_BRANCH
echo "✅ Branch sync complete"
```

## Strategy 2: Separate Repository with CI/CD Integration

### Approach
Keep minimal branches in DEV repo, use GitHub Actions/webhooks to sync with UAT.

### Implementation

#### 1. GitHub Actions Workflow

Create `.github/workflows/sync-to-uat.yml`:

```yaml
name: Sync to UAT

on:
  push:
    branches:
      - 25.12_AI_SERVICES_DEV_CM
      - 25.12_MANAGEMENT_DEV_CM
      - 25.12_CODA_DEV_CM
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout DEV repo
        uses: actions/checkout@v3
        with:
          ref: ${{ github.ref }}
      
      - name: Checkout UAT repo
        uses: actions/checkout@v3
        with:
          repository: CODA-PROD/uat
          token: ${{ secrets.UAT_REPO_TOKEN }}
          path: uat-repo
      
      - name: Sync branches
        run: |
          cd uat-repo
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git fetch origin
          
          # Map DEV branch to UAT branch
          DEV_BRANCH=${{ github.ref_name }}
          UAT_BRANCH="${DEV_BRANCH/DEV_CM/UAT_CM}"
          
          git checkout $UAT_BRANCH || git checkout -b $UAT_BRANCH
          git merge origin/$DEV_BRANCH --no-edit
          git push origin $UAT_BRANCH
```

## Strategy 3: Git Subtree/Submodule Approach

### Approach
Keep minimal branches as subtrees in UAT repo, sync via subtree push/pull.

### Implementation

```bash
# Add DEV as remote in UAT repo
cd /path/to/uat/repo
git remote add dev-repo /path/to/dev/repo

# Create subtree
git subtree add --prefix=minimal-branches/$BRANCH_NAME dev-repo $BRANCH_NAME --squash

# Pull updates
git subtree pull --prefix=minimal-branches/$BRANCH_NAME dev-repo $BRANCH_NAME --squash
```

## Recommended Approach: Strategy 1 with Automated Scripts

### Benefits
- Single source of truth
- Easy to track changes
- Simple conflict resolution
- No complex CI/CD setup required

### Implementation Checklist

- [ ] Create `scripts/sync_branches.sh` script
- [ ] Update all minimal branches to match main DEV
- [ ] Document branch naming conventions
- [ ] Set up pre-merge hooks to ensure branches are in sync
- [ ] Create `scripts/check_branch_sync.sh` to verify branches are up-to-date

### Branch Naming Convention

```
{VERSION}_{APP/AREA}_{ENV}_CM

Examples:
- 25.12_CODA_DEV_CM
- 25.12_CODA_UAT_CM
- 25.12_AI_SERVICES_DEV_CM
- 25.12_MANAGEMENT_UAT_CM
```

### Automated Sync Workflow

```bash
# Weekly sync script
#!/bin/bash
# scripts/weekly_branch_sync.sh

MAIN_BRANCH="25.12_CODA_DEV_CM"
MINIMAL_BRANCHES=(
    "25.12_AI_SERVICES_DEV_CM"
    "25.12_MANAGEMENT_DEV_CM"
)

echo "🔄 Weekly branch sync starting..."
./scripts/sync_branches.sh

# Check for conflicts
for branch in "${MINIMAL_BRANCHES[@]}"; do
    if git log $branch..$MAIN_BRANCH --oneline | grep -q .; then
        echo "⚠️  $branch is behind $MAIN_BRANCH"
    fi
done

echo "✅ Sync complete"
```

## Linking DEV and UAT Repositories

### Option A: Single Repository (Recommended)
Keep everything in one repo, use branches for environments.

### Option B: Separate Repos with Sync Script
Use a script to sync selected branches from DEV to UAT.

### Option C: GitHub App/Webhook
Automatically create pull requests when minimal branches are updated.

## Lightweight Branches Strategy

### Overview
Lightweight branches are minimal branches that focus on a single app, removing non-relevant documentation while keeping all apps in INSTALLED_APPS for cross-app dependencies.

### Branch Configuration Strategy

Each lightweight branch will:
1. ✅ Start from synced Heroku UAT code (commit f23127ccd)
2. ✅ Keep ALL apps in INSTALLED_APPS (required for dependencies)
3. ✅ Remove only non-relevant app documentation
4. ✅ Add BRANCH_FOCUS.md to guide developers
5. ✅ Test that `runserver` works before proceeding

### Branch-Specific Configurations

#### INVESTING Branch (`25.11_INVESTING_DEV`)
- **Keep Apps:** All apps (main, accounts, application, unified_dashboard, investing, etc.)
- **Remove Docs:** finance, management, ai_services, portfolio app docs
- **Keep Docs:** investing app docs, core docs (01-07)
- **Focus:** `coda/investing/` app

#### FINANCE Branch (`25.11_FINANCE_DEV`)
- **Keep Apps:** All apps (required for cross-app dependencies)
- **Remove Docs:** investing, management, ai_services, portfolio app docs
- **Keep Docs:** finance app docs, core docs (01-07)

#### MANAGEMENT Branch (`25.11_MANAGEMENT_DEV`)
- **Keep Apps:** All apps (required for cross-app dependencies)
- **Remove Docs:** investing, finance, ai_services, portfolio app docs
- **Keep Docs:** management app docs, core docs (01-07)

#### AI_SERVICES Branch (`25.11_AI_SERVICES_DEV`)
- **Keep Apps:** All apps (required for cross-app dependencies)
- **Remove Docs:** investing, finance, management, portfolio app docs
- **Keep Docs:** ai_services app docs, core docs (01-07)

### Branch Focus Guide Template

Each lightweight branch should include a `BRANCH_FOCUS.md` file:

```markdown
# 🎯 [APP_NAME] Branch - Focus Guide

## This Branch: `[BRANCH_NAME]`

**FOCUS ON:** `coda/[app_name]/` app

## 📁 Work Here
- `coda/[app_name]/models.py` - [Description]
- `coda/[app_name]/views/` - [Description]
- `coda/[app_name]/services/` - [Description]
- `coda/[app_name]/templates/` - [Description]

## 📚 Documentation
- `docs/apps/[app_name]/` - [App]-specific documentation only
- `docs/01_GETTING_STARTED/` - Core setup guides
- `docs/02_ARCHITECTURE/` - System architecture
- `docs/03_IMPLEMENTATION/` - Project workflows
- `docs/04_TESTING/` - Testing strategies
- `docs/05_DEPLOYMENT/` - Deployment guides
- `docs/06_INTEGRATION/` - Integration patterns
- `docs/07_MAINTENANCE/` - Maintenance procedures

## ⚙️ INSTALLED_APPS
**All apps are installed** - required for cross-app dependencies:
- ✅ All apps present (main, accounts, [app_name], etc.)
- ✅ This ensures imports and dependencies work correctly
- ✅ Only documentation is removed for performance

## 🚫 Ignore These (Other Branches)
- `coda/[other_app]/` → Use `[other_branch]` for [other_app] work
```

### Git Worktrees Setup (Recommended)

**Problem:** When opening the same folder (DEV) in multiple Cursor windows, you see the welcome screen because Cursor prevents opening the same folder twice.

**Solution:** Git worktrees allow you to have **multiple working directories** for the same repository, each checked out to a different branch.

#### Benefits:
- ✅ Each branch has its own folder (can open in separate Cursor windows)
- ✅ Same git repository (no duplication)
- ✅ No conflicts (each folder is on a different branch)
- ✅ Lightweight (shared git objects, minimal disk space)

#### Setup Steps:

```bash
# Step 1: Navigate to Parent Directory
cd ~/PROJECTS/CODA/DEVELOPMENT

# Step 2: Create Worktrees for Each Branch
git worktree add ../DEV_INVESTING 25.11_INVESTING_DEV
git worktree add ../DEV_FINANCE 25.11_FINANCE_DEV
git worktree add ../DEV_MANAGEMENT 25.11_MANAGEMENT_DEV
git worktree add ../DEV_AI_SERVICES 25.11_AI_SERVICES_DEV
```

#### Folder Structure After Setup:
```
~/PROJECTS/CODA/DEVELOPMENT/
├── DEV/                    # Main dev branch (25.11_CODA_DEV_CM)
├── DEV_INVESTING/         # Investing branch (25.11_INVESTING_DEV)
├── DEV_FINANCE/           # Finance branch (25.11_FINANCE_DEV)
├── DEV_MANAGEMENT/        # Management branch (25.11_MANAGEMENT_DEV)
├── DEV_AI_SERVICES/       # AI Services branch (25.11_AI_SERVICES_DEV)
└── STG/                   # Your existing staging folder
```

#### Common Worktree Commands:

```bash
# List all worktrees
cd ~/PROJECTS/CODA/DEVELOPMENT/DEV
git worktree list

# Remove a worktree (when done)
git worktree remove ../DEV_INVESTING
# Or if folder is locked:
git worktree remove --force ../DEV_INVESTING

# Update all worktrees (pull latest changes)
cd ~/PROJECTS/CODA/DEVELOPMENT/DEV
git fetch uat --all

# Then in each worktree folder
cd ~/PROJECTS/CODA/DEVELOPMENT/DEV_INVESTING
git pull uat 25.11_INVESTING_DEV
```

### Required Fixes for Lightweight Branches

#### Issue 1: Missing "My Account Services" Section ✅ FIXED
**Problem:** UAT has "My Account Services" section with buttons like "Edit Profile", "My DAF", etc., but PROD only shows "Available Dashboards".

**Solution:** Added "My Account Services" section to `coda/unified_dashboard/templates/unified_dashboard/dashboard.html` that renders `role_based_links` context variable.

**Status:** ✅ Fixed in UAT branch, needs to be merged to PROD.

#### Issue 2: Template Tag Error ⚠️ RESOLVED
**Error:**
```
InvalidTemplateLibrary: Invalid template library specified. 
ImportError raised when trying to load 'application.templatetags.customfilters': 
No module named 'application'
```

**Problem:** INVESTING branch has minimal INSTALLED_APPS but templates reference `application.templatetags.customfilters`.

**Solution Applied:**
1. ✅ Added `application.apps.ApplicationConfig` to INSTALLED_APPS
2. ✅ Added `unified_dashboard.apps.UnifiedDashboardConfig` to INSTALLED_APPS
3. ✅ Commented out context processors for removed apps (management, professional_services)

**Status:** ✅ Resolved - All required apps are now included.

### Required Apps for Lightweight Branches

Each lightweight branch needs these **core apps** even if it's focused on one app:

#### Minimum Required Apps:
1. `main.apps.MainConfig` - Core functionality
2. `accounts.apps.AccountsConfig` - User management
3. `application.apps.ApplicationConfig` - Template tags (customfilters)
4. `unified_dashboard.apps.UnifiedDashboardConfig` - Dashboard views
5. Your focused app (e.g., `investing.apps.InvestingConfig`)

#### Apps That Can Be Removed:
- `finance.apps.FinanceConfig` (unless working on finance)
- `management.apps.ManagementConfig` (unless working on management)
- `ai_services.apps.AiServicesConfig` (unless working on AI services)
- `portfolio.apps.PortfolioConfig` (unless working on portfolio)
- `professional_services.apps.ProfessionalServicesConfig` (unless working on it)

### Testing Checklist

For each lightweight branch:
- [ ] `python manage.py check` - No errors
- [ ] `python manage.py runserver` - Starts successfully
- [ ] No missing module errors
- [ ] No template tag errors
- [ ] Focus app works correctly
- [ ] Dashboard views work (if used)

## Next Steps

1. **Immediate**: Update minimal branches to match main DEV branch
2. **Short-term**: Create sync scripts and documentation
3. **Long-term**: Implement automated CI/CD for branch syncing
4. **Ongoing**: Maintain lightweight branch configurations and fix issues as they arise


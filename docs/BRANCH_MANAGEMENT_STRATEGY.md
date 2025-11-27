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

## Next Steps

1. **Immediate**: Update minimal branches to match main DEV branch
2. **Short-term**: Create sync scripts and documentation
3. **Long-term**: Implement automated CI/CD for branch syncing


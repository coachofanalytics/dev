#!/bin/bash
# Sync minimal branches with main DEV branch

set -e  # Exit on error

MAIN_BRANCH="25.12_CODA_DEV_CM"
MINIMAL_BRANCHES=(
    "25.12_AI_SERVICES_DEV_CM"
    "25.12_MANAGEMENT_DEV_CM"
    # Add more minimal branches as needed
)

echo "🔄 Branch Sync Script"
echo "===================="
echo ""
echo "Main branch: $MAIN_BRANCH"
echo "Minimal branches to sync:"
for branch in "${MINIMAL_BRANCHES[@]}"; do
    echo "  - $branch"
done
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if main branch exists
if ! git show-ref --verify --quiet refs/heads/$MAIN_BRANCH; then
    echo "❌ Error: Main branch $MAIN_BRANCH does not exist"
    exit 1
fi

# Ensure we're on a clean working tree
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: Working tree has uncommitted changes"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Store current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"
echo ""

# Fetch latest changes
echo "📥 Fetching latest changes..."
git fetch origin

# Sync each minimal branch
for branch in "${MINIMAL_BRANCHES[@]}"; do
    echo ""
    echo "🔄 Processing $branch..."
    
    # Check if branch exists locally
    if git show-ref --verify --quiet refs/heads/$branch; then
        echo "   ✓ Branch exists locally"
    else
        echo "   ⚠️  Branch doesn't exist locally, creating from origin..."
        if git show-ref --verify --quiet refs/remotes/origin/$branch; then
            git checkout -b $branch origin/$branch
        else
            echo "   ❌ Branch doesn't exist on origin either, skipping..."
            continue
        fi
    fi
    
    # Switch to branch
    git checkout $branch
    
    # Check if branch is behind main
    BEHIND=$(git rev-list --count $MAIN_BRANCH..$branch 2>/dev/null || echo "0")
    AHEAD=$(git rev-list --count $branch..$MAIN_BRANCH 2>/dev/null || echo "0")
    
    if [ "$AHEAD" -gt 0 ]; then
        echo "   ⚠️  Branch is $AHEAD commits behind $MAIN_BRANCH"
        echo "   🔄 Merging $MAIN_BRANCH into $branch..."
        
        # Try to merge
        if git merge $MAIN_BRANCH --no-edit --no-ff; then
            echo "   ✅ Merged successfully"
            echo "   💾 Pushing to origin..."
            git push origin $branch
        else
            echo "   ❌ Merge conflicts detected!"
            echo "   🔧 Please resolve conflicts manually:"
            echo "      1. Fix conflicts in the files"
            echo "      2. git add <resolved-files>"
            echo "      3. git commit"
            echo "      4. git push origin $branch"
            read -p "   Press Enter after resolving conflicts to continue..."
        fi
    else
        echo "   ✅ Branch is up to date with $MAIN_BRANCH"
    fi
done

# Return to original branch
echo ""
echo "📍 Returning to original branch: $CURRENT_BRANCH"
git checkout $CURRENT_BRANCH

echo ""
echo "✅ Branch sync complete!"
echo ""
echo "📋 Summary:"
for branch in "${MINIMAL_BRANCHES[@]}"; do
    if git show-ref --verify --quiet refs/heads/$branch; then
        BEHIND=$(git rev-list --count $MAIN_BRANCH..$branch 2>/dev/null || echo "0")
        AHEAD=$(git rev-list --count $branch..$MAIN_BRANCH 2>/dev/null || echo "0")
        if [ "$AHEAD" -eq 0 ] && [ "$BEHIND" -eq 0 ]; then
            echo "   ✅ $branch: In sync"
        elif [ "$AHEAD" -gt 0 ]; then
            echo "   ⚠️  $branch: $AHEAD commits behind"
        else
            echo "   ℹ️  $branch: $BEHIND commits ahead"
        fi
    fi
done


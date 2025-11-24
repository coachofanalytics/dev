# 🪶 Lightweight Branches - Setup Guide

## Problem
When opening the same folder (DEV) in multiple Cursor windows, you see the welcome screen because Cursor prevents opening the same folder twice.

## Solution: Git Worktrees ⭐ RECOMMENDED

Git worktrees allow you to have **multiple working directories** for the same repository, each checked out to a different branch. This is perfect for lightweight branches!

### Benefits:
- ✅ Each branch has its own folder (can open in separate Cursor windows)
- ✅ Same git repository (no duplication)
- ✅ No conflicts (each folder is on a different branch)
- ✅ Lightweight (shared git objects, minimal disk space)

---

## 🚀 Setup Worktrees for Lightweight Branches

### Step 1: Navigate to Parent Directory
```bash
cd ~/PROJECTS/CODA/DEVELOPMENT
```

### Step 2: Create Worktrees for Each Branch

```bash
# INVESTING branch worktree
git worktree add ../DEV_INVESTING 25.11_INVESTING_DEV

# FINANCE branch worktree
git worktree add ../DEV_FINANCE 25.11_FINANCE_DEV

# MANAGEMENT branch worktree
git worktree add ../DEV_MANAGEMENT 25.11_MANAGEMENT_DEV

# AI_SERVICES branch worktree
git worktree add ../DEV_AI_SERVICES 25.11_AI_SERVICES_DEV
```

### Step 3: Open in Cursor
Now you can open each folder separately:
- Open `DEV` → Main dev branch (`25.11_CODA_DEV_CM`)
- Open `DEV_INVESTING` → Investing branch (`25.11_INVESTING_DEV`)
- Open `DEV_FINANCE` → Finance branch (`25.11_FINANCE_DEV`)
- Open `DEV_MANAGEMENT` → Management branch (`25.11_MANAGEMENT_DEV`)
- Open `DEV_AI_SERVICES` → AI Services branch (`25.11_AI_SERVICES_DEV`)

---

## 📁 Folder Structure After Setup

```
~/PROJECTS/CODA/DEVELOPMENT/
├── DEV/                    # Main dev branch (25.11_CODA_DEV_CM)
├── DEV_INVESTING/         # Investing branch (25.11_INVESTING_DEV)
├── DEV_FINANCE/           # Finance branch (25.11_FINANCE_DEV)
├── DEV_MANAGEMENT/        # Management branch (25.11_MANAGEMENT_DEV)
├── DEV_AI_SERVICES/       # AI Services branch (25.11_AI_SERVICES_DEV)
└── STG/                   # Your existing staging folder
```

---

## 🛠️ Common Worktree Commands

### List all worktrees
```bash
cd ~/PROJECTS/CODA/DEVELOPMENT/DEV
git worktree list
```

### Remove a worktree (when done)
```bash
cd ~/PROJECTS/CODA/DEVELOPMENT/DEV
git worktree remove ../DEV_INVESTING
# Or if folder is locked:
git worktree remove --force ../DEV_INVESTING
```

### Update all worktrees (pull latest changes)
```bash
# In main DEV folder
cd ~/PROJECTS/CODA/DEVELOPMENT/DEV
git fetch uat --all

# Then in each worktree folder
cd ~/PROJECTS/CODA/DEVELOPMENT/DEV_INVESTING
git pull uat 25.11_INVESTING_DEV
```

---

## 🎯 Workflow Example

### Scenario: Work on Investing app

1. **Open Cursor** → Select `DEV_INVESTING` folder
2. **Work on code** → Edit files in `coda/investing/`
3. **Commit changes**:
   ```bash
   cd ~/PROJECTS/CODA/DEVELOPMENT/DEV_INVESTING
   git add coda/investing/
   git commit -m "feat: Add new feature"
   git push uat 25.11_INVESTING_DEV
   ```
4. **Switch context** → Open another Cursor window with `DEV_FINANCE` folder

---

## ⚠️ Important Notes

1. **Same Repository**: All worktrees share the same `.git` directory (in DEV folder)
2. **No Conflicts**: Each worktree can be on a different branch simultaneously
3. **Disk Space**: Minimal overhead (shared git objects)
4. **Cursor**: Each folder opens independently in separate windows

---

## 🔄 Alternative: Manual Folder Approach (NOT Recommended)

If you prefer separate folders (not worktrees):
1. Clone the repo multiple times (uses more disk space)
2. Each folder is independent
3. Need to manage sync manually

**Why worktrees are better:**
- ✅ Shared git history (saves space)
- ✅ Automatic sync
- ✅ Same remote branches

---

## 📚 Quick Reference

| Folder | Branch | Purpose |
|--------|--------|---------|
| `DEV` | `25.11_CODA_DEV_CM` | Main dev (all docs) |
| `DEV_INVESTING` | `25.11_INVESTING_DEV` | Investing app only |
| `DEV_FINANCE` | `25.11_FINANCE_DEV` | Finance app only |
| `DEV_MANAGEMENT` | `25.11_MANAGEMENT_DEV` | Management app only |
| `DEV_AI_SERVICES` | `25.11_AI_SERVICES_DEV` | AI Services app only |

---

**Created:** November 22, 2025  
**Last Updated:** November 22, 2025



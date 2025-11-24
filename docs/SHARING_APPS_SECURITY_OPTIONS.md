# 🔒 Sharing Apps with External Developers - Security Options

## 🎯 Goal
Share a specific app (e.g., `investing`) with external developers **without exposing** other apps (`finance`, `management`, `ai_services`, etc.) for security reasons.

---

## 📋 Option 1: Separate Repository Per App (RECOMMENDED) ⭐

### How It Works
- Create separate Git repositories for each app
- Main repo keeps all apps (monorepo)
- Each app repo contains only that app + minimal dependencies
- External developers get access only to the specific app repo

### Structure
```
coda-investing/              # Separate repo for investing
├── coda/investing/         # Only investing app
├── coda/main/              # Minimal shared models
├── coda/accounts/          # Minimal user models
├── requirements.txt        # App-specific dependencies
├── setup.py                # Installable package
└── README.md

coda-finance/               # Separate repo for finance
├── coda/finance/
├── coda/main/
├── coda/accounts/
└── ...

coda-main/                  # Main private repo
├── All apps
└── Private access only
```

### Pros ✅
- **Strong isolation** - No way to access other apps
- **Clear boundaries** - Each repo is self-contained
- **Independent versioning** - Version each app separately
- **Easy access control** - GitHub/GitLab permissions per repo
- **Clean separation** - Developers see only what they need

### Cons ❌
- **Setup overhead** - Need to create/maintain multiple repos
- **Sync complexity** - Changes in main repo need to sync to app repos
- **Dependency management** - Shared models need to be duplicated or packaged

### Implementation
```bash
# 1. Create app-specific repo
git subtree push --prefix=coda/investing origin investing-standalone

# 2. Or use git-filter-repo to create clean history
git filter-repo --path coda/investing --path coda/main --path coda/accounts

# 3. Share only the app repo with external developers
# 4. Main repo stays private
```

---

## 📋 Option 2: Git Sparse Checkout + Access Control

### How It Works
- Keep monorepo structure
- Use Git sparse checkout to only check out specific directories
- GitHub/GitLab branch protection rules limit access
- External developers use sparse checkout to only see allowed apps

### Setup
```bash
# Developer gets access only to investing branch
git clone <repo> --filter=blob:none --sparse
cd <repo>
git sparse-checkout init --cone
git sparse-checkout set coda/investing coda/main coda/accounts
```

### Pros ✅
- **Monorepo benefits** - Keep all code together
- **Fine-grained control** - GitHub branch protection rules
- **Easy sync** - No need to sync between repos
- **Quick setup** - Uses existing Git features

### Cons ❌
- **GitHub access** - Still have access to repo (even if sparse)
- **History visibility** - Commit history might expose other app names
- **Less isolation** - Developer could theoretically access other branches

### Security Concerns ⚠️
- External developer still has repo access
- Could potentially checkout other branches or paths
- Commit history might leak information about other apps

---

## 📋 Option 3: Package Distribution (PyPI/Private Package Index)

### How It Works
- Package each app as installable Python package
- Publish to private package index (or PyPI if public is OK)
- External developers install via `pip install coda-investing`
- Only gets installed code, no source repo access

### Structure
```
coda-investing/
├── setup.py
├── MANIFEST.in
├── coda/
│   └── investing/
│       ├── models.py
│       ├── views.py
│       └── ...
└── requirements.txt
```

### Pros ✅
- **Strong security** - No repo access at all
- **Version control** - Release specific versions
- **Easy distribution** - Standard Python packaging
- **Dependency management** - Clear dependencies via requirements.txt

### Cons ❌
- **Development overhead** - Need to package for each release
- **Limited debugging** - External developers work with installed code
- **Sync complexity** - Changes need to be packaged and released

### Implementation
```python
# setup.py
from setuptools import setup, find_packages

setup(
    name='coda-investing',
    version='1.0.0',
    packages=find_packages(exclude=['tests*']),
    install_requires=[
        'Django>=3.2',
        # Only public dependencies
    ],
    include_package_data=True,
)
```

---

## 📋 Option 4: Docker Container + Limited Filesystem

### How It Works
- Create Docker container with only specific app
- External developers work inside container
- Container filesystem only contains allowed apps
- No access to host filesystem or other apps

### Structure
```dockerfile
FROM python:3.12
WORKDIR /app
COPY coda/investing ./coda/investing
COPY coda/main ./coda/main
COPY coda/accounts ./coda/accounts
COPY requirements.txt .
RUN pip install -r requirements.txt
```

### Pros ✅
- **Strong isolation** - Complete filesystem separation
- **Reproducible** - Same environment for all developers
- **Security** - Can restrict network access, filesystem access
- **Easy deployment** - Container can be deployed directly

### Cons ❌
- **Development experience** - Less convenient than native development
- **Overhead** - Need to maintain Docker images
- **Debugging** - More complex debugging in container

---

## 📋 Option 5: Mirror Repository with Filtered History

### How It Works
- Create mirror repository via CI/CD
- Filter history to only include specific app commits
- External developers work with filtered mirror
- Main repo stays completely private

### Implementation
```bash
# CI/CD script runs on push
git filter-repo \
  --path coda/investing \
  --path coda/main \
  --path coda/accounts \
  --path requirements.txt \
  --path setup.py \
  --to-subdirectory-filter coda

# Push filtered repo to mirror
git remote add mirror <mirror-repo-url>
git push mirror main
```

### Pros ✅
- **Clean history** - Only relevant commits
- **Automatic sync** - CI/CD handles mirroring
- **Strong isolation** - Main repo never exposed
- **Version tracking** - Can track which version external devs have

### Cons ❌
- **Complexity** - Requires CI/CD setup
- **Filtering overhead** - git filter-repo can be slow on large repos
- **Maintenance** - Need to maintain mirror sync scripts

---

## 📋 Option 6: Monorepo with Branch-Based Access Control

### How It Works
- Create separate branches for each app
- External developers get access only to specific branch
- Branch only contains that app + minimal dependencies
- Use GitHub/GitLab branch protection rules

### Structure (Already Implemented! ✅)
```
25.11_INVESTING_DEV     # Investing app only
25.11_FINANCE_DEV       # Finance app only
25.11_MANAGEMENT_DEV    # Management app only
25.11_CODA_DEV_CM       # Full monorepo (private)
```

### Pros ✅
- **Already set up** - You have this structure!
- **Easy sharing** - Just share branch access
- **Version control** - Each branch tracks its own changes
- **Quick to implement** - No additional setup needed

### Cons ❌
- **Branch access** - Developer could potentially see other branches
- **History** - Git history might contain references to other apps
- **Less isolated** - Still part of same repo

### Security Enhancement 🔒
```bash
# Add to .git/config for external developers
[remote "origin"]
    url = <repo-url>
    fetch = +refs/heads/25.11_INVESTING_DEV:refs/remotes/origin/investing
    fetch = +refs/heads/main:refs/remotes/origin/main  # Only if needed
    # Don't fetch other branches
```

---

## 🏆 Recommended Approach: Hybrid (Option 1 + Option 3)

### Strategy
1. **For Active Development**: Use separate repositories (Option 1)
   - External developers clone `coda-investing` repo
   - Main `coda-main` repo stays completely private
   
2. **For Distribution**: Package as Python package (Option 3)
   - Release stable versions via private PyPI
   - External developers install via `pip install coda-investing`
   - Can switch to package-based workflow later

### Implementation Plan

#### Phase 1: Create App-Specific Repos
```bash
# 1. Extract investing app to separate repo
cd /path/to/coda-main
git subtree push --prefix=coda/investing origin investing-standalone

# 2. Create clean repo with filtered history
git clone <main-repo> coda-investing-temp
cd coda-investing-temp
git filter-repo \
  --path coda/investing \
  --path coda/main \
  --path coda/accounts \
  --to-subdirectory-filter coda

# 3. Push to new public/private repo
git remote add origin <new-investing-repo-url>
git push -u origin main
```

#### Phase 2: Set Up Sync Script (CI/CD)
```bash
#!/bin/bash
# sync-investing.sh - Sync changes from main repo to investing repo

# On push to main repo, sync to investing repo
git subtree push --prefix=coda/investing origin investing-standalone

# Or use more sophisticated sync:
git filter-repo --path coda/investing --path coda/main --path coda/accounts
```

#### Phase 3: Package Distribution (Optional)
```python
# setup.py for coda-investing package
from setuptools import setup

setup(
    name='coda-investing',
    version='1.0.0',
    packages=['coda.investing'],
    # ...
)
```

---

## 🔒 Security Checklist

### Before Sharing Any App
- [ ] Remove all sensitive credentials/configs
- [ ] Remove references to other apps in code
- [ ] Remove commit history that mentions other apps
- [ ] Use environment variables for secrets
- [ ] Review all imports - ensure no cross-app dependencies
- [ ] Remove internal documentation
- [ ] Remove database connection strings
- [ ] Use `.gitignore` to exclude sensitive files

### For Separate Repos
- [ ] Create separate GitHub/GitLab org for shared repos
- [ ] Use branch protection rules
- [ ] Set up access control (who can read/write)
- [ ] Enable audit logs
- [ ] Use GitHub Actions for automated security checks

---

## 💡 Quick Start: Option 6 (Branch-Based) - Already Set Up! ✅

You already have this structure! Here's how to use it securely:

### For External Developer
```bash
# 1. Give them access only to investing branch
git clone --branch 25.11_INVESTING_DEV --single-branch <repo-url> coda-investing

# 2. They only see investing app
cd coda-investing
ls coda/  # Only sees investing, main, accounts, etc.

# 3. Configure to only fetch investing branch
git config remote.origin.fetch "+refs/heads/25.11_INVESTING_DEV:refs/remotes/origin/investing"
```

### Security Notes
- ✅ They can't see other branches (unless explicitly fetched)
- ⚠️ They might see commit history with other app references
- ⚠️ They still have repo access (could potentially checkout other branches)

### Enhanced Security
- Create separate GitHub org for shared branches
- Use GitHub branch protection rules
- Restrict branch access via GitHub permissions
- Consider using `git filter-repo` to clean commit history

---

## 🎯 Final Recommendation

**For Maximum Security**: Use **Option 1 (Separate Repos)** with **Option 3 (Package Distribution)** for stable releases.

**For Quick Start**: Use **Option 6 (Branch-Based)** which you already have, but enhance it with:
- Separate GitHub org
- Branch protection rules
- Clean commit history via `git filter-repo`

**For Active Development**: Separate repos give best isolation and security.

---

## 📚 Next Steps

1. **Decide which approach** based on your security requirements
2. **Test with one app** (investing) first
3. **Set up CI/CD sync** to keep repos in sync
4. **Create access control** rules on GitHub/GitLab
5. **Document** the process for future apps

---

**Created:** November 22, 2025  
**Status:** 📋 Discussion document - Ready for review and implementation



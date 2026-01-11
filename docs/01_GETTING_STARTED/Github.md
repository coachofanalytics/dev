# CODA — Branching + GitHub Push (DELIVERY MODE, NO REFACTORING, NO DEPLOY)

You are working in:
- Repo: ~/Projects/uat
- Current branch: 25.12_CODA_DEV_CM

## Goal
Create and push 3 new branches to GitHub only. DO NOT deploy to Heroku.

## Branches to create
1) 26.01_CODA_DEV_CM
   - Includes: all code + docs
   - Source: latest stable state of 25.12_CODA_DEV_CM after fixes

2) 26.01_CODA_UAT_CM
   - Includes: necessary code for UAT (codamakutano), but this task does NOT deploy
   - Keep changes minimal; do not delete runtime files

3) 26.01_CODA_PROD_CM
   - Includes: production-ready code for later deployment to codatrainingapp
   - DO NOT deploy to prod yet

## Deployment clarification (IMPORTANT)
- UAT Heroku app: codamakutano (prepare branch only; DO NOT deploy)
- PROD Heroku app: codatrainingapp (DO NOT deploy)
- No Heroku CLI commands, no pipelines, no config var changes, no Procfile/buildpack edits unless explicitly required for branch creation (generally not required).

## Hard constraints
- DO NOT refactor the application.
- DO NOT reorganize folders/modules.
- No history rewrite, no rebase/squash, no force-push.

## Docs definition
Docs include: docs/, *.md, architecture/notes folders if present.
For UAT/PROD branches, do NOT delete docs unless explicitly requested; prefer leaving code identical and relying on deploy ignore mechanisms if needed later.

## Required steps
1) Confirm clean working tree:
   - git status
   - poetry run python coda/manage.py check

2) Create DEV branch:
   - git checkout 25.12_CODA_DEV_CM
   - git pull (if appropriate)
   - git checkout -b 26.01_CODA_DEV_CM
   - poetry run python coda/manage.py check
   - git push -u origin 26.01_CODA_DEV_CM

3) Create UAT branch from DEV:
   - git checkout 26.01_CODA_DEV_CM
   - git checkout -b 26.01_CODA_UAT_CM
   - (No deploy changes; keep identical unless something is clearly dev-only and non-runtime)
   - poetry run python coda/manage.py check
   - git push -u origin 26.01_CODA_UAT_CM

4) Create PROD branch from DEV:
   - git checkout 26.01_CODA_DEV_CM
   - git checkout -b 26.01_CODA_PROD_CM
   - (No deploy changes; keep identical unless something is clearly dev-only and non-runtime)
   - poetry run python coda/manage.py check
   - git push -u origin 26.01_CODA_PROD_CM

5) Print summary:
   - Branch name
   - Intended environment
   - Any differences vs DEV (should be none unless explicitly necessary)
   - Commands used

## Verification Evidence Block (must output this)
- git branch --show-current
- git status
- git log -1 --oneline
- poetry run python coda/manage.py check
- git branch -vv
- git ls-remote --heads origin | egrep "26.01_CODA_DEV_CM|26.01_CODA_UAT_CM|26.01_CODA_PROD_CM"

Proceed now.

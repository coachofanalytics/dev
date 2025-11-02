# CHATGPT AI GUIDE FOR CODA DEVELOPMENT
**Purpose:** Practical guide for using ChatGPT (and similar OpenAI-based interfaces) to assist CODA development. These recommendations apply whether using ChatGPT in-browser, via the API, or integrated into internal tooling.
**Last Updated:** October 29, 2025

---

## 🔑 READ THIS FIRST
- This document complements `CURSOR_AI_GUIDE.md`. Read that file for repository-specific workflows, branch rules, and deployment checklists. Use this guide when working with ChatGPT-style systems.
- Always follow security rules: do not paste secrets (API keys, credentials, PII) into prompts or responses.

---

## 🎯 QUICK START (When starting any ChatGPT-assisted task)
1. Read the feature docs: `docs/apps/finance/[Feature]/README.md` and `REQUIREMENTS.md`.
2. Collect minimal context: file paths, error messages, example inputs/outputs.
3. Prepare a concise system prompt + 1–3 examples (few-shot) if task is subtle.
4. Run small experiments locally (unit tests or static analysis) before applying changes.

---

## 🧭 CONTRACT (what to expect from ChatGPT prompts)
- Inputs: Short context (2–6 files or function snippets), clear instruction (one task), desired output format (diff, code block, test).
- Outputs: Suggested code/text, explanation of changes, risks, and tests to run.
- Error modes: hallucinations (fabricated file names/APIs), partial/incomplete fixes, or unsafe suggestions. Always verify outputs.

---

## ✍️ PROMPTING BEST PRACTICES
- System message: set the role and constraints. Example: "You are a careful senior Django engineer. Return only valid Python diffs or short explanations. Do not invent file paths. If uncertain, ask for clarification."
- Keep prompts focused and small. Split large tasks into subtasks.
- Provide sample inputs, expected outputs, and failing tests when requesting debugging help.
- Use explicit format instructions: "Return a git-style patch, or only the changed file with context lines." If you want a code diff, say so.
- Use few-shot examples for non-trivial format expectations (e.g., how to structure migrations).

---

## 🔬 EXAMPLE PROMPTS
- Code change (small): "Refactor `coda/finance/views.py::FooView` to use `select_related` for 'user' and add a unit test that verifies no N+1 for 3 sample objects. Return only a patch." 
- Bug triage: "Given this traceback: [paste], and this file `.../views.py` (attach), list 3 likely causes and a recommended fix with exact lines to edit."
- Docs update: "Update `docs/apps/finance/Budget/IMPLEMENTATION.md` to include the migration steps; return only the updated markdown fragment."

---

## 🛡️ SECURITY & DATA HANDLING (CRITICAL)
- Never paste secrets (API keys, private tokens) into chat. If you must illustrate, redact or use placeholders: `GOTOMEETING_CLIENT_ID=<<REDACTED>>`.
- For PII or production logs, scrub or synthesize example data before sending.
- Prefer asking the model for code patterns rather than real credentials. Implement secrets with environment variables and secret managers (Heroku config vars, AWS Secrets Manager, Azure Key Vault).
- Keep an audit of prompts and responses in `docs/_temp_summaries/AI_PROMPTS_LOG.md` if outputs affect the codebase.

---

## 🧾 API KEYS AND ACCESS
- Use a project-level API key for automation only after review. Scope keys when possible and rotate regularly.
- Do not commit API keys to git. Add keys to environment via `Heroku config:set` or CI secrets.
- For local testing on Windows PowerShell, set variables using:

```powershell
# PowerShell example
$env:OPENAI_API_KEY = "<<REDACTED>>"
```

---

## 🧠 MODEL CHOICES & PARAMETERS
- Prefer the most capable model available for complex reasoning (e.g., GPT-4 family), but test costs and latency.
- Use lower-temp for deterministic outputs (code patches): `temperature: 0 - 0.2`.
- Use higher-temp when generating creative text (e.g., help text, commit message templates): `temperature: 0.6 - 0.9`.
- Use `max_tokens` conservatively; keep prompts and expected outputs within token limits.
- Consider streaming partial responses for long outputs when supported.

---

## 🛠 CODE-GENERATION SAFEGUARDS
- Always request a unit test or validation when asking for code changes. Example: "Return the code patch and a pytest that demonstrates the change." 
- Ask for reasoning and a short test plan (1–3 steps) to verify the change locally.
- Prefer returning diffs or file snippets rather than full files to reduce hallucinated context.
- Validate generated code with linters and test runs before committing.

---

## ✅ REVIEW & QA WORKFLOW WITH CHATGPT
1. Prompt the model for a patch + tests.
2. Review the patch thoroughly: check imports, types, migrations, and settings usage.
3. Run tests locally: `./tests/run_tests.sh --regression` (or `bash ./tests/run_tests.sh` on Windows WSL). Note: on PowerShell you might use `bash ./tests/run_tests.sh` or run tests via `python -m pytest` as appropriate.
4. If patch touches models, create and inspect migrations: `cd coda && python manage.py makemigrations --dry-run` and `python manage.py showmigrations`.
5. If approved, create a PR with the patch and include the model's prompt and key outputs in the PR description (redact any secrets).

---

## 🔁 HUMAN-IN-THE-LOOP RULES
- Never accept a generated patch without a human review and test run.
- For production deployments, require an explicit human approval step (see `CURSOR_AI_GUIDE.md` for deployment rules).
- If a model suggests destructive commands (e.g., `git push --force`), treat them as proposals and require safer variants (`--force-with-lease`) and a rollback plan.

---

## 🧪 TESTING & CI
- Require tests for any behavior changes. Add unit + integration tests as appropriate.
- In PRs, include the prompt used and the model's answer (sanitized) in a collapsed section in the PR so reviewers can see rationale.
- Add CI checks that run linters and unit tests. Optionally run lightweight static checks on generated code via `ruff`, `mypy`, or `flake8`.

---

## 🔍 MONITORING, LOGGING & AUDIT
- Log AI-assisted changes in a central audit file under `docs/_temp_summaries/` and tag which PRs used ChatGPT.
- Monitor errors potentially introduced by AI-suggested patches (use Sentry or equivalent). Create alerts for sudden increases in test failures or production errors after AI-assisted merges.

---

## 🧩 PROMPT TEMPLATES (Reusable)
- Bug fix template:

```
System: You are a precise Django developer. Return a git-style patch and a short test.
Task: Fix the failure caused by this traceback: <paste traceback>
Context: Files: <list file paths> (attach snippets)
Output: Patch + pytest to reproduce the bug + 3-line rationale.
```

- Documentation update template:

```
System: You are a clear technical writer. Update the specified README with a short migration plan.
Task: Add migration steps for models X→Y.
Context: Current text: <paste fragment>
Output: Updated markdown fragment only.
```

---

## ⚠️ COMMON PITFALLS (and how to avoid them)
- Hallucinated file paths: always verify file existence (`git ls-files | grep <path>`).
- Overly broad prompts: break tasks into smaller steps and iterate.
- Committing generated secrets: never paste secret values in prompts — use placeholders.
- Blind trust: always run tests, linters, and a quick code review.

---

## 🚀 ADVANCED USAGE & INTEGRATION IDEAS
- Use ChatGPT as a pre-PR assistant: generate a draft patch + tests, then human reviews and submits the PR.
- Integrate into CI for suggested changelogs or PR summaries (model returns only summary text, never secrets).
- Cache model responses for identical prompts to control costs.

---

## 📚 REFERENCES & LINKS
- `docs/01_GETTING_STARTED/CURSOR_AI_GUIDE.md` — repo and deployment rules
- `docs/_temp_summaries/AI_ASSISTANT_WORKLOG.md` — record of AI actions
- `docs/apps/ai_services/GoToMeeting/` — example of AI-reviewed feature docs

---

## ✅ FINAL REMINDERS
- Always human-review and test AI-suggested code.
- Do not share secrets or real PII in prompts.
- Keep prompts small, reproducible, and attach examples.

**Maintained by:** CODA Development Team
**Last Updated:** October 29, 2025

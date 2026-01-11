DAF Retrospective — INPUT COLLECTION PROMPT (Standardize what you send back)

Goal:
I am preparing a retrospective analysis to reduce prompt volume and create a reusable delivery playbook (.md). 
Your job in this step is NOT to analyze or propose improvements yet.
Your job is to help me COLLECT and STANDARDIZE the inputs from this chat/Cursor session into a clean “Retrospective Input Package” that I can paste into a separate retrospective analyzer.

Important constraints:
- Do NOT implement code.
- Do NOT propose refactors.
- Do NOT generalize lessons learned yet.
- Only extract, organize, and label what happened in this session.

What you will receive:
This conversation log (and optionally: PR notes, diffs, commit messages, screenshots, or a before/after description).

Task:
Generate a single Markdown artifact titled “Retrospective Input Package — Session Summary” with the sections below. 
If information is missing, write “Unknown / Not provided” and continue.

Required Output (Markdown):

# Retrospective Input Package — Session Summary

## 1) Session Metadata
- Session type: (ChatGPT chat / Cursor composer / Cursor chat / Mixed)
- Date range covered:
- Primary module/domain: (DAF / Tasks / Evidence / Meetings / Requirements / Other)
- Environment/context: (branch name, repo path, settings/env if mentioned)
- Participants/roles mentioned: (developer, manager, etc.)

## 2) Objective of This Session
- Stated goal at the start:
- What “done” was supposed to look like:

## 3) Scope of Work Touched
List what was actually worked on in this session:
- Files touched (explicitly mentioned):
- Features/flows touched:
- URLs/endpoints mentioned:
- Templates mentioned:
- Models mentioned:
- Services/utils mentioned:
- Tests mentioned:

## 4) Actions Taken (Chronological)
Provide a concise timeline of what happened (bullet list). 
Each bullet should be: 
- [Step] Action → Outcome → Evidence (quote/log snippet if available)

## 5) Decisions & Rationale
List concrete decisions made (even small ones):
- Decision:
- Why:
- Tradeoff:
- Follow-up needed:

## 6) Problems / Errors / Friction Points
For each issue:
- Symptom:
- Root cause suspected (if stated):
- How it was resolved (if resolved):
- What remains unresolved:

## 7) Output Artifacts Produced
- Code changes described (if any):
- Commands executed (if any):
- Prompts used that were “key” (copy them if present):
- Documents created/updated (if any):

## 8) Current State at End of Session
- What is working now:
- What is broken now:
- What is incomplete:
- Known risks introduced:

## 9) Next Steps (as stated in the session)
- Immediate next step:
- Dependencies/blockers:
- Suggested priority:

## 10) Source Excerpts (Minimal)
Include up to 10 short excerpts (max 2–3 lines each) that best capture:
- the goal,
- the key decision,
- the biggest blocker,
- and the final state.
(If none, write “None provided”.)

Formatting rules:
- Keep it concise and factual.
- Do not add new ideas.
- Do not judge the work.
- Do not recommend improvements.
- Prefer exact names for functions/files/URLs where available.

Now produce the “Retrospective Input Package — Session Summary” for THIS conversation/session.
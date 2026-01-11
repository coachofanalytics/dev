Here’s a ready-to-drop-in DEV_WORKFLOW.md you can put in the repo root (~/Projects/uat/DEV_WORKFLOW.md).

You can create it with:

cd ~/Projects/uat
nvim DEV_WORKFLOW.md


…and paste everything below into the file.

# CODA UAT – Dev Environment Workflow

This document is the **morning cheat sheet** for rebuilding the full environment after a restart or shutdown.

Assumptions:

- Project root: `~/Projects/uat`
- Terminal: iTerm2
- tmux prefix: **Ctrl + t** (written as `<prefix>` below)
- Layout:
  - Left pane: Neovim / LazyVim (editing)
  - Top-right pane: Poetry shell (tests + server)
  - Bottom-right pane: LazyGit (git dashboard)

If you change the tmux prefix later (e.g. to Ctrl + a), mentally replace `<prefix>` with that key.

---

## 1. Start of Day – Get Into the Environment

1. Open **iTerm2**.
2. Go to the UAT project:

   ```bash
   cd ~/Projects/uat


Attach or create the uat tmux session:

tmux new -As uat


If the session already exists → attaches and restores panes.

If it does not exist → creates a new session.

If layout is already there, skip to Section 3.
If it’s a brand-new window, follow Section 2 to rebuild the layout.

2. Rebuild tmux Layout (Only When Needed)

You start in a single tmux pane.

Vertical split (Neovim left, terminals right):

<prefix>  |


Move to the right pane:

Alt + Right (repeat if needed), or

<prefix> o to cycle panes.

Horizontal split on the right (top-right + bottom-right):

<prefix>  -


Now you have:

Pane 1 – left

Pane 2 – top-right

Pane 3 – bottom-right

Pane navigation:

Alt + Left/Right/Up/Down → move between panes
(and optionally Ctrl + h/j/k/l if configured).

3. Left Pane – Neovim / LazyVim (Editor)

Move to the left pane:

Alt + Left   (repeat until cursor is at the left)


Start Neovim:

cd ~/Projects/uat
nvim

LazyVim Keybindings to Remember

Explorer (file tree):

<space> e


Fuzzy find file:

<space> f f


New file:

<space> f n   → type path (e.g. tests/.../test_x.py) → Enter


Save (works in normal/insert/visual):

Ctrl + s


Format current file:

<space> c f


Toggle format on save (per buffer):

<space> u F


Buffers / “tabs” at top:

Next buffer: Shift + l

Previous buffer: Shift + h

Buffer picker: <space> ,

Close current buffer: <space> b d

Useful Vim basics:

Normal mode: Esc

Insert mode: i

Quit buffer/window: :q

Save & quit: :wq

4. Top-Right Pane – Poetry Shell (Tests + Server)

Move to top-right pane:

Alt + Right   or   Alt + Up


Ensure you are in project root:

cd ~/Projects/uat

Standard Poetry Commands

Run all tests:

poetry run pytest


Run tests for a specific file (edit path as needed):

poetry run pytest tests/path/to/test_file.py


Run Django dev server (port 5000):

poetry run python coda/manage.py runserver 5000


Stop tests/server:

Ctrl + C


Rule of thumb: always use poetry run ... for Python commands in this project so you stay in the correct virtualenv.

5. Bottom-Right Pane – LazyGit (Git Dashboard)

Move to bottom-right pane:

Alt + Right   or   Alt + Down


Ensure you are in project root:

cd ~/Projects/uat


Start LazyGit:

lazygit

LazyGit Keys to Remember

Move in lists: j / k

Switch panels: Tab (and Shift + Tab to go back)

Direct panel selection: numbers 1–5
(e.g. 2 → Files, 3 → Branches, 4 → Commits)

In Files panel (2):

Stage / unstage file or hunk: Space

Open hunks for a file: Enter

Discard changes: d (will confirm)

Commits:

Commit staged changes: c → type message → follow prompt (usually Enter to confirm)

Remotes:

Push current branch: P then p

Pull: p

Quit LazyGit (back to shell): q

From the shell in that pane you can still run raw git commands:

git status
git diff
git add path/to/file.py
git commit -m "message"
git push

6. Typical Development Loop

Edit code/tests (left pane, Neovim)

<space> f f → open file

i → change code

Esc → normal mode

Ctrl + s → save

<space> c f → format

Run tests (top-right pane)

poetry run pytest

or poetry run pytest tests/path/to/test_file.py

Inspect results

Fix failing tests or errors in Neovim

Repeat test run as needed

Commit and push (bottom-right pane)

lazygit

Stage (Space), commit (c), push (P then p)

Quit LazyGit with q when done

Optional cleanup

In Neovim explorer (<space> e), delete temp files:

Navigate to file → d → y to confirm

7. End of Day

You do not need to manually stop tmux; you can simply:

Close iTerm2, or

Shut down the laptop.

Next day the start sequence is always:

cd ~/Projects/uat
tmux new -As uat


If the old session exists, you reattach to everything as it was.
If not, rebuild layout using Section 2.

8. Quick Troubleshooting

“Command not found: poetry”
Make sure Poetry is installed and on PATH. Check with:

which poetry
poetry --version


“ModuleNotFoundError: django / dotenv / etc.” in tests or server
From project root:

poetry run pip install -r requirements.txt


LazyGit says ‘not a git repository’
Confirm you are in the repo root:

pwd
ls


Make sure you see .git, pyproject.toml, etc. Then run lazygit again.

Pane layout gone weird
Start a new tmux window and rebuild:

<prefix> c          # new window
<prefix> |          # split vertical
<prefix> -          # split horizontal on the right


Then re-launch Neovim / Poetry / LazyGit in the respective panes.

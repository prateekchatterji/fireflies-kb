# Execution Guide

Copy-pasteable command sequences for every workflow this project supports. For understanding *how* the project works, see `PROJECT_KNOWLEDGE_BASE.md`. This doc is about *what to type when*.

**All commands assume Git Bash on Windows.**

---

## 0. Setup that every session needs

Every workflow below starts with these three lines. If your prompt already shows `(.venv)`, you can skip them.

```bash
cd /c/Users/prate/dev/fireflies-kb
source .venv/Scripts/activate
which python                          # sanity check — should point inside .venv/
```

---

## 1. Daily refresh (the everyday flow)

**When:** anytime you want to pull the latest meetings and update the Claude Project.
**What it does:** incremental fetch since last watermark, then re-bundles all priority meetings.

```bash
cd /c/Users/prate/dev/fireflies-kb
source .venv/Scripts/activate
python fetch_meetings.py
python bundle_priority_meetings.py
ls -lt data/bundles/ | head -10       # see the newest bundles
```

Then in your browser: drag new `.md` files from `data/bundles/` into your Claude Project.

---

## 2. Priority list changed

**When:** you added or removed someone in `priority_people.txt`.
**What it does:** re-bundles from existing raw data (no new fetch needed — the JSONs already contain all meetings).

```bash
cd /c/Users/prate/dev/fireflies-kb
source .venv/Scripts/activate
python bundle_priority_meetings.py
```

If a person was **removed**, also delete the stale bundles for meetings that no longer qualify. Currently there's no automatic cleanup — you'd manually delete from `data/bundles/`, or nuke and regenerate:

```bash
rm data/bundles/*.md
python bundle_priority_meetings.py
```

---

## 3. Retry failed fetches

**When:** the previous run reported `failed=N > 0`, or you notice missing meetings.
**What it does:** the watermark cap already forces retry on next normal run, but this forces it immediately.

```bash
cd /c/Users/prate/dev/fireflies-kb
source .venv/Scripts/activate
rm data/.last_fetch
python fetch_meetings.py
```

Existing JSONs are skipped (idempotent), so this only fetches the missing meetings.

---

## 4. Full 30-day backfill from scratch

**When:** first run on a new machine, or you suspect the raw data is stale/corrupt.
**What it does:** ignores the watermark, re-lists 30 days, fetches anything missing.

```bash
cd /c/Users/prate/dev/fireflies-kb
source .venv/Scripts/activate
rm -f data/.last_fetch
python fetch_meetings.py
python bundle_priority_meetings.py
```

**Before running:** plug in the charger and set Windows Power settings to "never sleep when plugged in" — a full backfill can take 5-15 minutes. Change it back afterward.

---

## 5. Extend the fetch window (older than 30 days)

**When:** you need meetings from further back.
**What it does:** temporarily widens the backfill window.

Edit `fetch_meetings.py` and change `BACKFILL_DAYS = 30` to your desired number (e.g. `90`). Then:

```bash
cd /c/Users/prate/dev/fireflies-kb
source .venv/Scripts/activate
rm -f data/.last_fetch
python fetch_meetings.py
python bundle_priority_meetings.py
```

**Remember to revert `BACKFILL_DAYS` to 30 afterward**, or your next disaster-recovery run will pull 90 days again.

Note: Fireflies retains transcripts based on your plan tier — very old meetings may not be available.

---

## 6. Sanity check / diagnostics

**When:** something feels off and you want to see the state of the project without changing anything.

```bash
cd /c/Users/prate/dev/fireflies-kb
source .venv/Scripts/activate

# Environment
which python
pip list | grep -E "requests|dotenv"

# Data inventory
ls data/raw/ | wc -l                  # how many raw JSONs
ls data/bundles/ | wc -l              # how many bundles
du -sh data/raw data/bundles data/digests

# Watermark
cat data/.last_fetch 2>/dev/null || echo "(no watermark — next run will backfill)"

# Newest bundles
ls -lt data/bundles/ | head -6

# Newest raw JSONs
ls -lt data/raw/ | head -6
```

---

## 7. Reset everything (nuclear option)

**When:** you want to start completely fresh. **This deletes all downloaded meetings.**

```bash
cd /c/Users/prate/dev/fireflies-kb
source .venv/Scripts/activate
rm -rf data/raw data/bundles data/digests data/.last_fetch
mkdir -p data/raw data/bundles data/digests
python fetch_meetings.py
python bundle_priority_meetings.py
```

The `data/` folder is in `.gitignore`, so this doesn't affect git.

---

## 8. Version control moves after any change

After editing code or docs:

```bash
cd /c/Users/prate/dev/fireflies-kb
git status                            # what changed
git --no-pager diff <file>            # eyeball the diff
git add <file>
git commit -m "type: short summary"   # type = fix|feat|docs|refactor|chore
git push
```

---

## 9. Automating repeated flows (later)

Once a command sequence above becomes routine, wrap it in a shell script so you don't retype it.

Example: create `scripts/refresh.sh`:

```bash
#!/bin/bash
set -e
cd /c/Users/prate/dev/fireflies-kb
source .venv/Scripts/activate
python fetch_meetings.py
python bundle_priority_meetings.py
```

Make it executable and run:

```bash
chmod +x scripts/refresh.sh
./scripts/refresh.sh
```

**Rules of thumb for what to script:**
- If you've typed the same sequence 3+ times, script it.
- If not, don't. Premature scripting creates a graveyard of `run_v2_final.sh` files nobody remembers.
- Give scripts descriptive names (`refresh.sh`, `backfill.sh`, `retry_failures.sh`) — not `run.sh`.
- Keep them in a `scripts/` folder to avoid cluttering the project root.
- `set -e` at the top means "stop immediately if any command fails" — a good safety default.

Once utilities get unified under a single `cli.py` (planned), shell scripts get much shorter:

```bash
#!/bin/bash
cd /c/Users/prate/dev/fireflies-kb
source .venv/Scripts/activate
python cli.py refresh
```

---

## Quick reference table

| I want to... | Section |
|---|---|
| Pull latest meetings and re-bundle | §1 |
| Re-bundle after editing `priority_people.txt` | §2 |
| Retry meetings that failed last run | §3 |
| Fetch everything from scratch (30 days) | §4 |
| Fetch older than 30 days | §5 |
| Check the health of the project | §6 |
| Blow away all data and start over | §7 |
| Commit and push changes | §8 |
| Automate a routine sequence | §9 |

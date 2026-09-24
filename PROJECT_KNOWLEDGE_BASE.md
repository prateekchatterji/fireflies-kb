# Fireflies → Claude Project Pipeline

A personal knowledge base for the meeting-extraction project. Written for someone who is new to Python and will forget the details between runs. Read top-to-bottom the first time; after that, the **Regular Workflow** section is all you usually need.

> **Looking for copy-pasteable commands?** See `EXECUTION_GUIDE.md`. This doc explains _how the project works_; the execution guide explains _what to type when_.

---

## 1. What this project does

You record meetings with Fireflies.ai. Fireflies has all your transcripts, summaries, and action items — but searching across many meetings inside Fireflies is awkward, and you can't easily ask an LLM to reason across them.

This project solves that in two steps:

1. **Fetch**: download recent meetings from Fireflies as raw JSON files (one file per meeting), saved to disk.
2. **Bundle**: filter those meetings to the ones that include specific "priority people" (you, key colleagues), and render each surviving meeting as a clean Markdown file.

The Markdown files are then uploaded to a **Claude Project** as project knowledge, so you can ask Claude questions across all your important meetings.

```
Fireflies API  →  data/raw/*.json  →  data/bundles/*.md  →  Claude Project
   (cloud)         (fetch_meetings)    (bundle_priority...)    (manual upload)
```

---

## 2. Project layout

> **Windows + Git Bash notes.** Two things to remember:
>
> - In Git Bash, `C:\path\to\fireflies-kb` is written as `/c/path/to/fireflies-kb` (forward slashes, drive letter becomes `/c/`).
> - To activate the Python venv on Windows you use `.venv/Scripts/activate`, **not** `.venv/bin/activate` (that's the Mac/Linux path — most tutorials online show that one).

```
fireflies-kb/
├── .env                            ← secret: your Fireflies API key. NEVER commit.
├── .gitignore                      ← tells git to ignore .env, data/, .venv/ etc.
├── priority_people.example.txt     ← template committed to the repo
├── priority_people.txt             ← your real list; gitignored, stays local
├── requirements.txt                ← Python libraries this project needs
├── fetch_meetings.py               ← script 1: pulls meetings from Fireflies
├── bundle_priority_meetings.py     ← script 2: filters + renders to Markdown
└── data/                           ← all generated content; not committed to git
    ├── raw/                        ← every meeting pulled from Fireflies, as JSON
    ├── bundles/                    ← priority meetings rendered to Markdown
    │                                 (these are what you upload to the Claude Project)
    └── digests/                    ← reserved for future use (e.g. cross-meeting
                                      summaries, weekly rollups). Empty for now.
```

---

## 3. How each piece works

### `priority_people.txt` (and `priority_people.example.txt`)

`priority_people.example.txt` is committed to the repo and shows the format. On first setup you copy it to `priority_people.txt` and fill in real emails. The real file is gitignored so it never gets committed.

Both files are plain text. One email per line. Lines starting with `#` are comments and ignored. A meeting is "priority" if **any** of its participants matches **any** email in the file. Case-insensitive.

Edit `priority_people.txt` freely — add or remove emails as priorities change.

### `.env`
A plain text file that holds your secret API key. Format:
```
FIREFLIES_API_KEY=your-key-here
```
Never share, never commit to git. `.gitignore` already excludes it.

If the key ever leaks (e.g. pasted in a chat), regenerate it in Fireflies: **Settings → Developer Settings → regenerate**.

### `fetch_meetings.py`
- Reads `FIREFLIES_API_KEY` from `.env`.
- Decides its date window: if `data/.last_fetch` exists, it fetches from that timestamp minus a 2-day overlap; otherwise it backfills the last 30 days.
- Asks Fireflies' GraphQL API for the list of transcripts in that window, paging 25 at a time.
- For each meeting, fetches the full detail (summary, action items, full transcript with timestamps).
- Saves each meeting to `data/raw/{meeting-id}.json`.
- **Idempotent**: if `{meeting-id}.json` already exists, it's skipped. Safe to re-run.
- **Failure-aware**: if any detail fetch fails, the watermark is held back to just before the earliest failure, so those meetings get retried on the next run.
- Uses a small helper `parse_meeting_date()` to normalize Fireflies' date fields (which come as either epoch milliseconds or ISO strings).

### `bundle_priority_meetings.py`
- Reads `priority_people.txt`.
- Walks every `.json` in `data/raw/`.
- Keeps meetings whose participant list overlaps with priority people.
- For each kept meeting, writes a Markdown file to `data/bundles/` named:
  `YYYY-MM-DD_meeting-title_shortid.md`
- The Markdown contains: title, date, duration, participants, Fireflies summary, action items, keywords, and the full timestamped transcript.
- Sorted newest first in console output.

---

## 4. One-time setup

You only do this once on a new computer.

### 4a. Install Python 3
```bash
python --version
```
If you see `Python 3.10.x` or higher, you're set. Otherwise install from python.org or via Homebrew (`brew install python`).

### 4b. Clone the repo
```bash
git clone https://github.com/prateekchatterji/fireflies-kb.git
cd fireflies-kb
```

### 4c. Create a virtual environment
```bash
python -m venv .venv
```
This creates a hidden `.venv/` folder. You only do this once.

### 4d. Activate the venv
**Every time you open a new Git Bash window to work on this project, run:**
```bash
source .venv/Scripts/activate
```
Your prompt gets a `(.venv)` prefix. That's how you know it's active.

> ⚠️ On Windows the path is `.venv/Scripts/activate`. On Mac/Linux it would be `.venv/bin/activate`.

To leave the venv later: `deactivate`.

### 4e. Install dependencies
With the venv active:
```bash
pip install -r requirements.txt
```
This installs `requests` and `python-dotenv`.

### 4f. Create `.env`
```bash
echo "FIREFLIES_API_KEY=paste-your-key-here" > .env
```
Then edit `.env` and replace `paste-your-key-here` with your actual Fireflies API key (from Fireflies → Settings → Developer Settings).

### 4g. Create your `priority_people.txt`
```bash
cp priority_people.example.txt priority_people.txt
```
Then edit `priority_people.txt` to list the real emails you care about, one per line.

---

## 5. Regular workflow

Every time you want to refresh your Claude Project with new meetings:

```bash
# 1. Open Git Bash and go to the project folder
cd /c/path/to/fireflies-kb

# 2. Activate the venv (note: Scripts/ on Windows, not bin/)
source .venv/Scripts/activate

# 3. Sanity check — confirm venv is active and deps are installed
which python                    # should point inside .venv/
pip list | grep -E "requests|dotenv"   # should show both

# 4. Pull new meetings from Fireflies
python fetch_meetings.py

# 5. Re-bundle the priority meetings to Markdown
python bundle_priority_meetings.py

# 6. Done — see what was produced
ls -lh data/bundles/ | head
```

Then:
- Open your Claude Project in the browser.
- Drag the new `.md` files from `data/bundles/` into the project knowledge.
- (If updating files that already exist there, delete the old version first.)

---

## 6. Useful bash commands (cheat sheet)

```bash
# See where you are
pwd

# List files in the current folder (long format with sizes)
ls -lh

# List meetings you've fetched
ls data/raw/ | wc -l         # how many JSON files
ls data/bundles/             # which markdown bundles exist

# Look at the most recent 5 bundles
ls -lt data/bundles/ | head -6

# Read one bundle in the terminal
cat data/bundles/<filename>.md

# Quickly check your .env (careful — it shows the key)
cat .env

# Clear out everything and start fresh (DANGER — deletes downloaded meetings)
rm -rf data/

# Update your dependencies if you ever change requirements.txt
pip install -r requirements.txt

# Show which Python libraries are installed in the venv
pip list

# Exit the venv when done
deactivate
```

---

## 7. Common situations & how to handle them

**"I added someone to `priority_people.txt`. Do I need to re-fetch?"**
No. The raw JSONs already contain every meeting from the last 30 days regardless of priority. Just re-run `python bundle_priority_meetings.py`.

**"I want meetings older than 30 days."**
Edit `fetch_meetings.py`, find `BACKFILL_DAYS = 30`, change to whatever you need. Re-run `fetch_meetings.py`. Note: Fireflies retains transcripts based on your plan; very old ones may not be available.

**"I want to delete old bundles before regenerating."**
```bash
rm data/bundles/*.md
python bundle_priority_meetings.py
```
Safe to do — the raw JSONs in `data/raw/` are untouched, and bundling re-creates everything.

**"The script errored with `Missing FIREFLIES_API_KEY in .env`."**
Either `.env` doesn't exist in the current folder, or the line inside it is malformed. Check with `cat .env`. The line must be exactly `FIREFLIES_API_KEY=...` with no quotes and no spaces around `=`.

**"The script errored with an HTTP 401 or `Unauthorized`."**
Your API key is wrong, expired, or rotated. Get a fresh one from Fireflies and update `.env`.

**"The script says `command not found: python`."**
Python isn't installed, or your venv isn't activated. Run `source .venv/Scripts/activate` first.

**"It says `ModuleNotFoundError: No module named 'requests'`."**
The venv isn't active, or dependencies weren't installed. Run `source .venv/Scripts/activate && pip install -r requirements.txt`.

**"I accidentally committed `.env` to git."**
Rotate the key in Fireflies immediately. Then remove the file from git history using `git filter-repo` (non-trivial — worth reading its docs before running).

**"Some meetings failed to fetch and I want them retried."**
The watermark cap retries them automatically on the next run. If you want to force it right away:
```bash
rm data/.last_fetch
python fetch_meetings.py
```
Existing meetings are still skipped (idempotent), so this only fetches the missing ones.

**"My laptop went to sleep in the middle of a long fetch."**
Two safeguards:
1. Failed meetings will be retried on the next run (see above).
2. To prevent it: before a long backfill, plug in the charger and set Windows Settings → System → Power → "when plugged in, PC goes to sleep after" → **Never**. Set it back afterward.

---

## 8. Things to know about the data

- **Participant emails**: matching is by exact email (lowercased). If a colleague joined under an alias, they'll be missed. Spot-check by opening a raw JSON.
- **Transcript sensitivity**: transcripts can contain sensitive operational content — names, discussions, and sometimes credentials mentioned aloud in meetings. This is why `data/` is gitignored. **Do not remove `data/` from `.gitignore`**, and do not attach raw JSONs or bundles to public issues, gists, or forum posts.
- **Transcript size**: full transcripts can be long. If you upload many bundles to a Claude Project you may hit the project knowledge cap. If that happens, consider a stripped-down bundler that omits the transcript and keeps only the summary.
- **Recurring meetings**: each occurrence is its own meeting in Fireflies, so a weekly 1:1 becomes one bundle per week. Intentional.
- **Idempotency**: `fetch_meetings.py` skips meetings already on disk. If a meeting's transcript was updated after you first fetched it, your local copy is stale. To force a refresh: `rm data/raw/<id>.json` and re-run.

---

## 9. Reducing Fireflies API calls (implemented)

`fetch_meetings.py` uses an incremental strategy. Two kinds of API call happen per run:

1. **List query** — pages through every meeting in the date window, 25 per page.
2. **Detail query** — one per meeting _that isn't already on disk_. Deduplicated by the `if out_path.exists(): skipped += 1; continue` check.

### How the watermark works
On startup the script checks for `data/.last_fetch`:
- **If it exists**, sets `FROM_DATE = last_fetch - 2 days` (the 2-day overlap catches any meeting whose transcript finalized late).
- **If not**, backfills the last 30 days (first-run behaviour).

At the end of a successful run, the script writes the current time to `data/.last_fetch` as the new watermark. A daily run then lists only ~3 days of meetings instead of 30 — roughly a **10× reduction** in list calls after the first run.

### Failure handling
If any detail fetch fails during a run (network hiccup, laptop sleep, API blip), the watermark is capped at the earliest failed meeting's date minus 1 day of safety margin. Failed meetings fall inside the next run's window and get retried.

Output on a run with failures:
```
Done. fetched=42, skipped(existing)=100, failed=3
Saved watermark to data\.last_fetch (2026-06-25T00:00:00+00:00)
  (capped at earliest failure so 3 failed meeting(s) get retried)
```

### Manual controls
- **Force a full 30-day backfill**: `rm data/.last_fetch && python fetch_meetings.py`.
- **Adjust the safety overlap**: edit `OVERLAP_DAYS = 2` at the top of the script.
- **Adjust first-run window**: edit `BACKFILL_DAYS = 30`.

### Other levers (not implemented — future consideration)
- **Slow down further**: increase `time.sleep(0.5)` between detail fetches.
- **Cap per run**: add `if fetched >= 50: break` inside the loop.
- **Pre-filter by participants**: skip the detail call for non-priority meetings. Saves the most expensive calls. Trade-off: losing the option to re-bundle for a new priority person without re-fetching.

---

## 10. Working with bundles — local & low-cost options

You don't need a frontier model to do useful things with these meeting bundles. The transcripts are bounded, the questions are usually narrow, and small local models handle that well.

### Option A — Ollama (fully local, free)
[Ollama](https://ollama.com) runs LLMs on your own machine. Windows installer, background service, local API on `localhost:11434`.

Recommended starter models:
- **`llama3.1:8b`** — good general-purpose, ~5 GB RAM
- **`qwen2.5:7b`** — strong at structured extraction, ~5 GB RAM
- **`phi3.5`** — smaller and faster, ~2 GB RAM

A typical flow: loop over `data/bundles/*.md`, send each to Ollama with an extraction prompt, write results to `data/digests/`.

### Option B — Cheap hosted APIs
- **Groq** — Llama/Qwen at very high speed; generous free tier.
- **DeepSeek API** — extremely cheap, strong quality.
- **Claude Haiku** — Anthropic's small model; cheap and good at extraction.
- **OpenRouter** — single API that routes to many providers.

### Option C — Claude Code
Useful for _one-off_ heavier asks (e.g. "read all bundles from the last month and draft a report"). Overkill for routine extraction.

### Recommended starting point
1. Install Ollama, pull `qwen2.5:7b`.
2. Write a small `make_digests.py` that processes bundles → digests via Ollama.
3. Escalate to hosted API or Claude Code only if the local model falls short.

---

## 11. The `digests/` folder

Currently empty and unreferenced by any script. Reserved for **derived outputs** built on top of bundles — things you'd run periodically and want to keep around. Examples:

- `2026-W25_weekly-rollup.md` — one-paragraph summary of every priority meeting that week.
- `action-items_<person>.md` — running list of commitments involving a specific person.
- `topics_<topic>.md` — every mention of a topic across bundles, with timestamps and back-references.

Each digest script is small: read N bundles, call an LLM with an extraction prompt, write a Markdown file. Bundles are the source of truth; digests are disposable and can be regenerated any time.

---

## 12. Security checklist

- [x] `.env` is in `.gitignore`.
- [x] `data/` is in `.gitignore` — transcripts contain sensitive content.
- [x] `priority_people.txt` is in `.gitignore`; `priority_people.example.txt` is committed as a template.
- [ ] API key has never been pasted into a chat, document, or screenshot.
- [ ] If the key ever leaks, rotate it within minutes.

---

## 13. Version control (git + GitHub)

Repository: **https://github.com/prateekchatterji/fireflies-kb**

### Everyday workflow
```bash
git status
git --no-pager diff <filename>
git add <filename>
git commit -m "type: short summary"
git push
```

### Commit message convention (Conventional Commits)
- `fix:` — bug fixes
- `feat:` — new features
- `docs:` — documentation only
- `refactor:` — internal restructuring, no behaviour change
- `chore:` — housekeeping (config, deps, formatting)

### Undo commands
```bash
git checkout -- <file>               # discard uncommitted changes to a file
git restore <file>                   # same thing, modern syntax
git log --oneline                    # see recent commits
git revert <hash>                    # create a new commit that undoes an old one
```

### The doc-drift habit
**Update `PROJECT_KNOWLEDGE_BASE.md` in the same commit as any code change that affects behaviour or workflow.** Documentation that lags behind code becomes untrustworthy.

---

## 14. Glossary for the Python-curious

- **venv (virtual environment)**: a private folder of Python libraries just for this project.
- **`pip`**: Python's package installer.
- **`requirements.txt`**: a list of libraries this project needs.
- **GraphQL**: the query language Fireflies' API uses.
- **Idempotent**: a script that's safe to run multiple times — running it twice gives the same result as running it once.
- **`.env`**: convention for a file holding secrets, loaded as environment variables and never committed.

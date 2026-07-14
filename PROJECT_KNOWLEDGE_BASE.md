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

> **You're on Windows, using Git Bash.** Two things to remember:
>
> - In Git Bash, `C:\Users\prate\dev\fireflies-kb` is written as `/c/Users/prate/dev/fireflies-kb` (forward slashes, drive letter becomes `/c/`).
> - To activate the Python venv on Windows you use `.venv/Scripts/activate`, **not** `.venv/bin/activate` (that's the Mac/Linux path — most tutorials online show that one).

```
fireflies-kb/                       ← C:\Users\prate\dev\fireflies-kb
├── .env                            ← secret: your Fireflies API key. NEVER commit.
├── .gitignore                      ← tells git to ignore .env, data/, .venv/ etc.
├── priority_people.txt             ← list of emails that mark a meeting as "important"
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

### `priority_people.txt`

A plain text file. One email per line. Lines starting with `#` are comments and ignored. A meeting is "priority" if **any** of its participants matches **any** email here. Case-insensitive.

Current contents:

```
avni@highschoolmoms.com
kanchan@gide.ai
swati@gide.ai
```

Edit this file freely — add or remove emails as priorities change.

### `.env`

A plain text file that holds your secret API key. Format:

```
FIREFLIES_API_KEY=your-key-here
```

Never share, never commit to git. `.gitignore` already excludes it.

If you ever leak this key (e.g. paste it in a chat), regenerate it in Fireflies: **Settings → Developer Settings → regenerate**.

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

Check if it's already there:

```bash
python --version
```

If you see something like `Python 3.10.x` or higher, you're set. Otherwise install from python.org or via Homebrew (`brew install python`).

### 4b. Get the project files into a folder

Put all five files (`fetch_meetings.py`, `bundle_priority_meetings.py`, `priority_people.txt`, `requirements.txt`, `.env`) in a single folder. Open Git Bash and `cd` into it:

```bash
cd /c/Users/prate/dev/fireflies-kb
```

### 4c. Create a virtual environment

A "venv" is a sealed sandbox of Python libraries for this project — keeps it from clashing with anything else on your machine.

```bash
python -m venv .venv
```

This creates a hidden `.venv/` folder. You only do this once.

### 4d. Activate the venv

**Every time you open a new Git Bash window to work on this project, run:**

```bash
source .venv/Scripts/activate
```

Your prompt will get a `(.venv)` prefix. That's how you know it's active.

> ⚠️ On Windows the path is `.venv/Scripts/activate`. On Mac/Linux it would be `.venv/bin/activate`. Easy thing to trip on.

To leave the venv later: `deactivate`.

### 4e. Install dependencies

With the venv active:

```bash
pip install -r requirements.txt
```

This installs `requests` (for HTTP calls) and `python-dotenv` (for reading `.env`).

### 4f. Create `.env`

If you don't have one yet:

```bash
echo "FIREFLIES_API_KEY=paste-your-key-here" > .env
```

Then edit `.env` and replace `paste-your-key-here` with your actual Fireflies API key (from Fireflies → Settings → Developer Settings).

---

## 5. Regular workflow

Every time you want to refresh your Claude Project with new meetings:

```bash
# 1. Open Git Bash and go to the project folder
cd /c/Users/prate/dev/fireflies-kb

# 2. Activate the venv (note: Scripts/ on Windows, not bin/)
source .venv/Scripts/activate

# 3. Sanity check — confirm venv is active and deps are installed
which python                    # should point inside .venv/
pip list | grep -E "requests|dotenv"   # should show both

# 4. Pull new meetings from Fireflies (last 30 days)
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

The whole run usually takes a minute or two, depending on how many new meetings.

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
cat data/bundles/2025-11-15_some-meeting_abc12345.md

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
No. The raw JSONs already contain every meeting from the last 30 days regardless of priority. Just re-run `python bundle_priority_meetings.py` and the new person's meetings will appear in `data/bundles/`.

**"I want meetings older than 30 days."**
Edit `fetch_meetings.py`, find the line `FROM_DATE = TO_DATE - timedelta(days=30)`, change `30` to whatever you need (e.g. `90`). Re-run `fetch_meetings.py`. Note: Fireflies retains transcripts based on your plan; very old ones may not be available.

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
Python isn't installed, or your venv isn't activated. Run `source .venv/bin/activate` first.

**"It says `ModuleNotFoundError: No module named 'requests'`."**
The venv isn't active, or dependencies weren't installed. Run `source .venv/Scripts/activate && pip install -r requirements.txt`.

**"I accidentally committed `.env` to git."**
Rotate the key in Fireflies immediately. Then remove the file from git history (this is non-trivial; ask Claude for help with `git filter-repo` when it happens).

**"Some meetings failed to fetch and I want them retried."**
Normal handling: the watermark cap will retry them on the next run automatically. If you want to force it right away, delete the watermark and run again:

```bash
rm data/.last_fetch
python fetch_meetings.py
```

Existing meetings are still skipped (idempotent), so this only fetches the missing ones.

**"My laptop went to sleep in the middle of a long fetch."**
Two safeguards:

1. Failed meetings will be retried on the next run (see above).
2. To prevent it happening: before a long backfill, plug in the charger and set Windows Settings → System → Power → "when plugged in, PC goes to sleep after" → **Never**. Set it back afterward.

---

## 8. Things to know about the data

- **Participant emails**: matching is by exact email (lowercased). If a colleague joined under an alias or a different address, they'll be missed. Spot-check by opening a raw JSON: `cat data/raw/<some-id>.json | head -50`.
- **Transcript size**: full transcripts can be long. If you upload many bundles to a Claude Project, you may hit the project knowledge size cap. If that happens, consider a stripped-down bundler that omits the `## Transcript` section and keeps only the summary.
- **Recurring meetings**: each occurrence is its own meeting in Fireflies, so a weekly 1:1 becomes one bundle per week. That's intentional.
- **Idempotency**: `fetch_meetings.py` skips meetings already on disk. If a meeting's transcript was updated _after_ you first fetched it (rare), your local copy is stale. To force a refresh of one meeting: `rm data/raw/<id>.json` and re-run.

---

## 9. Reducing Fireflies API calls (implemented)

`fetch_meetings.py` uses an incremental strategy. Two kinds of API call happen per run:

1. **List query** — pages through every meeting in the date window, 25 per page.
2. **Detail query** — one per meeting _that isn't already on disk_. Deduplicated by the `if out_path.exists(): skipped += 1; continue` check.

### How the watermark works

On startup the script checks for `data/.last_fetch`:

- **If it exists**, sets `FROM_DATE = last_fetch - 2 days` (the 2-day overlap catches any meeting whose transcript finalized late).
- **If not**, backfills the last 30 days (first-run behaviour).

At the end of a successful run, the script writes the current time to `data/.last_fetch` as the new watermark. This means a daily run lists only ~3 days of meetings instead of 30 — roughly a **10× reduction** in list calls after the first run.

### Failure handling

If any detail fetch fails during a run (network hiccup, laptop sleep, API blip), the watermark is **not** advanced all the way to now. Instead, it's capped at the earliest failed meeting's date, minus 1 day of safety margin. This guarantees failed meetings fall inside the next run's window and get retried.

Output on a run with failures looks like:

```
Done. fetched=42, skipped(existing)=100, failed=3
Saved watermark to data\.last_fetch (2026-06-25T00:00:00+00:00)
  (capped at earliest failure so 3 failed meeting(s) get retried)
```

### Manual controls

- **Force a full 30-day backfill**: `rm data/.last_fetch && python fetch_meetings.py`.
- **Adjust the safety overlap**: edit `OVERLAP_DAYS = 2` at the top of the script.
- **Adjust first-run window**: edit `BACKFILL_DAYS = 30`.

### Other levers (not implemented — for future consideration)

- **Slow down further**: increase `time.sleep(0.5)` between detail fetches to be even gentler on rate limits.
- **Cap per run**: add `if fetched >= 50: break` inside the loop to stop after N new meetings — useful if a backfill is huge.
- **Pre-filter by participants**: the list query already returns `participants`, so you could skip the detail call for non-priority meetings. Saves the most expensive calls. Trade-off: you lose the option to re-bundle later for a new priority person without re-fetching.

---

## 10. Working with bundles — local & low-cost options

You don't need a frontier model to do useful things with these meeting bundles. The transcripts are bounded, the questions are usually narrow (find a commitment, summarize a thread, list action items for X), and small local models handle that well.

### Option A — Ollama (fully local, free)

[Ollama](https://ollama.com) is the easiest way to run an LLM on your own machine. Windows installer, runs as a background service, exposes a local API on `localhost:11434`.

Recommended starter models (all free, all run on consumer hardware):

- **`llama3.1:8b`** — good general-purpose model, ~5 GB RAM
- **`qwen2.5:7b`** — strong at structured extraction (action items, summaries)
- **`phi3.5`** — smaller and faster, ~2 GB RAM, surprisingly capable

A typical flow: write a small Python script that loops over `data/bundles/*.md`, sends each to Ollama with a prompt like _"extract action items assigned to Avni"_, and writes results to `data/digests/`.

This is exactly what the `digests/` folder is reserved for — see §11.

### Option B — Cheap hosted APIs (when local is too slow)

If a local model is too slow or quality isn't enough, these are dramatically cheaper than Claude Opus/Sonnet while still being useful:

- **Groq** — runs Llama and Qwen models at very high speed; generous free tier.
- **DeepSeek API** — extremely cheap (cents per million tokens), strong quality.
- **Claude Haiku** — Anthropic's own small model; cheap and good at extraction tasks.
- **OpenRouter** — single API that routes to many providers; lets you A/B models easily.

### Option C — Claude Code (what you already have)

Since you mentioned you can run Claude Code: it's overkill for routine extraction over bundles (and the cost adds up), but it's useful for _one-off_ heavier asks — e.g. "read all bundles from the last month and draft a board update." Use it sparingly for high-leverage work, not for routine digesting.

### Recommended starting point

1. Install Ollama, pull `qwen2.5:7b`.
2. Write a small `make_digests.py` that processes bundles → digests using Ollama.
3. Only escalate to a hosted API or Claude Code if the local model falls short on specific tasks.

---

## 11. The `digests/` folder

Currently empty and unreferenced by any script. It's reserved for **derived outputs** built on top of bundles — things you'd run periodically and want to keep around. Examples:

- `2026-W25_weekly-rollup.md` — one-paragraph summary of every priority meeting that week.
- `action-items_avni.md` — running list of commitments involving Avni, extracted from all her meetings.
- `topics_admissions.md` — every mention of "admissions" across bundles, with timestamps and links back to source bundle files.

These are the natural next scripts to write. Each digest script is small: read N bundles, call an LLM with an extraction prompt, write a Markdown file. The bundles are the source of truth; digests are disposable and can be regenerated any time.

---

## 12. Security checklist

- [ ] `.env` is in `.gitignore` (it is — verified).
- [ ] `data/` is in `.gitignore` (it is — meetings can contain sensitive content).
- [ ] API key has never been pasted into a chat, document, or screenshot.
- [ ] If the key ever leaks, rotate it within minutes.

---

## 13. Version control (git + GitHub)

This project is tracked in git and hosted on GitHub as a **private** repository:
**https://github.com/prateekchatterji/fireflies-kb**

### Why private matters

The repo intentionally excludes `.env` (API key) and `data/` (meeting content) via `.gitignore`. But `priority_people.txt` contains colleagues' email addresses, and code comments may reference clients or internal context. Keep the repo private.

### Everyday workflow

```bash
# See what you've changed
git status
git --no-pager diff <filename>       # skip the pager for short diffs

# Stage and commit
git add <filename>                   # or: git add . for everything
git commit -m "type: short summary"

# Push to GitHub
git push
```

### Commit message convention

Use short, imperative type-prefixed messages (Conventional Commits):

- `fix:` — bug fixes (e.g. `fix: hold watermark at earliest failure`)
- `feat:` — new features (e.g. `feat: add metadata export utility`)
- `docs:` — documentation only (e.g. `docs: document watermark behaviour`)
- `refactor:` — internal restructuring, no behaviour change
- `chore:` — housekeeping (config, deps, formatting)

Long-form multi-line commits are welcome when the _why_ isn't obvious from the diff.

### Undo commands you'll actually need

```bash
git checkout -- <file>               # discard uncommitted changes to a file
git restore <file>                   # same thing, modern syntax
git log --oneline                    # see recent commits
git revert <hash>                    # create a new commit that undoes an old one
```

### The doc-drift habit

**Update `PROJECT_KNOWLEDGE_BASE.md` in the same commit as any code change that affects behaviour or workflow.** Documentation that lags behind code becomes untrustworthy. If you catch yourself thinking "I'll update the doc later," add it to the same commit now instead.

Suggested split:

- Code-only change → one commit, `fix:` or `feat:`.
- Code + doc update → two separate commits pushed together: one `feat:`/`fix:`, one `docs:`.
- Doc-only update → one `docs:` commit.

---

## 14. Glossary for the Python-curious

- **venv (virtual environment)**: a private folder of Python libraries just for this project, so it doesn't conflict with other projects or with system Python.
- **`pip`**: Python's package installer. `pip install X` adds library X to the active venv.
- **`requirements.txt`**: a list of libraries this project needs, so anyone (including future-you) can recreate the venv with one command.
- **GraphQL**: the query language Fireflies' API uses. You don't need to learn it — the queries are already written in `fetch_meetings.py`.
- **Idempotent**: a script that's safe to run multiple times — running it twice gives the same result as running it once.
- **`.env`**: convention for a file holding secrets (API keys, passwords) that gets loaded as environment variables and is never committed to source control.

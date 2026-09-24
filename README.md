# fireflies-kb

A personal pipeline that pulls meeting transcripts from [Fireflies.ai](https://fireflies.ai) and turns the ones involving key people into clean Markdown bundles for use as knowledge in a [Claude Project](https://www.anthropic.com/news/projects).

```
Fireflies API  →  data/raw/*.json  →  data/bundles/*.md  →  Claude Project
   (cloud)         (fetch_meetings)   (bundle_priority...)    (manual upload)
```

Two small Python scripts, no server, no database. Runs locally on Windows via Git Bash.

## Why this exists

Fireflies stores every meeting you record, but searching across many meetings inside its UI is awkward, and you can't easily ask an LLM to reason across them. This project extracts, filters and reformats the meetings you care about so a Claude Project can answer questions across them.

## Quick start

Assumes Python 3.10+ and a Fireflies account with API access.

```bash
git clone https://github.com/prateekchatterji/fireflies-kb.git
cd fireflies-kb
python -m venv .venv
source .venv/Scripts/activate       # on Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
echo "FIREFLIES_API_KEY=your-key-here" > .env    # then edit with real key
python fetch_meetings.py
python bundle_priority_meetings.py
```

Bundles land in `data/bundles/`. Drag them into a Claude Project as knowledge.

For everyday use, common workflows and troubleshooting, see the two docs below.

## Documentation

- **[PROJECT_KNOWLEDGE_BASE.md](PROJECT_KNOWLEDGE_BASE.md)** — how the project works, one-time setup, data model, security, git workflow. Read this once.
- **[EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)** — copy-pasteable command sequences for every workflow (daily refresh, backfill, retry, reset, etc.). Consult as needed.

## What's in the repo

| File | Purpose |
|---|---|
| `fetch_meetings.py` | Pulls meetings from Fireflies (incremental, failure-aware). |
| `bundle_priority_meetings.py` | Filters by priority people and renders as Markdown. |
| `priority_people.txt` | Emails that mark a meeting as "important." |
| `requirements.txt` | Python dependencies (`requests`, `python-dotenv`). |
| `.gitignore` | Excludes `.env`, `data/`, `.venv/` from git. |

Not in the repo (excluded by `.gitignore`):
- `.env` — holds the Fireflies API key. Never committed.
- `data/` — all fetched meeting content. Never committed.
- `.venv/` — the Python virtual environment.

## Status

Working personal pipeline. Extensions on the roadmap:

- Ledger utility — sortable/filterable index of the meeting corpus.
- Local LLM digests via Ollama — cross-meeting summaries, per-person action items.
- CLI unification — collapse the utilities under a single `cli.py` with subcommands.

## License

Private personal project. No license granted for reuse.

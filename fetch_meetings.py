"""
Pulls Fireflies meetings and saves each as a JSON file in data/raw/.

Incremental: remembers the last successful run timestamp in data/.last_fetch
and only asks Fireflies for meetings since then (minus a 2-day safety overlap).
On the first run (no state file), backfills the last 30 days.

To force a full 30-day backfill, delete data/.last_fetch and re-run.

Idempotent: skips meetings whose JSON is already on disk.
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FIREFLIES_API_KEY")
if not API_KEY:
    raise SystemExit("Missing FIREFLIES_API_KEY in .env")

API_URL = "https://api.fireflies.ai/graphql"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = Path("data/.last_fetch")
OVERLAP_DAYS = 2          # re-scan this many days before last_fetch, in case
                          # a recent meeting's transcript finalised late
BACKFILL_DAYS = 30        # used only when STATE_FILE doesn't exist

# --- Date window ---------------------------------------------------------
TO_DATE = datetime.now(timezone.utc)

if STATE_FILE.exists():
    try:
        last = datetime.fromisoformat(STATE_FILE.read_text().strip())
        FROM_DATE = last - timedelta(days=OVERLAP_DAYS)
        MODE = f"incremental (since {last.date()}, with {OVERLAP_DAYS}-day overlap)"
    except Exception as e:
        print(f"  warning: could not read {STATE_FILE} ({e}); doing full backfill")
        FROM_DATE = TO_DATE - timedelta(days=BACKFILL_DAYS)
        MODE = f"backfill (last {BACKFILL_DAYS} days)"
else:
    FROM_DATE = TO_DATE - timedelta(days=BACKFILL_DAYS)
    MODE = f"first run / backfill (last {BACKFILL_DAYS} days)"

# --- GraphQL queries -----------------------------------------------------
LIST_QUERY = """
query Transcripts($fromDate: DateTime, $toDate: DateTime, $limit: Int, $skip: Int) {
  transcripts(fromDate: $fromDate, toDate: $toDate, limit: $limit, skip: $skip) {
    id
    title
    date
    duration
    participants
  }
}
"""

DETAIL_QUERY = """
query Transcript($id: String!) {
  transcript(id: $id) {
    id
    title
    date
    duration
    participants
    organizer_email
    host_email
    summary {
      overview
      action_items
      keywords
      short_summary
      bullet_gist
      gist
    }
    sentences {
      index
      speaker_name
      speaker_id
      text
      start_time
      end_time
    }
  }
}
"""

def parse_meeting_date(m: dict) -> datetime:
    """Parse a meeting's date field (epoch ms or ISO string) to a UTC datetime."""
    d = m.get("date")
    if isinstance(d, (int, float)):
        return datetime.fromtimestamp(d / 1000, tz=timezone.utc)
    return datetime.fromisoformat(str(d).replace("Z", "+00:00"))

def gql(query: str, variables: dict) -> dict:
    r = requests.post(API_URL, headers=HEADERS,
                      json={"query": query, "variables": variables}, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def list_meetings() -> list[dict]:
    """Page through transcripts in the date window."""
    all_items, skip, limit = [], 0, 25
    while True:
        page = gql(LIST_QUERY, {
            "fromDate": FROM_DATE.isoformat(),
            "toDate": TO_DATE.isoformat(),
            "limit": limit,
            "skip": skip,
        })["transcripts"]
        if not page:
            break
        all_items.extend(page)
        print(f"  ...listed {len(all_items)} so far")
        if len(page) < limit:
            break
        skip += limit
        time.sleep(0.3)  # be polite
    return all_items


def fetch_detail(meeting_id: str) -> dict:
    return gql(DETAIL_QUERY, {"id": meeting_id})["transcript"]


def main():
    print(f"Mode: {MODE}")
    print(f"Fetching meetings from {FROM_DATE.date()} to {TO_DATE.date()}...")
    meetings = list_meetings()
    print(f"Found {len(meetings)} meetings in the window.\n")

    fetched, skipped, failed = 0, 0, 0
    failed_dates = []                              # NEW
    for m in meetings:
        out_path = RAW_DIR / f"{m['id']}.json"
        if out_path.exists():
            skipped += 1
            continue
        try:
            detail = fetch_detail(m["id"])
            out_path.write_text(json.dumps(detail, indent=2, ensure_ascii=False),
                                encoding="utf-8")
            fetched += 1
            print(f"  saved: {m.get('title', m['id'])[:60]}")
            time.sleep(0.5)
        except Exception as e:
            failed += 1
            # Track when this failed meeting occurred, so we can hold the
            # watermark back and retry it next run.
            try:                                                # NEW
                failed_dates.append(parse_meeting_date(m))      # NEW
            except Exception:                                   # NEW
                pass                                            # NEW
            print(f"  FAILED {m['id']}: {e}")

    print(f"\nDone. fetched={fetched}, skipped(existing)={skipped}, failed={failed}")

    # Advance the watermark only up to the earliest failure. If any meeting
    # failed, we cap the watermark at that meeting's date so the next run
    # re-lists it. If nothing failed, we advance fully to TO_DATE.
    if failed_dates:
        earliest_failure = min(failed_dates)
        # Save watermark 1 day before earliest failure, for safety margin
        new_watermark = earliest_failure - timedelta(days=1)
        STATE_FILE.write_text(new_watermark.isoformat())
        print(f"Saved watermark to {STATE_FILE} ({new_watermark.isoformat()})")
        print(f"  (capped at earliest failure so {failed} failed meeting(s) get retried)")
    else:
        STATE_FILE.write_text(TO_DATE.isoformat())
        print(f"Saved watermark to {STATE_FILE} ({TO_DATE.isoformat()})")

if __name__ == "__main__":
    main()

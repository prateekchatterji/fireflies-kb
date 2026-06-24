"""
Pulls the last 30 days of Fireflies meetings and saves each as a JSON file
in data/raw/. Idempotent: skips meetings already on disk.
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

# Date range: last 30 days
TO_DATE = datetime.now(timezone.utc)
FROM_DATE = TO_DATE - timedelta(days=30)

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
    print(f"Fetching meetings from {FROM_DATE.date()} to {TO_DATE.date()}...")
    meetings = list_meetings()
    print(f"Found {len(meetings)} meetings in the window.\n")

    fetched, skipped, failed = 0, 0, 0
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
            print(f"  FAILED {m['id']}: {e}")

    print(f"\nDone. fetched={fetched}, skipped(existing)={skipped}, failed={failed}")


if __name__ == "__main__":
    main()
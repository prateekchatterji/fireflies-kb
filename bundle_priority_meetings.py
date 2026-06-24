"""
Reads data/raw/*.json, filters to meetings involving priority_people.txt,
and writes one human-readable .md file per meeting into data/bundles/.
Sorted newest first. Designed for copy-paste into a Claude Project.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/bundles")
OUT_DIR.mkdir(parents=True, exist_ok=True)
PRIORITY_FILE = Path("priority_people.txt")

def load_priority() -> set[str]:
    if not PRIORITY_FILE.exists():
        raise SystemExit("Missing priority_people.txt")
    return {
        line.strip().lower()
        for line in PRIORITY_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

def fmt_ts(seconds):
    if seconds is None:
        return "??:??"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"

def participants_set(meeting) -> set[str]:
    p = meeting.get("participants") or []
    # participants is sometimes a list of emails, sometimes objects
    out = set()
    for item in p:
        if isinstance(item, str):
            out.add(item.lower())
        elif isinstance(item, dict):
            email = item.get("email") or item.get("name") or ""
            if email:
                out.add(email.lower())
    return out

def parse_date(d):
    if d is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    # Fireflies returns epoch ms or ISO string depending on field
    try:
        if isinstance(d, (int, float)):
            return datetime.fromtimestamp(d / 1000, tz=timezone.utc)
        return datetime.fromisoformat(str(d).replace("Z", "+00:00"))
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)

def render(meeting) -> str:
    title = meeting.get("title", "Untitled")
    date = parse_date(meeting.get("date"))
    duration = meeting.get("duration", "?")
    participants = ", ".join(sorted(participants_set(meeting))) or "(none)"
    summary = meeting.get("summary") or {}

    lines = [
        f"# {title}",
        f"**Date:** {date.strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Duration:** {duration} min",
        f"**Participants:** {participants}",
        "",
        "## Fireflies summary",
        (summary.get("overview") or summary.get("short_summary") or "(none)"),
        "",
        "## Action items",
        (summary.get("action_items") or "(none)"),
        "",
        "## Keywords",
        ", ".join(summary.get("keywords") or []) or "(none)",
        "",
        "## Transcript",
    ]
    for s in meeting.get("sentences") or []:
        speaker = s.get("speaker_name", "?")
        text = (s.get("text") or "").strip()
        ts = fmt_ts(s.get("start_time"))
        if text:
            lines.append(f"[{ts}] {speaker}: {text}")
    return "\n".join(lines)

def main():
    priority = load_priority()
    print(f"Priority people: {priority}")

    matched = []
    for f in RAW_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  skip {f.name}: {e}")
            continue
        parts = participants_set(data)
        if parts & priority:
            matched.append((parse_date(data.get("date")), f, data))

    matched.sort(key=lambda x: x[0], reverse=True)  # newest first
    print(f"Matched {len(matched)} meetings.\n")

    for i, (date, src, data) in enumerate(matched, 1):
        safe_title = "".join(c if c.isalnum() or c in "-_ " else "_"
                             for c in (data.get("title") or "untitled"))[:60].strip()
        out_name = f"{date.strftime('%Y-%m-%d')}_{safe_title}_{src.stem[:8]}.md"
        (OUT_DIR / out_name).write_text(render(data), encoding="utf-8")
        print(f"  [{i:3d}] {out_name}")

    print(f"\nWrote {len(matched)} bundles to {OUT_DIR}/")

if __name__ == "__main__":
    main()
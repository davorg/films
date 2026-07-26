#!/usr/bin/env python3
"""
Multi-user version of the update script.

This script processes multiple user watchlists from the 'watchlists/' directory
and generates separate outputs for each user under 'site/<username>/'.

Usage:
    TMDB_API_KEY="..." python3 examples/multi_user_update.py
"""
import os
import sys
import json
import urllib.request
import urllib.parse
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHLISTS_DIR = ROOT / "watchlists"
OUT_DIR = ROOT / "site"

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "").strip()

TMDB_API = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_RELEASE_TYPE_THEATRICAL = 3

def http_get_json(url: str) -> dict:
  req = urllib.request.Request(url, headers={"Accept": "application/json"})
  with urllib.request.urlopen(req, timeout=30) as resp:
    raw = resp.read().decode("utf-8")
  return json.loads(raw)

def tmdb_url(path: str, params: dict) -> str:
  return f"{TMDB_API}{path}?{urllib.parse.urlencode({**params, 'api_key': TMDB_API_KEY})}"

def parse_iso_date(s: str) -> datetime.date:
  return datetime.date.fromisoformat(s[:10])

def choose_gb_theatrical_date(release_dates_payload: dict, today: datetime.date):
  gb = None
  for r in release_dates_payload.get("results", []):
    if r.get("iso_3166_1") == "GB":
      gb = r
      break
  if not gb:
    return None, None

  theatrical = []
  for rd in gb.get("release_dates", []):
    if rd.get("type") == TMDB_RELEASE_TYPE_THEATRICAL and rd.get("release_date"):
      try:
        d = parse_iso_date(rd["release_date"])
        theatrical.append(d)
      except (ValueError, KeyError) as e:
        print(f"Warning: Could not parse release date '{rd.get('release_date')}': {e}", file=sys.stderr)

  if not theatrical:
    return None, None

  theatrical.sort()
  future = [d for d in theatrical if d >= today]
  if future:
    return future[0].isoformat(), "upcoming"
  else:
    return theatrical[0].isoformat(), "released"

def get_utc_timestamp() -> str:
  return (
    datetime.datetime
    .now(datetime.UTC)
    .replace(microsecond=0)
    .strftime("%Y%m%dT%H%M%SZ")
  )

def build_ics_events(movies, dtstamp_utc: str, username: str) -> str:
  lines = []
  lines.append("BEGIN:VCALENDAR")
  lines.append("VERSION:2.0")
  lines.append(f"PRODID:-//Film Release Tracker//{username}//EN")
  lines.append("CALSCALE:GREGORIAN")
  lines.append("METHOD:PUBLISH")
  lines.append(f"X-WR-CALNAME:{username}'s Film Releases")
  lines.append(f"X-WR-CALDESC:UK theatrical releases tracked by {username}")

  for m in movies:
    y, mo, d = map(int, m["release_date"].split("-"))
    start = datetime.date(y, mo, d)
    end = start + datetime.timedelta(days=1)

    uid = f"tmdb-{m['tmdb_id']}-{username}@film-release-tracker"
    summary = f"{m['title']} (UK theatrical release)"
    desc = f"TMDb: {m['tmdb_url']}"

    def yyyymmdd(dt: datetime.date) -> str:
      return f"{dt.year:04d}{dt.month:02d}{dt.day:02d}"

    def ics_escape(s: str) -> str:
      return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

    lines.append("BEGIN:VEVENT")
    lines.append(f"UID:{ics_escape(uid)}")
    lines.append(f"DTSTAMP:{dtstamp_utc}")
    lines.append(f"DTSTART;VALUE=DATE:{yyyymmdd(start)}")
    lines.append(f"DTEND;VALUE=DATE:{yyyymmdd(end)}")
    lines.append(f"SUMMARY:{ics_escape(summary)}")
    lines.append(f"DESCRIPTION:{ics_escape(desc)}")
    lines.append("STATUS:CONFIRMED")
    lines.append("TRANSP:TRANSPARENT")
    lines.append("END:VEVENT")

  lines.append("END:VCALENDAR")
  return "\n".join(lines) + "\n"

def process_user_watchlist(watchlist_path: Path, username: str, today: datetime.date, dtstamp_utc: str):
  """Process a single user's watchlist and generate outputs."""
  print(f"\nProcessing watchlist for user: {username}")
  
  if not watchlist_path.exists():
    print(f"Warning: Watchlist not found: {watchlist_path}", file=sys.stderr)
    return

  watch = json.loads(watchlist_path.read_text(encoding="utf-8"))
  if not isinstance(watch, list):
    print(f"Warning: {watchlist_path} must be a JSON array", file=sys.stderr)
    return

  upcoming = []
  released = []
  tbd = []

  for item in watch:
    tmdb_id = item.get("tmdb_id")
    if not tmdb_id:
      continue

    try:
      details = http_get_json(tmdb_url(f"/movie/{tmdb_id}", {"language": "en-GB"}))
      releases = http_get_json(tmdb_url(f"/movie/{tmdb_id}/release_dates", {}))

      if not isinstance(details, dict):
        print(f"Warning: Invalid details response for TMDb ID {tmdb_id}", file=sys.stderr)
        continue
      if not isinstance(releases, dict) or "results" not in releases:
        print(f"Warning: Invalid releases response for TMDb ID {tmdb_id}", file=sys.stderr)
        continue

      chosen_date, bucket = choose_gb_theatrical_date(releases, today)

      movie = {
        "tmdb_id": tmdb_id,
        "title": details.get("title") or details.get("original_title") or item.get("title_hint") or f"TMDb {tmdb_id}",
        "release_date": chosen_date,
        "poster_url": (IMG_BASE + details["poster_path"]) if details.get("poster_path") else None,
        "tmdb_url": f"https://www.themoviedb.org/movie/{tmdb_id}",
      }

      if bucket == "upcoming":
        upcoming.append(movie)
      elif bucket == "released":
        released.append(movie)
      else:
        movie["release_date"] = None
        tbd.append(movie)
    except Exception as e:
      print(f"Error processing TMDb ID {tmdb_id}: {e}", file=sys.stderr)
      continue

  # Sort buckets
  upcoming.sort(key=lambda m: m["release_date"])
  released.sort(key=lambda m: m["release_date"], reverse=True)
  tbd.sort(key=lambda m: m["title"].lower())

  # Create user output directory
  user_out_dir = OUT_DIR / username
  user_out_dir.mkdir(parents=True, exist_ok=True)

  # Write JSON
  out_json = user_out_dir / "releases.json"
  out = {
    "username": username,
    "generated_at": (
      datetime.datetime
      .now(datetime.UTC)
      .replace(microsecond=0)
      .isoformat()
    ),
    "upcoming": upcoming,
    "tbd": tbd,
    "released": released,
  }
  out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

  # Write ICS
  out_ics = user_out_dir / "releases.ics"
  out_ics.write_text(build_ics_events(upcoming, dtstamp_utc, username), encoding="utf-8")

  print(f"  ✓ Wrote {out_json}")
  print(f"  ✓ Wrote {out_ics}")
  print(f"  Stats: {len(upcoming)} upcoming, {len(tbd)} TBD, {len(released)} released")

def generate_index_page(output_dir: Path, users: list):
  """Generate a landing page that lists all users."""
  html = f"""<!doctype html>
<html lang="en-GB">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Film Release Tracker - Users</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header class="header">
      <div class="container">
        <h1>Film Release Tracker</h1>
        <p class="subtitle">Multi-user film tracking • UK theatrical releases</p>
      </div>
    </header>

    <main class="container">
      <section>
        <h2>Available Users</h2>
        <p>Select a user to view their tracked film releases:</p>
        <ul style="list-style: none; padding: 0;">
"""
  
  for user in sorted(users):
    html += f"""          <li style="margin: 1rem 0;">
            <a href="{user}/" style="font-size: 1.2rem; text-decoration: none; color: #0066cc;">
              📽️ {user}
            </a>
            <span style="margin-left: 1rem;">
              (<a href="{user}/releases.ics" style="font-size: 0.9rem;">ICS</a>)
            </span>
          </li>
"""
  
  html += """        </ul>
      </section>
    </main>

    <footer class="footer">
      <div class="container">
        <p>Powered by <a href="https://www.themoviedb.org/" target="_blank">TMDb</a></p>
      </div>
    </footer>
  </body>
</html>
"""
  
  index_path = output_dir / "index.html"
  index_path.write_text(html, encoding="utf-8")
  print(f"\n✓ Wrote user directory: {index_path}")

def main():
  if not TMDB_API_KEY:
    raise SystemExit("TMDB_API_KEY is not set. Add it as an env var (or GitHub Actions secret).")

  if not WATCHLISTS_DIR.exists():
    print(f"Creating watchlists directory: {WATCHLISTS_DIR}")
    WATCHLISTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Migrate old watchlist.json if it exists
    old_watchlist = ROOT / "watchlist.json"
    if old_watchlist.exists():
      print(f"Migrating {old_watchlist} to watchlists/default.json")
      default_watchlist = WATCHLISTS_DIR / "default.json"
      default_watchlist.write_text(old_watchlist.read_text(encoding="utf-8"))

  watchlist_files = list(WATCHLISTS_DIR.glob("*.json"))
  if not watchlist_files:
    raise SystemExit(f"No watchlist files found in {WATCHLISTS_DIR}/")

  today = datetime.date.today()
  dtstamp_utc = get_utc_timestamp()
  users = []

  print(f"Found {len(watchlist_files)} watchlist(s)")

  for watchlist_file in watchlist_files:
    username = watchlist_file.stem
    users.append(username)
    process_user_watchlist(watchlist_file, username, today, dtstamp_utc)

  # Generate index page
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  generate_index_page(OUT_DIR, users)

  print(f"\n✅ All done! Processed {len(users)} user(s)")

if __name__ == "__main__":
  main()

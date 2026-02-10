# Film Releases Tracker (UK theatrical + ICS)

This repo builds a small static website and an `.ics` calendar feed for **UK theatrical release dates** for films you care about.

**Your rules (implemented):**
- Only **GB (UK) theatrical** releases (TMDb release type `3 = Theatrical`). citeturn0search2turn0search3turn2search2
- Calendar events are **all-day**.
- Films with no UK theatrical date are shown under **TBD** and are **omitted** from the `.ics`.

## What you get

After the workflow runs, GitHub Pages will host:
- `index.html` – upcoming films (sorted by date), then TBD, then already-released.
- `releases.ics` – subscribe in Google Calendar (only upcoming films).

## Quick start

1) Create a TMDb API key and add it as a GitHub Actions secret named:

- `TMDB_API_KEY`

2) Edit `watchlist.json` and replace the example IDs with real TMDb movie IDs:

```json
[
  { "tmdb_id": 603, "title_hint": "The Matrix" },
  { "tmdb_id": 872585, "title_hint": "Oppenheimer" }
]
```

Only `tmdb_id` is required; `title_hint` is just there to keep the file readable.

3) Enable GitHub Pages:
- Repo **Settings → Pages**
- Source: **GitHub Actions**

4) Trigger the workflow:
- Push a commit, or
- Actions → “Build & Deploy” → Run workflow

## Subscribe to the calendar in Google Calendar

Once deployed, your ICS feed will be at:

- `https://<your-user>.github.io/<your-repo>/releases.ics`

In Google Calendar:
- “Other calendars” → “+” → “From URL”
- Paste the URL above.

Note: Google Calendar re-fetches subscribed calendars on its own schedule and updates may not appear instantly. citeturn0search11

## Local run (optional)

You can generate the outputs locally:

```bash
TMDB_API_KEY="..." python3 bin/update
```

Outputs are written to `site/`:
- `site/releases.json`
- `site/releases.ics`

## How dates are chosen

For each TMDb movie:
- Fetch `/movie/{id}/release_dates`
- Find `GB`
- Pick entries where `type == 3` (Theatrical) citeturn2search2
- Choose the earliest theatrical date that is **today or later** for “Upcoming”.
- If only past theatrical dates exist, the film appears under “Already released”.
- If no GB theatrical date exists at all, it appears under “TBD” (and is not in the ICS).

## Files

- `watchlist.json` – your list (edit this)
- `bin/update` – fetches TMDb and regenerates `site/releases.json` + `site/releases.ics`
- `site/` – static site assets
- `.github/workflows/deploy.yml` – scheduled build + Pages deploy

## Licence

MIT. See `LICENSE`.

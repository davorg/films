# Copilot Instructions for Film Releases Tracker

## Repository Overview

This repository builds a static website and ICS calendar feed for tracking UK theatrical release dates of films using The Movie Database (TMDb) API.

**Key Features:**
- Fetches UK theatrical release dates (TMDb release type 3 = Theatrical)
- Generates a static HTML page with upcoming, TBD, and already-released films
- Creates an ICS calendar feed for subscription in Google Calendar
- Deploys automatically to GitHub Pages via GitHub Actions

## Technology Stack

- **Language:** Python 3.13
- **APIs:** TMDb API v3
- **Deployment:** GitHub Actions + GitHub Pages
- **Output Formats:** JSON, ICS (iCalendar), HTML

## Project Structure

```
.
├── bin/
│   └── update              # Main Python script to fetch data and generate outputs
├── site/                   # Static site files (HTML, CSS, generated JSON/ICS)
│   ├── index.html
│   ├── releases.json       # Generated: film release data
│   └── releases.ics        # Generated: iCalendar feed
├── watchlist.json          # User-maintained list of TMDb movie IDs to track
├── .github/
│   └── workflows/
│       └── deploy.yml      # CI/CD pipeline for daily updates
└── README.md
```

## Key Files

### `bin/update`
- **Purpose:** Fetches release dates from TMDb and generates output files
- **Input:** `watchlist.json`, `TMDB_API_KEY` environment variable
- **Output:** `site/releases.json` and `site/releases.ics`
- **Language:** Python 3 using only standard library (no external dependencies)

### `watchlist.json`
- **Purpose:** User-maintained list of films to track
- **Format:** Array of objects with `tmdb_id` (required) and `title_hint` (optional)
- **Example:**
  ```json
  [
    { "tmdb_id": 603, "title_hint": "The Matrix" }
  ]
  ```

### `.github/workflows/deploy.yml`
- **Triggers:** Push to main, manual dispatch, daily cron schedule (03:17 UTC)
- **Steps:** Checkout, setup Python 3.13, run `bin/update`, upload and deploy to Pages

## Development Guidelines

### Code Style
- Use Python 3.13+ features where appropriate
- Follow PEP 8 style guidelines
- Keep dependencies minimal (prefer standard library)
- Use type hints where they improve clarity

### Date Handling
- UK theatrical releases only (`iso_3166_1 == "GB"`, `type == 3`)
- Select the **earliest** upcoming theatrical date that is today or later
- If only past dates exist, mark as "Already released"
- If no GB theatrical date exists, mark as "TBD" (excluded from ICS)

### API Usage
- TMDb API base: `https://api.themoviedb.org/3`
- Key endpoints: `/movie/{id}`, `/movie/{id}/release_dates`
- Always include `api_key` parameter in requests
- Handle timeouts and errors gracefully

### Output Formats
- **releases.json:** Full structured data for all films
- **releases.ics:** Standard iCalendar format (RFC 5545)
  - Only include upcoming films with confirmed UK dates
  - Use all-day events
  - Include SUMMARY, DTSTART, DESCRIPTION, UID

### Testing Locally
Run the update script with your API key:
```bash
TMDB_API_KEY="your-key-here" python3 bin/update
```

Verify outputs in `site/` directory:
- Check `releases.json` structure
- Validate `releases.ics` can be imported to calendar apps

### GitHub Actions
- Runs daily to check for updated release dates
- Uses secret `TMDB_API_KEY` for API authentication
- Deploys generated site to GitHub Pages automatically

## Common Tasks

### Adding a Film
1. Find TMDb movie ID (from TMDb website URL)
2. Add entry to `watchlist.json`:
   ```json
   { "tmdb_id": 12345, "title_hint": "Film Title" }
   ```
3. Push to main branch to trigger update

### Debugging Release Dates
- Check TMDb's `/movie/{id}/release_dates` endpoint directly
- Verify `GB` region exists in response
- Look for `type: 3` (Theatrical) entries
- Date format: ISO 8601 with timezone (e.g., "2026-04-17T00:00:00.000Z")

### Modifying Date Logic
- Main function: `choose_gb_theatrical_date()` in `bin/update`
- Returns tuple: `(selected_date, all_dates_list)`
- Consider both future and past dates for proper categorization

## Best Practices

1. **Minimal Dependencies:** Keep the project dependency-free where possible
2. **Error Handling:** Handle missing/invalid TMDb data gracefully
3. **Data Validation:** Validate JSON structure before processing
4. **Idempotency:** Script should produce same output given same inputs
5. **Documentation:** Update README.md when changing user-facing behavior
6. **API Rate Limits:** Be mindful of TMDb API rate limits in bulk operations

## Troubleshooting

### Script Fails
- Verify `TMDB_API_KEY` is set correctly
- Check TMDb API status
- Validate `watchlist.json` format

### Missing Release Dates
- TMDb may not have UK theatrical dates for all films
- These films appear under "TBD" and are excluded from ICS

### Calendar Not Updating
- Google Calendar caches subscribed calendars
- Updates may take several hours to appear
- Verify ICS file is valid (check with validators online)

## Security Notes

- Never commit `TMDB_API_KEY` to the repository
- Use GitHub Actions secrets for sensitive data
- Only use HTTPS for API requests
- Validate and sanitize any user inputs if extending functionality

# Multi-User Implementation Example

This directory contains a proof-of-concept implementation of **Approach 2** from the [MULTI_USER_GUIDE.md](../MULTI_USER_GUIDE.md) - supporting multiple users with separate watchlists.

## What's Here

### `multi_user_update.py`

A modified version of `bin/update` that:
- Processes multiple watchlists from a `watchlists/` directory
- Generates separate outputs for each user under `site/<username>/`
- Creates a landing page listing all users
- Adds user-specific calendar names to ICS files

## How to Test It

### 1. Create test watchlists

```bash
# Create watchlists directory
mkdir -p watchlists

# Create sample watchlists for different users
cat > watchlists/alice.json << 'EOF'
[
  { "tmdb_id": 603, "title_hint": "The Matrix" },
  { "tmdb_id": 872585, "title_hint": "Oppenheimer" }
]
EOF

cat > watchlists/bob.json << 'EOF'
[
  { "tmdb_id": 1003596, "title_hint": "Avengers: Doomsday" },
  { "tmdb_id": 1170608, "title_hint": "Dune: Part Three" }
]
EOF
```

### 2. Run the multi-user script

```bash
TMDB_API_KEY="your-tmdb-api-key-here" python3 examples/multi_user_update.py
```

### 3. Check the outputs

```bash
# View directory structure
tree site/

# Expected structure:
# site/
# ├── index.html (user directory)
# ├── alice/
# │   ├── releases.json
# │   └── releases.ics
# └── bob/
#     ├── releases.json
#     └── releases.ics
```

### 4. View the results

Open `site/index.html` in a browser to see the user directory, or open individual user pages.

Each user's ICS calendar includes their username in the calendar name (e.g., "Alice's Film Releases").

## Key Differences from Original Script

| Feature | Original `bin/update` | Multi-user version |
|---------|----------------------|-------------------|
| Watchlist location | Single `watchlist.json` | Multiple files in `watchlists/*.json` |
| Output location | `site/` root | `site/<username>/` subdirectories |
| ICS calendar name | Generic | User-specific |
| Landing page | Single user page | User directory |
| Migration support | N/A | Auto-migrates old `watchlist.json` |

## Migration Notes

If you want to adopt this approach for your repository:

1. **Backup your existing watchlist:**
   ```bash
   cp watchlist.json watchlist.backup.json
   ```

2. **Create the new structure:**
   ```bash
   mkdir watchlists
   mv watchlist.json watchlists/yourname.json
   ```

3. **Replace `bin/update` with this script** (or merge the changes)

4. **Update `.github/workflows/deploy.yml`** to point to the new script (if needed)

5. **Test locally** before pushing to GitHub

## Advantages of This Approach

- ✅ **Easy to add users:** Just add a new `.json` file in `watchlists/`
- ✅ **Isolated outputs:** Each user has their own subdirectory
- ✅ **Separate calendars:** Each ICS feed is distinct
- ✅ **Backward compatible:** Migration support for single-user setup
- ✅ **No URL conflicts:** Each user has their own path

## Limitations

- Users share the same TMDb API key (rate limits apply)
- All watchlists are in the same repository (less privacy)
- All users update on the same schedule
- Requires creating GitHub Pages structure that supports subdirectories

## Alternative: Keeping Both Scripts

You can keep both scripts and choose which one to use:

- **Single user:** Use `bin/update` (original)
- **Multiple users:** Use `examples/multi_user_update.py`

Update `.github/workflows/deploy.yml` to use the appropriate script based on your needs.

## Next Steps

If you want to fully adopt this approach, see the [MULTI_USER_GUIDE.md](../MULTI_USER_GUIDE.md) for:
- Complete implementation guide
- Testing procedures
- Production deployment considerations
- Security and rate limit management

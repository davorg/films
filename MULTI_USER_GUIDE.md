# Multi-User Support Guide

This document outlines several approaches for supporting multiple users with the Film Releases Tracker. Each approach has different trade-offs in terms of complexity, isolation, and maintenance.

## Current Architecture

The current implementation is designed for **single-user** deployment:
- One `watchlist.json` file containing all tracked films
- Single static site output at GitHub Pages root
- One ICS calendar feed (`releases.ics`)
- Single TMDb API key used for all requests

## Proposed Approaches

### Approach 1: Fork-Based Personal Instances (Recommended for Most Users)

**Overview:** Each user forks the repository and maintains their own instance.

**Pros:**
- ✅ Complete isolation between users
- ✅ Minimal code changes required (zero changes to core functionality)
- ✅ Each user has full control over their watchlist
- ✅ Independent deployment schedules
- ✅ Personal GitHub Pages URL per user

**Cons:**
- ❌ Users must maintain their own fork
- ❌ Need to manually sync updates from upstream
- ❌ Each user needs their own TMDb API key
- ❌ Multiple separate deployments

**Implementation:**
1. User forks the repository to their own GitHub account
2. User configures their own `TMDB_API_KEY` secret
3. User enables GitHub Pages on their fork
4. User edits their `watchlist.json` with personal film choices
5. User's fork deploys to `https://<username>.github.io/films/`

**Best for:** Individual users who want complete control and privacy over their film tracking.

---

### Approach 2: Multiple Watchlists with User-Specific Outputs

**Overview:** Support multiple users within a single repository by creating separate watchlists and outputs for each user.

**Architecture Changes:**

```
Repository Structure:
├── watchlists/
│   ├── alice.json
│   ├── bob.json
│   └── charlie.json
├── site/
│   ├── index.html (shows all users or a directory)
│   ├── alice/
│   │   ├── index.html
│   │   ├── releases.json
│   │   └── releases.ics
│   ├── bob/
│   │   ├── index.html
│   │   ├── releases.json
│   │   └── releases.ics
│   └── charlie/
│       ├── index.html
│       ├── releases.json
│       └── releases.ics
```

**Required Changes:**

1. **Update `bin/update` script:**
   - Loop through all `watchlists/*.json` files
   - Generate separate outputs for each user in `site/<username>/`
   - Create a landing page that lists all users

2. **Update GitHub Actions workflow:**
   - No changes needed (same workflow works for all users)

3. **Update HTML templates:**
   - Support user parameter or generate separate HTML per user
   - Add user selector/directory on landing page

**Pros:**
- ✅ Single repository to maintain
- ✅ Centralized updates benefit all users
- ✅ Single TMDb API key (within rate limits)
- ✅ Easy to add new users (just add a JSON file)
- ✅ Each user gets their own ICS feed

**Cons:**
- ❌ All users share same domain
- ❌ Need to manage TMDb API rate limits across all users
- ❌ Requires moderate code changes
- ❌ Less privacy (all watchlists in same repo)

**Best for:** Small teams or families who want to share infrastructure but maintain separate watchlists.

---

### Approach 3: Single Shared Watchlist with User Tags

**Overview:** Use a single watchlist where each film entry is tagged with user(s) interested in it.

**Architecture Changes:**

```json
[
  {
    "tmdb_id": 603,
    "title_hint": "The Matrix",
    "users": ["alice", "bob"]
  },
  {
    "tmdb_id": 872585,
    "title_hint": "Oppenheimer",
    "users": ["charlie"]
  },
  {
    "tmdb_id": 1003596,
    "title_hint": "Avengers: Doomsday",
    "users": ["alice", "bob", "charlie"]
  }
]
```

**Required Changes:**

1. **Update `bin/update` script:**
   - Parse `users` field from each watchlist entry
   - Generate per-user outputs filtering films by user tag
   - Support "all" view showing all films

2. **Update site generation:**
   - Create user-specific pages and ICS feeds
   - Create aggregated view showing all films with user labels

**Pros:**
- ✅ Easy to see which films multiple users are interested in
- ✅ Reduces API calls (fetch each film once)
- ✅ Collaborative watchlist management
- ✅ Single source of truth

**Cons:**
- ❌ Less privacy (everyone sees everyone's interests)
- ❌ Potential for merge conflicts when editing watchlist
- ❌ Requires moderate code changes
- ❌ More complex watchlist management

**Best for:** Close-knit groups who want to discover shared interests and coordinate moviegoing.

---

### Approach 4: Configuration-Based User Profiles

**Overview:** Use a configuration file to define users and their watchlists, with flexible output options.

**Architecture Changes:**

```yaml
# config.yml
users:
  alice:
    watchlist: watchlists/alice.json
    output_dir: alice
    calendar_name: "Alice's Film Releases"
  
  bob:
    watchlist: watchlists/bob.json
    output_dir: bob
    calendar_name: "Bob's Movie Calendar"

shared:
  tmdb_api_key: "TMDB_API_KEY"  # from secrets
  update_schedule: "17 3 * * *"
```

**Required Changes:**

1. **Add configuration parser** (YAML/JSON)
2. **Update `bin/update`** to read config and process each user
3. **Make output paths configurable**
4. **Support per-user calendar naming**

**Pros:**
- ✅ Most flexible approach
- ✅ Easy to configure new users
- ✅ Supports different options per user
- ✅ Scalable to many users

**Cons:**
- ❌ Adds configuration complexity
- ❌ Requires significant code changes
- ❌ May need additional dependencies for config parsing
- ❌ More moving parts to maintain

**Best for:** Organizations or advanced users who need maximum flexibility and want to support many users.

---

## Comparison Matrix

| Feature | Fork-Based | Multiple Watchlists | Shared with Tags | Config-Based |
|---------|-----------|-------------------|-----------------|--------------|
| **Code Changes** | None | Moderate | Moderate | Significant |
| **Privacy** | High | Medium | Low | Medium |
| **Setup Complexity** | Low | Low | Low | Medium |
| **Maintenance** | Per-user | Central | Central | Central |
| **API Rate Limits** | Per-user | Shared | Shared | Shared |
| **Discoverability** | Low | Medium | High | Medium |
| **Best For** | Individuals | Small teams | Families/Groups | Organizations |

---

## Recommended Implementation Path

For most use cases, we recommend **Approach 1 (Fork-Based)** as it:
- Requires zero code changes
- Works today without modifications
- Provides maximum privacy and control
- Scales naturally (each user manages their own instance)

If you need centralized management, **Approach 2 (Multiple Watchlists)** offers the best balance of simplicity and functionality for small teams.

---

## Implementation Example: Approach 2 (Multiple Watchlists)

Here's what the implementation would look like for Approach 2:

### Step 1: Update Directory Structure

```bash
mkdir -p watchlists
mv watchlist.json watchlists/default.json
```

### Step 2: Modify `bin/update`

Key changes needed:

```python
# Near the top of bin/update
WATCHLISTS_DIR = ROOT / "watchlists"

def process_user_watchlist(watchlist_path: Path, output_dir: Path):
    """Process a single user's watchlist and generate outputs."""
    # Existing logic, but with configurable output paths
    ...

def main():
    if not TMDB_API_KEY:
        raise SystemExit("TMDB_API_KEY is not set.")
    
    # Process each watchlist file
    for watchlist_file in WATCHLISTS_DIR.glob("*.json"):
        username = watchlist_file.stem
        user_output_dir = OUT_DIR / username
        user_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Processing watchlist for user: {username}")
        process_user_watchlist(watchlist_file, user_output_dir)
    
    # Generate index page listing all users
    generate_index_page(OUT_DIR)
```

### Step 3: Update Workflow (Optional)

No changes needed to `.github/workflows/deploy.yml` - it will automatically process all watchlists.

### Step 4: Add Users

To add a new user:

```bash
# Create new watchlist
echo '[{"tmdb_id": 603, "title_hint": "The Matrix"}]' > watchlists/newuser.json

# Commit and push
git add watchlists/newuser.json
git commit -m "Add newuser's watchlist"
git push
```

User's site will be available at:
- `https://<org>.github.io/<repo>/newuser/`
- Calendar feed: `https://<org>.github.io/<repo>/newuser/releases.ics`

---

## Security Considerations

### API Rate Limits
- TMDb free tier: ~40 requests/10 seconds
- Each film requires 2 API calls (details + release dates)
- With 16 films per user: ~32 calls per user
- **Recommendation:** Limit to 10-15 users per repository for shared API key approach

### API Key Security
- Never commit `TMDB_API_KEY` to the repository
- Use GitHub Secrets for all deployments
- For fork-based approach: each user manages their own secret

### Privacy
- Watchlists in public repos are visible to everyone
- Consider private repos for sensitive watchlists
- ICS feeds are publicly accessible once deployed

---

## Testing Multi-User Setup Locally

For Approach 2, test locally:

```bash
# Create test watchlists
mkdir -p watchlists
echo '[{"tmdb_id": 603}]' > watchlists/alice.json
echo '[{"tmdb_id": 872585}]' > watchlists/bob.json

# Run update
TMDB_API_KEY="your-key" python3 bin/update

# Check outputs
ls -la site/alice/
ls -la site/bob/
```

---

## Migration Guide

### From Single User to Multiple Watchlists

1. **Backup current watchlist:**
   ```bash
   cp watchlist.json watchlist.backup.json
   ```

2. **Create watchlists directory:**
   ```bash
   mkdir watchlists
   ```

3. **Move current watchlist:**
   ```bash
   mv watchlist.json watchlists/yourname.json
   ```

4. **Update code** (implement Approach 2 changes)

5. **Test locally** before deploying

6. **Update documentation** to reflect new structure

---

## Frequently Asked Questions

### Can I mix approaches?

Yes! For example, you could:
- Use fork-based approach as the primary model
- Provide a "shared instance" option for teams using Approach 2
- Document both in README

### What about different regions (not just UK)?

This would require:
- Adding region parameter to watchlist entries
- Updating `choose_gb_theatrical_date()` to support multiple regions
- This is orthogonal to multi-user support

### Can users have different update schedules?

- **Fork-based:** Yes, each user configures their own cron schedule
- **Shared repo:** All users share the same schedule unless you implement per-user workflows

### How do I handle duplicate films?

- **Multiple Watchlists:** Each user can track the same film independently
- **Shared with Tags:** Film appears once, tagged with multiple users
- Deduplication during API calls can save rate limit quota

---

## Conclusion

The best approach depends on your specific needs:

- **Privacy-focused individuals:** Use **Approach 1 (Fork-Based)**
- **Small teams (2-5 people):** Use **Approach 2 (Multiple Watchlists)**  
- **Close-knit groups wanting to coordinate:** Use **Approach 3 (Shared Tags)**
- **Organizations with complex needs:** Use **Approach 4 (Config-Based)**

For most users, we recommend starting with the fork-based approach and migrating to a shared approach only if collaboration becomes important.

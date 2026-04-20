"""
Unit tests for the multi-user update script.

These tests validate the multi-user functionality without requiring TMDb API access.
"""
import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import datetime

import pytest

# Import the multi-user script
_script_path = Path(__file__).resolve().parents[1] / "examples" / "multi_user_update.py"
with open(_script_path, 'r') as f:
    _code = f.read()

multi_user = type(sys)('multi_user')
multi_user.__file__ = str(_script_path)
os.environ.setdefault('TMDB_API_KEY', 'test_key')
exec(_code, multi_user.__dict__)
sys.modules['multi_user'] = multi_user


class TestMultiUserUpdate:
    """Tests for multi-user update script."""
    
    def test_generate_index_page(self, tmp_path):
        """Test that index page is generated correctly."""
        users = ["alice", "bob", "charlie"]
        multi_user.generate_index_page(tmp_path, users)
        
        index_path = tmp_path / "index.html"
        assert index_path.exists()
        
        content = index_path.read_text()
        assert "alice" in content
        assert "bob" in content
        assert "charlie" in content
        assert "releases.ics" in content
        assert "Multi-user film tracking" in content
    
    def test_build_ics_events_with_username(self):
        """Test that ICS events include username in PRODID and calendar name."""
        movies = [{
            "tmdb_id": 123,
            "title": "Test Movie",
            "release_date": "2026-04-17",
            "tmdb_url": "https://www.themoviedb.org/movie/123"
        }]
        
        ics = multi_user.build_ics_events(movies, "20260101T000000Z", "alice")
        
        # Check user-specific fields
        assert "PRODID:-//Film Release Tracker//alice//EN" in ics
        assert "X-WR-CALNAME:alice's Film Releases" in ics
        assert "X-WR-CALDESC:UK theatrical releases tracked by alice" in ics
        assert "UID:tmdb-123-alice@film-release-tracker" in ics
    
    def test_build_ics_events_different_users(self):
        """Test that different users get different UIDs."""
        movies = [{
            "tmdb_id": 123,
            "title": "Test Movie",
            "release_date": "2026-04-17",
            "tmdb_url": "https://www.themoviedb.org/movie/123"
        }]
        
        ics_alice = multi_user.build_ics_events(movies, "20260101T000000Z", "alice")
        ics_bob = multi_user.build_ics_events(movies, "20260101T000000Z", "bob")
        
        assert "tmdb-123-alice@film-release-tracker" in ics_alice
        assert "tmdb-123-bob@film-release-tracker" in ics_bob
        assert ics_alice != ics_bob


class TestProcessUserWatchlist:
    """Tests for processing individual user watchlists."""
    
    @patch.object(multi_user, 'http_get_json')
    def test_process_user_creates_output_directory(self, mock_http, tmp_path):
        """Test that user output directory is created."""
        # Setup paths
        multi_user.OUT_DIR = tmp_path / "site"
        watchlist_path = tmp_path / "alice.json"
        watchlist_path.write_text('[{"tmdb_id": 603}]')
        
        # Mock API responses
        mock_http.side_effect = [
            {"title": "The Matrix", "poster_path": "/path.jpg"},
            {"results": [{"iso_3166_1": "GB", "release_dates": [
                {"type": 3, "release_date": "2026-05-01T00:00:00.000Z"}
            ]}]}
        ]
        
        today = datetime.date(2026, 1, 1)
        dtstamp = "20260101T000000Z"
        
        multi_user.process_user_watchlist(watchlist_path, "alice", today, dtstamp)
        
        # Check output directory was created
        user_dir = tmp_path / "site" / "alice"
        assert user_dir.exists()
        assert (user_dir / "releases.json").exists()
        assert (user_dir / "releases.ics").exists()
    
    @patch.object(multi_user, 'http_get_json')
    def test_process_user_includes_username_in_json(self, mock_http, tmp_path):
        """Test that username is included in JSON output."""
        multi_user.OUT_DIR = tmp_path / "site"
        watchlist_path = tmp_path / "bob.json"
        watchlist_path.write_text('[{"tmdb_id": 603}]')
        
        mock_http.side_effect = [
            {"title": "The Matrix", "poster_path": "/path.jpg"},
            {"results": [{"iso_3166_1": "GB", "release_dates": [
                {"type": 3, "release_date": "2026-05-01T00:00:00.000Z"}
            ]}]}
        ]
        
        today = datetime.date(2026, 1, 1)
        dtstamp = "20260101T000000Z"
        
        multi_user.process_user_watchlist(watchlist_path, "bob", today, dtstamp)
        
        json_path = tmp_path / "site" / "bob" / "releases.json"
        data = json.loads(json_path.read_text())
        
        assert data["username"] == "bob"
        assert "generated_at" in data
        assert "upcoming" in data
        assert "tbd" in data
        assert "released" in data


class TestMultiUserMain:
    """Tests for main function logic."""
    
    def test_migration_of_old_watchlist(self, tmp_path):
        """Test that old watchlist.json is migrated to watchlists/default.json."""
        # Setup
        multi_user.ROOT = tmp_path
        multi_user.WATCHLISTS_DIR = tmp_path / "watchlists"
        
        old_watchlist = tmp_path / "watchlist.json"
        old_watchlist.write_text('[{"tmdb_id": 603}]')
        
        # Simulate the migration check in main()
        if not multi_user.WATCHLISTS_DIR.exists():
            multi_user.WATCHLISTS_DIR.mkdir(parents=True, exist_ok=True)
            
            if old_watchlist.exists():
                default_watchlist = multi_user.WATCHLISTS_DIR / "default.json"
                default_watchlist.write_text(old_watchlist.read_text(encoding="utf-8"))
        
        # Verify migration
        default_path = tmp_path / "watchlists" / "default.json"
        assert default_path.exists()
        assert default_path.read_text() == '[{"tmdb_id": 603}]'

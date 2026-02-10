"""Tests for the update script functions."""
import datetime
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the update script by reading and executing it
_bin_path = Path(__file__).resolve().parents[1] / "bin" / "update"
with open(_bin_path, 'r') as f:
    _code = f.read()

# Create a module-like namespace
update = type(sys)('update')
update.__file__ = str(_bin_path)
# Set TMDB_API_KEY to avoid errors during import
os.environ.setdefault('TMDB_API_KEY', 'test_key')
exec(_code, update.__dict__)
sys.modules['update'] = update


class TestParseIsoDate:
    """Tests for parse_iso_date function."""
    
    def test_parse_standard_iso_datetime(self):
        """Test parsing standard ISO datetime string from TMDb."""
        result = update.parse_iso_date("2026-04-17T00:00:00.000Z")
        assert result == datetime.date(2026, 4, 17)
    
    def test_parse_iso_date_only(self):
        """Test parsing ISO date string without time."""
        result = update.parse_iso_date("2026-12-25")
        assert result == datetime.date(2026, 12, 25)
    
    def test_parse_leap_year_date(self):
        """Test parsing leap year date."""
        result = update.parse_iso_date("2024-02-29T00:00:00.000Z")
        assert result == datetime.date(2024, 2, 29)


class TestChooseGbTheatricalDate:
    """Tests for choose_gb_theatrical_date function."""
    
    def test_upcoming_theatrical_release(self):
        """Test with an upcoming GB theatrical release."""
        today = datetime.date(2026, 1, 1)
        payload = {
            "id": 123,
            "results": [
                {
                    "iso_3166_1": "GB",
                    "release_dates": [
                        {
                            "type": 3,  # Theatrical
                            "release_date": "2026-04-17T00:00:00.000Z"
                        }
                    ]
                }
            ]
        }
        date, bucket = update.choose_gb_theatrical_date(payload, today)
        assert date == "2026-04-17"
        assert bucket == "upcoming"
    
    def test_already_released_theatrical(self):
        """Test with a past GB theatrical release."""
        today = datetime.date(2026, 5, 1)
        payload = {
            "id": 123,
            "results": [
                {
                    "iso_3166_1": "GB",
                    "release_dates": [
                        {
                            "type": 3,  # Theatrical
                            "release_date": "2026-04-17T00:00:00.000Z"
                        }
                    ]
                }
            ]
        }
        date, bucket = update.choose_gb_theatrical_date(payload, today)
        assert date == "2026-04-17"
        assert bucket == "released"
    
    def test_no_gb_region(self):
        """Test with no GB region in release dates."""
        today = datetime.date(2026, 1, 1)
        payload = {
            "id": 123,
            "results": [
                {
                    "iso_3166_1": "US",
                    "release_dates": [
                        {
                            "type": 3,
                            "release_date": "2026-04-17T00:00:00.000Z"
                        }
                    ]
                }
            ]
        }
        date, bucket = update.choose_gb_theatrical_date(payload, today)
        assert date is None
        assert bucket is None
    
    def test_no_theatrical_release(self):
        """Test with GB region but no theatrical release."""
        today = datetime.date(2026, 1, 1)
        payload = {
            "id": 123,
            "results": [
                {
                    "iso_3166_1": "GB",
                    "release_dates": [
                        {
                            "type": 4,  # Digital
                            "release_date": "2026-04-17T00:00:00.000Z"
                        }
                    ]
                }
            ]
        }
        date, bucket = update.choose_gb_theatrical_date(payload, today)
        assert date is None
        assert bucket is None
    
    def test_multiple_theatrical_dates_choose_earliest_future(self):
        """Test with multiple theatrical dates, should choose earliest future date."""
        today = datetime.date(2026, 1, 1)
        payload = {
            "id": 123,
            "results": [
                {
                    "iso_3166_1": "GB",
                    "release_dates": [
                        {
                            "type": 3,
                            "release_date": "2026-05-01T00:00:00.000Z"
                        },
                        {
                            "type": 3,
                            "release_date": "2026-04-17T00:00:00.000Z"
                        }
                    ]
                }
            ]
        }
        date, bucket = update.choose_gb_theatrical_date(payload, today)
        assert date == "2026-04-17"
        assert bucket == "upcoming"
    
    def test_empty_results(self):
        """Test with empty results array."""
        today = datetime.date(2026, 1, 1)
        payload = {
            "id": 123,
            "results": []
        }
        date, bucket = update.choose_gb_theatrical_date(payload, today)
        assert date is None
        assert bucket is None


class TestGetUtcTimestamp:
    """Tests for get_utc_timestamp function."""
    
    def test_utc_timestamp_format(self):
        """Test that UTC timestamp is in correct format."""
        timestamp = update.get_utc_timestamp()
        # Should be in format YYYYMMDDTHHMMSSZ
        assert len(timestamp) == 16
        assert timestamp.endswith("Z")
        assert timestamp[8] == "T"
        
        # Verify it's a valid date/time
        year = int(timestamp[0:4])
        month = int(timestamp[4:6])
        day = int(timestamp[6:8])
        hour = int(timestamp[9:11])
        minute = int(timestamp[11:13])
        second = int(timestamp[13:15])
        
        assert 1 <= month <= 12
        assert 1 <= day <= 31
        assert 0 <= hour <= 23
        assert 0 <= minute <= 59
        assert 0 <= second <= 59


class TestIcsEscape:
    """Tests for ICS escape function (helper inside build_ics_events)."""
    
    def test_ics_escape_backslash(self):
        """Test escaping backslashes."""
        # This function is defined inside build_ics_events, so we test it indirectly
        # by examining the output
        movies = [{
            "tmdb_id": 123,
            "title": "Test\\Movie",
            "release_date": "2026-04-17",
            "tmdb_url": "https://www.themoviedb.org/movie/123"
        }]
        ics = update.build_ics_events(movies, "20260101T000000Z")
        assert "Test\\\\Movie" in ics
    
    def test_ics_escape_special_chars(self):
        """Test escaping semicolons and commas."""
        movies = [{
            "tmdb_id": 123,
            "title": "Test; Movie, Part 2",
            "release_date": "2026-04-17",
            "tmdb_url": "https://www.themoviedb.org/movie/123"
        }]
        ics = update.build_ics_events(movies, "20260101T000000Z")
        assert "Test\\; Movie\\, Part 2" in ics


class TestBuildIcsEvents:
    """Tests for build_ics_events function."""
    
    def test_empty_movies_list(self):
        """Test with empty movies list."""
        ics = update.build_ics_events([], "20260101T000000Z")
        assert "BEGIN:VCALENDAR" in ics
        assert "END:VCALENDAR" in ics
        assert "BEGIN:VEVENT" not in ics
    
    def test_single_movie(self):
        """Test with single movie."""
        movies = [{
            "tmdb_id": 123,
            "title": "Test Movie",
            "release_date": "2026-04-17",
            "tmdb_url": "https://www.themoviedb.org/movie/123"
        }]
        ics = update.build_ics_events(movies, "20260101T000000Z")
        
        assert "BEGIN:VCALENDAR" in ics
        assert "VERSION:2.0" in ics
        assert "BEGIN:VEVENT" in ics
        assert "END:VEVENT" in ics
        assert "UID:tmdb-123@film-release-tracker" in ics
        assert "SUMMARY:Test Movie (UK theatrical release)" in ics
        assert "DTSTART;VALUE=DATE:20260417" in ics
        assert "DTEND;VALUE=DATE:20260418" in ics  # Next day for all-day event
        assert "DTSTAMP:20260101T000000Z" in ics
    
    def test_multiple_movies(self):
        """Test with multiple movies."""
        movies = [
            {
                "tmdb_id": 123,
                "title": "Movie One",
                "release_date": "2026-04-17",
                "tmdb_url": "https://www.themoviedb.org/movie/123"
            },
            {
                "tmdb_id": 456,
                "title": "Movie Two",
                "release_date": "2026-05-20",
                "tmdb_url": "https://www.themoviedb.org/movie/456"
            }
        ]
        ics = update.build_ics_events(movies, "20260101T000000Z")
        
        assert ics.count("BEGIN:VEVENT") == 2
        assert ics.count("END:VEVENT") == 2
        assert "tmdb-123@film-release-tracker" in ics
        assert "tmdb-456@film-release-tracker" in ics
        assert "Movie One (UK theatrical release)" in ics
        assert "Movie Two (UK theatrical release)" in ics
    
    def test_ics_calendar_structure(self):
        """Test that ICS has required calendar structure."""
        movies = [{
            "tmdb_id": 123,
            "title": "Test",
            "release_date": "2026-04-17",
            "tmdb_url": "https://www.themoviedb.org/movie/123"
        }]
        ics = update.build_ics_events(movies, "20260101T000000Z")
        
        lines = ics.split("\n")
        assert lines[0] == "BEGIN:VCALENDAR"
        assert "VERSION:2.0" in ics
        assert "PRODID:-//Film Release Tracker//EN" in ics
        assert "CALSCALE:GREGORIAN" in ics
        assert "METHOD:PUBLISH" in ics
        assert lines[-2] == "END:VCALENDAR"


class TestHttpGetJson:
    """Tests for http_get_json function."""
    
    @patch('urllib.request.urlopen')
    def test_successful_json_fetch(self, mock_urlopen):
        """Test successful JSON fetch."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"key": "value"}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        result = update.http_get_json("https://api.example.com/data")
        assert result == {"key": "value"}
    
    @patch('urllib.request.urlopen')
    def test_json_with_unicode(self, mock_urlopen):
        """Test JSON fetch with unicode characters."""
        mock_response = MagicMock()
        mock_response.read.return_value = '{"title": "Café"}'.encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        result = update.http_get_json("https://api.example.com/data")
        assert result == {"title": "Café"}


class TestTmdbUrl:
    """Tests for tmdb_url function."""
    
    def test_url_construction(self):
        """Test URL construction with API key."""
        # Directly test with a mock API key since module is already loaded
        original_key = update.TMDB_API_KEY
        try:
            update.TMDB_API_KEY = 'test_key_123'
            url = update.tmdb_url("/movie/123", {"language": "en-GB"})
            assert "https://api.themoviedb.org/3/movie/123" in url
            assert "api_key=test_key_123" in url
            assert "language=en-GB" in url
        finally:
            update.TMDB_API_KEY = original_key

# Tests

This directory contains tests for both Python and JavaScript code in the Film Releases Tracker project.

## Python Tests (`test_update.py`)

Tests for the `bin/update` Python script that fetches movie data from TMDb and generates release files.

### Test Coverage (19 tests)

- **Date Parsing**: Tests for `parse_iso_date` function
  - Standard ISO datetime strings from TMDb
  - ISO date strings without time
  - Leap year dates

- **Release Date Selection**: Tests for `choose_gb_theatrical_date` function
  - Upcoming theatrical releases
  - Already released theatrical films
  - Films with no GB region data
  - Films with no theatrical release
  - Multiple theatrical dates (choosing earliest future date)
  - Empty results handling

- **Timestamp Generation**: Tests for `get_utc_timestamp` function
  - UTC timestamp format validation

- **ICS Calendar Generation**: Tests for `build_ics_events` function
  - Empty movies list
  - Single movie event
  - Multiple movie events
  - ICS calendar structure validation
  - Special character escaping (backslash, semicolon, comma)

- **API Functions**: Tests for HTTP and URL functions
  - JSON fetching with mocking
  - Unicode character handling
  - URL construction with API key

### Running Python Tests

```bash
# Install dependencies
pip install -r requirements-test.txt

# Run all Python tests
python -m pytest tests/test_update.py -v

# Run with coverage
python -m pytest tests/test_update.py --cov=bin
```

## JavaScript Tests (`app.test.js`)

Tests for the `site/app.js` frontend code that displays the movie releases.

### Test Coverage (21 tests)

- **Date Formatting**: Tests for date utility functions
  - `monthKey`: Extract year-month from ISO dates
  - `fmtMonthHeader`: Format month headers for display
  - `fmtDate`: Format full dates with weekday

- **DOM Element Creation**: Tests for `el` function
  - Basic element creation
  - Elements with classes
  - Elements with attributes
  - Text children
  - Element children
  - Mixed children
  - HTML content insertion

- **Data Loading**: Tests for `load` function
  - Successful JSON fetch
  - Error handling for failed fetches
  - Timeout configuration

- **Integration Tests**
  - Date formatting pipeline
  - Nested DOM structure creation

### Running JavaScript Tests

```bash
# Install dependencies
npm install

# Run all JavaScript tests
npm test

# Run tests in watch mode
npm run test:watch
```

## Continuous Integration

Tests are automatically run on every push and pull request via GitHub Actions. See `.github/workflows/tests.yml`.

## Notes

- Python tests use dynamic module loading since `bin/update` is an executable script without `.py` extension
- JavaScript tests use regex-based function extraction since `app.js` is an IIFE that doesn't export functions
- Both approaches are documented in the test files and work reliably for the current code structure

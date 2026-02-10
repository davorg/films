/**
 * Tests for site/app.js
 * 
 * Note: The app.js file is an IIFE (Immediately Invoked Function Expression)
 * that doesn't export its functions. We use regex extraction and eval to test
 * individual functions. This approach is fragile but avoids modifying the
 * production code structure.
 */

// Read the app.js file and extract the functions
const fs = require('fs');
const path = require('path');

// Load app.js content
const appJsPath = path.join(__dirname, '../site/app.js');
const appJsContent = fs.readFileSync(appJsPath, 'utf8');

// Helper to safely extract and eval a function
function safeExtractFunction(code, functionName, pattern) {
  const match = code.match(pattern);
  if (!match || !match[0]) {
    throw new Error(`Could not extract function ${functionName} from app.js`);
  }
  return eval(`(${match[0]})`);
}

// Extract functions with null safety checks
const monthKey = safeExtractFunction(
  appJsContent, 
  'monthKey',
  /function monthKey\(isoDate\) \{[\s\S]*?\n\}/
);

const fmtMonthHeader = safeExtractFunction(
  appJsContent,
  'fmtMonthHeader', 
  /function fmtMonthHeader\(yyyyMm\) \{[\s\S]*?\n\}/
);

const fmtDate = safeExtractFunction(
  appJsContent,
  'fmtDate',
  /function fmtDate\(isoDate\) \{[\s\S]*?\n\}/
);

const el = safeExtractFunction(
  appJsContent,
  'el',
  /function el\(tag, attrs = \{\}, children = \[\]\) \{[\s\S]*?\n\}/
);
describe('app.js - monthKey', () => {
  test('extracts year and month from ISO date', () => {
    expect(monthKey('2026-04-17')).toBe('2026-04');
  });

  test('handles different months', () => {
    expect(monthKey('2026-12-25')).toBe('2026-12');
    expect(monthKey('2026-01-01')).toBe('2026-01');
  });

  test('only takes first 7 characters', () => {
    expect(monthKey('2026-06-15')).toBe('2026-06');
  });
});

describe('app.js - fmtMonthHeader', () => {
  test('formats month and year for display', () => {
    const result = fmtMonthHeader('2026-04');
    expect(result).toMatch(/Apr.*2026/);
  });

  test('formats January', () => {
    const result = fmtMonthHeader('2026-01');
    expect(result).toMatch(/Jan.*2026/);
  });

  test('formats December', () => {
    const result = fmtMonthHeader('2026-12');
    expect(result).toMatch(/Dec.*2026/);
  });
});

describe('app.js - fmtDate', () => {
  test('formats date with weekday', () => {
    const result = fmtDate('2026-04-17');
    // Should contain day name, day number, month, and year
    expect(result).toMatch(/\w+/); // weekday
    expect(result).toContain('17');
    expect(result).toMatch(/Apr/);
    expect(result).toContain('2026');
  });

  test('handles different dates', () => {
    const result = fmtDate('2026-12-25');
    expect(result).toContain('25');
    expect(result).toMatch(/Dec/);
    expect(result).toContain('2026');
  });

  test('handles leap year date', () => {
    const result = fmtDate('2024-02-29');
    expect(result).toContain('29');
    expect(result).toMatch(/Feb/);
    expect(result).toContain('2024');
  });
});

describe('app.js - el (DOM element creation)', () => {
  test('creates basic element', () => {
    const element = el('div');
    expect(element.tagName).toBe('DIV');
  });

  test('creates element with class', () => {
    const element = el('div', { class: 'test-class' });
    expect(element.className).toBe('test-class');
  });

  test('creates element with attributes', () => {
    const element = el('a', { href: 'https://example.com', target: '_blank' });
    expect(element.getAttribute('href')).toBe('https://example.com');
    expect(element.getAttribute('target')).toBe('_blank');
  });

  test('creates element with text children', () => {
    const element = el('p', {}, ['Hello', ' ', 'World']);
    expect(element.textContent).toBe('Hello World');
  });

  test('creates element with element children', () => {
    const child = el('span', {}, ['child']);
    const parent = el('div', {}, [child]);
    expect(parent.children.length).toBe(1);
    expect(parent.children[0].tagName).toBe('SPAN');
    expect(parent.textContent).toBe('child');
  });

  test('creates element with mixed children', () => {
    const span = el('span', {}, ['bold']);
    const element = el('p', {}, ['Text ', span, ' more text']);
    expect(element.textContent).toBe('Text bold more text');
  });

  test('creates element with html attribute', () => {
    const element = el('div', { html: '<strong>Bold</strong>' });
    expect(element.innerHTML).toBe('<strong>Bold</strong>');
  });
});

describe('app.js - load function', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('fetches releases.json successfully', async () => {
    const mockData = {
      upcoming: [],
      tbd: [],
      released: []
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    // Extract and test the load function
    const loadFn = safeExtractFunction(
      appJsContent,
      'load',
      /async function load\(\) \{[\s\S]*?\n\}/
    );
    const result = await loadFn();

    expect(result).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith('releases.json', {
      cache: 'no-store',
      signal: expect.any(AbortSignal)
    });
  });

  test('throws error when fetch fails', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 404
    });

    const loadFn = safeExtractFunction(
      appJsContent,
      'load',
      /async function load\(\) \{[\s\S]*?\n\}/
    );
    
    await expect(loadFn()).rejects.toThrow('Failed to load releases.json: 404');
  });

  test('has timeout configuration', () => {
    // This test verifies that the load function includes timeout logic
    // Actual timeout testing would require complex async timing control
    const loadFn = safeExtractFunction(
      appJsContent,
      'load',
      /async function load\(\) \{[\s\S]*?\n\}/
    );

    expect(loadFn).toBeDefined();
    const fnString = loadFn.toString();
    expect(fnString).toContain('abort');
    expect(fnString).toContain('10000'); // 10 second timeout
  });
});

describe('app.js - Integration Tests', () => {
  test('monthKey and fmtMonthHeader work together', () => {
    const isoDate = '2026-04-17';
    const key = monthKey(isoDate);
    const formatted = fmtMonthHeader(key);
    
    expect(key).toBe('2026-04');
    expect(formatted).toMatch(/Apr.*2026/);
  });

  test('el creates nested structure correctly', () => {
    const card = el('div', { class: 'card' }, [
      el('h3', { class: 'title' }, ['Movie Title']),
      el('p', {}, ['Release date: ', el('strong', {}, ['April 17, 2026'])])
    ]);

    expect(card.className).toBe('card');
    expect(card.querySelector('.title').textContent).toBe('Movie Title');
    expect(card.querySelector('strong').textContent).toBe('April 17, 2026');
  });
});

async function load() {
  const res = await fetch('releases.json', { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to load releases.json: ${res.status}`);
  return await res.json();
}

function monthKey(isoDate) {
  // "YYYY-MM-DD" -> "YYYY-MM"
  return isoDate.slice(0, 7);
}

function fmtMonthHeader(yyyyMm) {
  const [y, m] = yyyyMm.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, 1));
  return dt.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' });
}

function mountUpcomingByMonth(gridId, items, emptyId, metaId) {
  const grid = document.getElementById(gridId);
  const empty = document.getElementById(emptyId);
  const meta = document.getElementById(metaId);

  grid.innerHTML = '';

  if (!items.length) {
    empty.hidden = false;
    meta.textContent = '0 films';
    return;
  }

  empty.hidden = true;
  meta.textContent = `${items.length} film${items.length === 1 ? '' : 's'}`;

  // items are already sorted by date by the generator
  const groups = new Map();
  for (const m of items) {
    const key = monthKey(m.release_date);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(m);
  }

  for (const [key, films] of groups.entries()) {
    const header = el('h3', { class: 'month-header' }, [fmtMonthHeader(key)]);
    const monthGrid = el('div', { class: 'grid' }, []);
    for (const film of films) monthGrid.appendChild(renderCard(film, 'upcoming'));

    grid.appendChild(el('div', { class: 'month-block' }, [header, monthGrid]));
  }
}

function el(tag, attrs = {}, children = []) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') n.className = v;
    else if (k === 'html') n.innerHTML = v;
    else n.setAttribute(k, v);
  }
  for (const c of children) n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  return n;
}

function fmtDate(isoDate) {
  // ISO "YYYY-MM-DD" -> nice UK display
  const [y, m, d] = isoDate.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  return dt.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
}

function renderCard(movie, mode) {
  const poster = el('div', { class: 'poster' }, []);
  if (movie.poster_url) {
    poster.appendChild(el('img', { src: movie.poster_url, alt: `${movie.title} poster`, loading: 'lazy' }));
  } else {
    poster.appendChild(el('div', { class: 'poster-fallback' }, ['TMDb']));
  }

  const pills = [];
  if (mode === 'upcoming') {
    pills.push(el('span', { class: 'pill' }, ['🎬 UK theatrical']));
    pills.push(el('span', { class: 'pill' }, ['📅 ', fmtDate(movie.release_date)]));
  } else if (mode === 'released') {
    pills.push(el('span', { class: 'pill' }, ['✅ Released']));
    pills.push(el('span', { class: 'pill' }, ['📅 ', fmtDate(movie.release_date)]));
  } else {
    pills.push(el('span', { class: 'pill' }, ['⏳ Date TBD']));
  }

  const line = el('div', { class: 'line' }, pills);

  const links = el('div', { class: 'links' }, [
    el('a', { class: 'link', href: movie.tmdb_url, target: '_blank', rel: 'noreferrer' }, ['TMDb ↗'])
  ]);

  return el('article', { class: 'card' }, [
    poster,
    el('div', { class: 'content' }, [
      el('h3', { class: 'title' }, [movie.title]),
      line,
      links
    ])
  ]);
}

function mount(gridId, items, mode, emptyId, metaId) {
  const grid = document.getElementById(gridId);
  const empty = document.getElementById(emptyId);
  const meta = document.getElementById(metaId);

  grid.innerHTML = '';
  if (!items.length) {
    empty.hidden = false;
    meta.textContent = '0 films';
    return;
  }
  empty.hidden = true;
  meta.textContent = `${items.length} film${items.length === 1 ? '' : 's'}`;

  for (const m of items) grid.appendChild(renderCard(m, mode));
}

(async () => {
  try {
    const data = await load();
    mountUpcomingByMonth('upcomingGrid', data.upcoming, 'upcomingEmpty', 'metaUpcoming');
    mount('tbdGrid', data.tbd, 'tbd', 'tbdEmpty', 'metaTbd');
    mount('releasedGrid', data.released, 'released', 'releasedEmpty', 'metaReleased');
  } catch (err) {
    console.error(err);
    document.body.prepend(el('div', { class: 'container' }, [
      el('div', { class: 'empty' }, ['Failed to load data. Check the console.'])
    ]));
  }
})();

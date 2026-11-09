(function () {
  'use strict';
  var LANGS = ['ru', 'en', 'he'];
  var root = document.documentElement;
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };

  /* storage is a convenience only: every read and write may fail */
  var store = {
    get: function (k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* ignore */ } }
  };

  function pickLang() {
    var saved = store.get('laii.lang');
    if (LANGS.indexOf(saved) > -1) return saved;
    var prefs = navigator.languages || [navigator.language || 'en'];
    for (var i = 0; i < prefs.length; i++) {
      var p = String(prefs[i]).toLowerCase().slice(0, 2);
      if (p === 'iw') p = 'he';
      if (LANGS.indexOf(p) > -1) return p;
    }
    return 'en';
  }

  var BY_CODE = {};
  CATALOG.forEach(function (it) { BY_CODE[it.c] = it; });

  var state = {
    lang: pickLang(),
    cur: null,
    cat: 'ALL',
    q: '',
    goal: 0,
    spec: []
  };
  state.cur = store.get('laii.cur') || (state.lang === 'en' ? 'usd' : 'ils');
  try {
    var savedSpec = JSON.parse(store.get('laii.spec') || '[]');
    if (Array.isArray(savedSpec)) state.spec = savedSpec.filter(function (c) { return BY_CODE[c]; });
  } catch (e) { state.spec = []; }

  /* ---------- text helpers ---------- */
  function li() { return LANGS.indexOf(state.lang); }
  /* In right-to-left text an en dash between two numbers flips their order; a hyphen keeps "3-5" together. */
  function fixHe(s) { return state.lang === 'he' ? s.replace(/(\d)–(\d)/g, '$1-$2') : s; }
  function t(key, vars) {
    var row = T[key];
    var s = row ? row[li()] : key;
    if (vars) Object.keys(vars).forEach(function (k) { s = s.replace('{' + k + '}', vars[k]); });
    return fixHe(s);
  }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  function nm(it) { return fixHe(it[state.lang][0]); }
  function ds(it) { return fixHe(it[state.lang][1]); }
  function catOf(it) { return it.c.split('-')[0]; }

  function fmt(n) { return new Intl.NumberFormat(state.lang === 'ru' ? 'ru-RU' : 'en-US').format(n); }
  function money(n) { return (state.cur === 'usd' ? '$' : '₪') + fmt(n); }
  function priceText(it) {
    if (it.q) return null;
    var i = state.cur === 'usd' ? 0 : 1;
    var parts = [];
    if (it.p) parts.push(money(it.p[i]) + (it.u ? t('u.' + it.u) : ''));
    if (it.pm) parts.push(money(it.pm[i]) + t('u.mo'));
    return parts.join(' + ');
  }
  function priceHTML(it) {
    var p = priceText(it);
    if (!p) return '<span>' + esc(t('p.quote')) + '</span>';
    var parts = p.split(' + ').map(function (x, i) { return '<span class="pp">' + (i ? '+ ' : '') + esc(x) + '</span>'; }).join(' ');
    /* no forced direction: in Hebrew the price must read right to left as "from, amount, per month" */
    return '<span class="pr-from">' + esc(t('p.from')) + '</span> <span>' + parts + '</span>';
  }
  function term(code) {
    if (!code) return '—';
    if (code === 'ong') return t('t.ong');
    if (code === '3m') return t('t.3m');
    if (code === '6m') return t('t.6m');
    var m = code.match(/^(\d+)(?:-(\d+))?([dwh])$/);
    if (!m) return code;
    var sep = state.lang === 'he' ? '-' : '–';
    return (m[2] ? m[1] + sep + m[2] : m[1]) + ' ' + t('t.' + m[3]);
  }
  function badges(it) {
    var f = it.f || '', out = '';
    if (f.indexOf('f') > -1) out += '<span class="badge b-f">' + esc(t('b.flag')) + '</span>';
    if (f.indexOf('b') > -1) out += '<span class="badge b-b">' + esc(t('b.buy')) + '</span>';
    if (f.indexOf('p') > -1) out += '<span class="badge b-p">' + esc(t('b.pilot')) + '</span>';
    return out;
  }
  function inSpec(code) { return state.spec.indexOf(code) > -1; }

  /* ---------- renderers ---------- */
  function rowHTML(it) {
    var on = inSpec(it.c);
    return '<article class="row' + (on ? ' is-in' : '') + '" data-code="' + it.c + '">' +
      '<span class="mono row-code">' + it.c + '</span>' +
      '<div class="row-main"><h4 class="row-name"><span>' + esc(nm(it)) + '</span>' + badges(it) + '</h4>' +
      '<p class="row-desc">' + esc(ds(it)) + '</p></div>' +
      '<div class="row-meta"><span class="mono row-term">' + esc(term(it.t)) + '</span>' +
      '<span class="row-price num">' + priceHTML(it) + '</span></div>' +
      '<button class="row-add" type="button" aria-pressed="' + on + '" aria-label="' +
      esc((on ? t('a11y.rem') : t('a11y.add')) + ' ' + nm(it)) + '"></button></article>';
  }

  function matches(it, q) {
    if (!q) return true;
    var hay = (it.c + ' ' + it.ru.join(' ') + ' ' + it.en.join(' ') + ' ' + it.he.join(' ')).toLowerCase();
    return q.split(/\s+/).every(function (w) { return hay.indexOf(w) > -1; });
  }

  function renderTabs() {
    var q = state.q.trim().toLowerCase();
    var html = '<button class="tab" type="button" data-tab="ALL" aria-pressed="' + (state.cat === 'ALL') + '">' +
      esc(t('cat.all')) + ' <small class="num">' + CATALOG.filter(function (it) { return matches(it, q); }).length + '</small></button>';
    CATS.forEach(function (c) {
      var n = CATALOG.filter(function (it) { return catOf(it) === c && matches(it, q); }).length;
      html += '<button class="tab" type="button" data-tab="' + c + '" aria-pressed="' + (state.cat === c) + '">' +
        esc(t('tab.' + c)) + ' <small class="num">' + n + '</small></button>';
    });
    $('#tabs').innerHTML = html;
  }

  function renderCatalog() {
    var q = state.q.trim().toLowerCase();
    var html = '';
    CATS.forEach(function (c) {
      if (state.cat !== 'ALL' && state.cat !== c) return;
      var items = CATALOG.filter(function (it) { return catOf(it) === c && matches(it, q); });
      if (!items.length) return;
      html += '<header class="grp"><span class="mono">' + c + '</span><h3>' + esc(t('cat.' + c)) +
        '</h3><span class="mono num">' + items.length + '</span></header>' + items.map(rowHTML).join('');
    });
    if (!html) {
      html = '<div class="empty"><span>' + esc(t('cat.empty')) + '</span>' +
        '<button class="btn btn-line btn-sm" type="button" id="resetFilter">' + esc(t('cat.reset')) + '</button></div>';
    }
    $('#bom').innerHTML = html;
    renderTabs();
  }

  function renderGoals() {
    $('#goalChips').innerHTML = GOALS.map(function (g, i) {
      return '<button class="chip" type="button" data-goal="' + i + '" aria-pressed="' + (state.goal === i) + '">' + esc(t(g[0])) + '</button>';
    }).join('');
    var g = GOALS[state.goal];
    $('#goalOut').innerHTML = '<div class="goal-out-head"><span class="mono">' + esc(t('goal.start')) + '</span>' +
      '<a href="#catalog" data-cat="' + g[1] + '">' + esc(t('goal.all')) + ': ' + esc(t('cat.' + g[1])) + ' <span class="arr" aria-hidden="true">→</span></a></div>' +
      '<div style="padding-inline:1rem">' + g[2].map(function (c) { return rowHTML(BY_CODE[c]); }).join('') + '</div>';
  }

  function renderQuick() {
    $('#quickGrid').innerHTML = QUICK.map(function (code) {
      var it = BY_CODE[code];
      return '<article class="q"><em class="mono">' + code + ' · ' + esc(term(it.t)) + '</em>' +
        '<h3>' + esc(nm(it)) + '</h3><span class="pr num">' + priceHTML(it) + '</span>' +
        '<p>' + esc(ds(it)) + '</p>' +
        '<button class="btn btn-line btn-sm" type="button" data-add="' + code + '"></button></article>';
    }).join('');
  }

  function renderTools() {
    var track = TOOLS.map(function (n) { return '<span>' + esc(n) + '</span><i aria-hidden="true">+</i>'; }).join('');
    $('#mq').innerHTML = '<div class="mq-track">' + track + '</div><div class="mq-track" aria-hidden="true">' + track + '</div>';
  }

  function syncSpecUI() {
    var n = state.spec.length;
    $('#specCount').textContent = n;
    $('#fabCount').textContent = n;
    $('#specBtn').classList.toggle('has', n > 0);
    $('#fab').classList.toggle('show', n > 0);
    $$('.row').forEach(function (r) {
      var on = inSpec(r.getAttribute('data-code'));
      r.classList.toggle('is-in', on);
      var b = $('.row-add', r), it = BY_CODE[r.getAttribute('data-code')];
      b.setAttribute('aria-pressed', on);
      b.setAttribute('aria-label', (on ? t('a11y.rem') : t('a11y.add')) + ' ' + nm(it));
    });
    $$('[data-add]').forEach(function (b) {
      var on = inSpec(b.getAttribute('data-add'));
      b.textContent = on ? t('btn.added') : t('btn.add');
      b.classList.toggle('is-in', on);
      b.setAttribute('aria-pressed', on);
    });
    renderDrawer();
  }

  function totals() {
    var i = state.cur === 'usd' ? 0 : 1, once = 0, mo = 0;
    state.spec.forEach(function (c) {
      var it = BY_CODE[c];
      if (it.p) { if (it.u === 'mo') mo += it.p[i]; else once += it.p[i]; }
      if (it.pm) mo += it.pm[i];
    });
    return { once: once, mo: mo };
  }

  function renderDrawer() {
    var body = $('#drBody'), foot = $('#drFoot');
    if (!state.spec.length) {
      body.innerHTML = '<p class="dr-empty">' + esc(t('sp.empty')) + '</p>';
      foot.hidden = true;
      return;
    }
    foot.hidden = false;
    body.innerHTML = state.spec.map(function (c) {
      var it = BY_CODE[c];
      return '<div class="dr-item"><span class="mono">' + c + '</span><b>' + esc(nm(it)) + '</b>' +
        '<span class="row-price num">' + priceHTML(it) + '</span>' +
        '<button type="button" data-remove="' + c + '" aria-label="' + esc(t('a11y.rem') + ' ' + nm(it)) + '"></button></div>';
    }).join('');
    var tt = totals();
    $('#totOnce').textContent = tt.once ? money(tt.once) : '—';
    $('#totMo').textContent = tt.mo ? money(tt.mo) : '—';
    var lines = [t('sp.hi')];
    state.spec.forEach(function (c) {
      var it = BY_CODE[c], p = priceText(it);
      lines.push('• ' + c + ' ' + nm(it) + ' — ' + (p ? t('p.from') + ' ' + p : t('p.quote')));
    });
    var est = [];
    if (tt.once) est.push(t('sp.onceS') + ' ' + money(tt.once));
    if (tt.mo) est.push(t('sp.moS') + ' ' + money(tt.mo));
    if (est.length) lines.push(t('sp.est') + ': ' + est.join(', ') + '.');
    $('#reqText').value = lines.join('\n');
  }

  function applyI18n() {
    root.lang = state.lang;
    root.dir = state.lang === 'he' ? 'rtl' : 'ltr';
    $$('[data-i]').forEach(function (el) { el.textContent = t(el.getAttribute('data-i')); });
    $$('[data-i-aria]').forEach(function (el) { el.setAttribute('aria-label', t(el.getAttribute('data-i-aria'))); });
    $$('[data-i-ph]').forEach(function (el) { el.setAttribute('placeholder', t(el.getAttribute('data-i-ph'))); });
    $$('[data-i-alt]').forEach(function (el) { el.setAttribute('alt', t(el.getAttribute('data-i-alt'))); });
    $('#h1c').textContent = t('hero.h1c', { n: CATALOG.length });
    $('#catDim').textContent = t('cat.dim', { n: CATALOG.length });
    $$('#langSeg button').forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-lang') === state.lang); });
    $$('#curSeg button').forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-cur') === state.cur); });
  }

  function renderPrices() {
    $('#loadSym').textContent = state.cur === 'usd' ? '$' : '₪';
    $$('[data-price]').forEach(function (el) { el.innerHTML = priceHTML(BY_CODE[el.getAttribute('data-price')]); });
  }

  /* shrink the orange headline label to its longest line (CSS cannot shrink-wrap wrapped text) */
  function fitHL() {
    var hl = $('#h1c');
    hl.style.width = '';
    var r = document.createRange();
    r.selectNodeContents(hl);
    /* mixed-direction text gives several boxes per line, so measure each line as a whole */
    var rects = r.getClientRects(), lines = {}, w = 0;
    for (var i = 0; i < rects.length; i++) {
      var k = Math.round(rects[i].top / 8);
      var ln = lines[k] || (lines[k] = { l: Infinity, r: -Infinity });
      ln.l = Math.min(ln.l, rects[i].left); ln.r = Math.max(ln.r, rects[i].right);
    }
    Object.keys(lines).forEach(function (k) { w = Math.max(w, lines[k].r - lines[k].l); });
    if (!w) return;
    var cs = getComputedStyle(hl);
    hl.style.width = Math.ceil(w + parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight) + 1) + 'px';
  }

  function renderAll() {
    applyI18n();
    renderPrices();
    renderGoals();
    renderQuick();
    renderCatalog();
    syncSpecUI();
    startTyping();
    fitHL();
  }

  /* ---------- hero: typed examples ---------- */
  var typed = $('#typed'), typeTimer = null;
  var calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function startTyping() {
    clearTimeout(typeTimer);
    var list = EXAMPLES[state.lang], idx = 0, pos = list[0].length, erasing = true;
    typed.textContent = list[0];
    if (calm) {
      typeTimer = setInterval(function () { idx = (idx + 1) % list.length; typed.textContent = list[idx]; }, 4500);
      return;
    }
    function step() {
      var s = list[idx];
      if (erasing) {
        pos -= 2;
        if (pos <= 0) { pos = 0; erasing = false; idx = (idx + 1) % list.length; typed.textContent = ''; typeTimer = setTimeout(step, 260); return; }
        typed.textContent = s.slice(0, pos);
        typeTimer = setTimeout(step, 18);
      } else {
        pos += 1;
        typed.textContent = s.slice(0, pos);
        if (pos >= s.length) { erasing = true; typeTimer = setTimeout(step, 2400); return; }
        typeTimer = setTimeout(step, 36);
      }
    }
    typeTimer = setTimeout(step, 2600);
  }

  /* ---------- toast ---------- */
  var toastEl = $('#toast'), toastTimer = null;
  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 1800);
  }

  /* ---------- quote (spec) ---------- */
  function toggleSpec(code) {
    var i = state.spec.indexOf(code);
    if (i > -1) { state.spec.splice(i, 1); toast(t('sp.removedT')); }
    else { state.spec.push(code); toast(t('sp.addedT') + ': ' + code); }
    store.set('laii.spec', JSON.stringify(state.spec));
    syncSpecUI();
  }

  var drawer = $('#drawer'), scrim = $('#scrim'), lastFocus = null;
  function openDrawer() {
    lastFocus = document.activeElement;
    drawer.classList.add('open'); scrim.classList.add('open');
    drawer.removeAttribute('inert');
    root.style.overflow = 'hidden';
    $('#drClose').focus();
  }
  function closeDrawer() {
    drawer.classList.remove('open'); scrim.classList.remove('open');
    drawer.setAttribute('inert', '');
    root.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  function copyText(text, fallbackEl) {
    function done() { toast(t('ct.copied')); }
    function manual() {
      if (fallbackEl && fallbackEl.select) { fallbackEl.focus(); fallbackEl.select(); }
      else if (fallbackEl) { var r = document.createRange(); r.selectNodeContents(fallbackEl); var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); }
      toast(t('sp.selT'));
    }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, manual);
    else manual();
  }

  /* ---------- mobile menu ---------- */
  var mnav = $('#mnav'), menuBtn = $('#menuBtn');
  function setMenu(open) {
    mnav.classList.toggle('open', open);
    menuBtn.setAttribute('aria-expanded', open);
    root.style.overflow = open ? 'hidden' : '';
  }

  function goCat(cat) {
    state.cat = cat; state.q = ''; $('#q').value = '';
    renderCatalog(); syncSpecUI();
  }

  /* ---------- events ---------- */
  document.addEventListener('click', function (e) {
    var el = e.target.closest ? e.target : e.target.parentElement;
    if (!el) return;
    var hit;
    if ((hit = el.closest('.row-add'))) { toggleSpec(hit.parentElement.getAttribute('data-code')); return; }
    if ((hit = el.closest('[data-add]'))) { toggleSpec(hit.getAttribute('data-add')); return; }
    if ((hit = el.closest('[data-remove]'))) { toggleSpec(hit.getAttribute('data-remove')); return; }
    if ((hit = el.closest('[data-tab]'))) { state.cat = hit.getAttribute('data-tab'); renderCatalog(); syncSpecUI(); return; }
    if ((hit = el.closest('[data-goal]'))) { state.goal = +hit.getAttribute('data-goal'); renderGoals(); syncSpecUI(); return; }
    if ((hit = el.closest('[data-cat]'))) { goCat(hit.getAttribute('data-cat')); }
    if ((hit = el.closest('[data-lang]'))) { state.lang = hit.getAttribute('data-lang'); store.set('laii.lang', state.lang); renderAll(); return; }
    if ((hit = el.closest('[data-cur]'))) { state.cur = hit.getAttribute('data-cur'); store.set('laii.cur', state.cur); renderAll(); return; }
    if (el.closest('#resetFilter')) { goCat('ALL'); return; }
    if (el.closest('#specBtn') || el.closest('#fab')) { openDrawer(); return; }
    if (el.closest('#drClose') || el.closest('#scrim')) { closeDrawer(); return; }
    if (el.closest('#reqCopy')) { copyText($('#reqText').value, $('#reqText')); return; }
    if (el.closest('#reqClear')) { state.spec = []; store.set('laii.spec', '[]'); syncSpecUI(); return; }
    if (el.closest('#mailCopy')) { copyText($('#mailTxt').textContent, $('#mailTxt')); return; }
    if (el.closest('#menuBtn')) { setMenu(!mnav.classList.contains('open')); return; }
    if (el.closest('#mnav a')) { setMenu(false); return; }
    if (el.closest('#themeBtn') || el.closest('[data-theme-toggle]')) {
      var cur = root.getAttribute('data-theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      var next = cur === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next); store.set('laii.theme', next);
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (drawer.classList.contains('open')) closeDrawer();
    else if (mnav.classList.contains('open')) setMenu(false);
  });
  var qTimer = null;
  $('#q').addEventListener('input', function (e) {
    clearTimeout(qTimer);
    var v = e.target.value;
    qTimer = setTimeout(function () { state.q = v; renderCatalog(); syncSpecUI(); }, 120);
  });

  /* drafting crosshair in the hero, for mouse users only */
  var hero = $('#hero'), xhR = $('#xhR'), raf = 0;
  if (window.matchMedia && window.matchMedia('(hover:hover) and (pointer:fine)').matches && !calm) {
    hero.addEventListener('pointermove', function (e) {
      if (raf) return;
      raf = requestAnimationFrame(function () {
        raf = 0;
        var r = hero.getBoundingClientRect(), x = Math.round(e.clientX - r.left), y = Math.round(e.clientY - r.top);
        hero.style.setProperty('--mx', x + 'px');
        hero.style.setProperty('--my', y + 'px');
        xhR.textContent = 'X ' + ('000' + x).slice(-4) + '  Y ' + ('000' + y).slice(-4);
        hero.classList.add('live');
      });
    });
    hero.addEventListener('pointerleave', function () { hero.classList.remove('live'); });
  }

  /* highlight the nav item of the section in view */
  if ('IntersectionObserver' in window) {
    var links = {};
    $$('.nav a').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var a = links[en.target.id];
        if (a && en.isIntersecting) { $$('.nav a').forEach(function (x) { x.classList.remove('on'); }); a.classList.add('on'); }
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    Object.keys(links).forEach(function (id) { var s = document.getElementById(id); if (s) io.observe(s); });
  }

  var savedTheme = store.get('laii.theme');
  if (savedTheme === 'dark' || savedTheme === 'light') root.setAttribute('data-theme', savedTheme);

  var fitTimer = null;
  window.addEventListener('resize', function () { clearTimeout(fitTimer); fitTimer = setTimeout(fitHL, 120); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitHL);

  renderTools();
  renderAll();
})();

/* core.js — ядро движка «Мультмашина».

   Идея: каждый кадр — чистая функция от времени. Сцена один раз строится кодом (SVG), все движения записываются как
   отрезки «ключ элемента: от значения к значению за такой-то промежуток», а на любое время t состояние считается заново.
   Поэтому перемотка, пауза и покадровый рендер дают один и тот же результат, а видео можно снимать в любом порядке.

   Эпизод состоит из битов: бит = одна реплика закадрового голоса + картинка к ней. Биты идут друг за другом, длина бита —
   максимум из (пауза до голоса + длина реплики) и конца последней анимации, плюс пауза после бита.

   Файл подключается обычным <script>; имена ниже — глобальные, чтобы код сцен был коротким. */
'use strict';

const SVG_NS = 'http://www.w3.org/2000/svg';
const STYLE = window.STYLE || {};                                   // style.js, собирает scripts/build.py из TOML
const STAGE = Object.assign({ w: 900, h: 1600 }, STYLE.stage);
const W = STAGE.w, H = STAGE.h, CX = W / 2;
const FX = Object.assign({ lead: .22, hold: .6, grain: true, vignette: .5 }, STYLE.effects);
const LEAD = FX.lead;                                               // картинка опережает слово на LEAD секунд: на самом слове она уже «приехала»

// ---------- плавности ----------
const lin = q => q;
const out = q => 1 - Math.pow(1 - q, 3);
const io = q => q < .5 ? 4 * q * q * q : 1 - Math.pow(-2 * q + 2, 3) / 2;
const soft = q => (1 - Math.cos(Math.PI * q)) / 2;
const back = q => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(q - 1, 3) + c1 * Math.pow(q - 1, 2); };
const clamp01 = q => q < 0 ? 0 : q > 1 ? 1 : q;
const ramp01 = (t, a, b) => clamp01((t - a) / (b - a));
const smooth = q => q * q * (3 - 2 * q);
function seeded(seed) { return () => (seed = (seed * 16807) % 2147483647) / 2147483647; }   // повторяемый «случайный» ряд

// ---------- контекст сборки ----------
let CUR = null;            // бит, который сейчас строится
let RENDERING = false;     // идёт расчёт кадра (put внутри prog пишет поверх анимации)
let BEAT_ID = '';
const BEAT_LIST = [];      // собранные биты

// ---------- элементы ----------
// Состояние элемента: x y (сдвиг), s (масштаб), r (поворот, градусы), o (прозрачность), d (доля нарисованной линии, 0..1).
const KEYS = ['x', 'y', 's', 'r', 'o', 'd'];
const num = v => Math.round(v * 1000) / 1000;

function mk(tag, attrs = {}, parent) {
  const e = document.createElementNS(SVG_NS, tag);
  for (const k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}

function paint(e, v) {
  v = v || e._b;
  const tr = [];
  if (v.x || v.y) tr.push(`translate(${num(v.x)} ${num(v.y)})`);
  if (v.r) tr.push(`rotate(${num(v.r)})`);
  if (v.s !== 1) tr.push(`scale(${num(v.s)})`);
  if (tr.length) e.setAttribute('transform', tr.join(' ')); else e.removeAttribute('transform');
  if (v.o >= 1) e.removeAttribute('opacity'); else e.setAttribute('opacity', num(Math.max(0, v.o)));
  if (e._len !== undefined) {
    e.setAttribute('stroke-dashoffset', num(e._len * (1 - v.d)));
    // нерисованная линия скрыта совсем: с круглыми кончиками штрих нулевой длины всё равно оставляет точку
    if (v.d <= 0.001) e.setAttribute('visibility', 'hidden'); else e.removeAttribute('visibility');
  }
}

function withState(e, st) {
  e._b = Object.assign({ x: 0, y: 0, s: 1, r: 0, o: 1, d: 1 }, st);
  paint(e);
  return e;
}

// группа с состоянием
const G = (parent, st = {}) => withState(mk('g', {}, parent), st);

// текст: x, y — сдвиг (состояние), остальное — оформление
function T(parent, str, o = {}) {
  const { x = 0, y = 0, o: op = 1, size = 40, fill, font, weight = 600, anchor = 'start' } = o;
  const e = mk('text', { 'font-size': size, 'font-family': font || (STYLE.fonts && STYLE.fonts.display_stack) || 'sans-serif', 'font-weight': weight, 'text-anchor': anchor }, parent);
  if (fill) e.setAttribute('fill', fill);
  e.textContent = str;
  return withState(e, { x, y, o: op });
}

// контур; со вторым состоянием {d: 0} готов к рисованию линии через draw()
function path(parent, d, attrs = {}, st) {
  const e = mk('path', Object.assign({ d }, attrs), parent);
  if (st && 'd' in st) {
    const probe = mk('path', { d }, document.querySelector('svg'));   // длину контура можно узнать только у элемента в документе
    e._len = probe.getTotalLength(); probe.remove();
    e.setAttribute('stroke-dasharray', e._len);
  }
  return withState(e, st || {});
}

const rect = (p, x, y, w, h, attrs = {}) => mk('rect', Object.assign({ x, y, width: w, height: h }, attrs), p);

// ---------- анимация ----------
function valueAt(e, key, t) {
  let v = e._b[key];
  const segs = e._sg && e._sg[key];
  if (segs) for (const s of segs) {
    if (t < s.t0) break;
    v = t >= s.t1 ? s.to : s.from + (s.to - s.from) * s.ease((t - s.t0) / (s.t1 - s.t0));
  }
  return v;
}

function reg(e) { if (CUR) CUR.els.add(e); }

// tw(элемент, {x, y, s, r, o, d}, начало, длительность, плавность): отрезок движения; «от» берётся как значение в момент начала
function tw(e, to, t0, dur = .3, ease = io) {
  e._sg = e._sg || {};
  for (const k in to) {
    const segs = e._sg[k] = e._sg[k] || [];
    segs.push({ t0, t1: t0 + Math.max(dur, 1e-6), from: valueAt(e, k, t0), to: to[k], ease });
    segs.sort((a, b) => a.t0 - b.t0);
  }
  reg(e);
  if (CUR) CUR.end = Math.max(CUR.end, t0 + dur);
  return e;
}
const show = (e, t0, dur = .2, ease = lin) => tw(e, { o: 1 }, t0, dur, ease);
const hide = (e, t0, dur = .2, ease = lin) => tw(e, { o: 0 }, t0, dur, ease);
const draw = (e, t0, dur = .5, ease = out) => tw(e, { d: 1 }, t0, dur, ease);

// put: мгновенно задать состояние; внутри prog() значение накладывается поверх анимации этого кадра
function put(e, st) {
  if (RENDERING) { e._ov = Object.assign(e._ov || {}, st); paint(e, Object.assign({}, e._cur || e._b, e._ov)); return e; }
  Object.assign(e._b, st); paint(e);
  return e;
}

// prog(f, начало, длительность, плавность): f(q) вызывается на каждом кадре с долей q от 0 до 1 (до начала — 0, после конца — 1)
function prog(f, t0, dur, ease = lin) {
  CUR.progs.push({ f, t0, dur: Math.max(dur, 1e-6), ease });
  CUR.end = Math.max(CUR.end, t0 + dur);
}

// tick(f): f(t) на каждом кадре со временем бита t (секунды). Бит не растягивает — для постоянного движения: качание, вращение, мерцание
function tick(f) { CUR.ticks.push(f); }

// звуковой эффект на часах бита; файл — sfx/<имя>.mp3; громкость 1 — обычная (в смеси половина от голоса)
function sfx(_beat, t, name, vol = 1) { if (CUR) CUR.sfx.push({ t, name, vol }); }

// панель текущего бита (группа SVG, которую показывают только пока идёт бит)
const panel = () => CUR.panel;

// ---------- сборка эпизода ----------
function buildBeats(defs) {
  const svg = document.getElementById('mm-svg');
  let start = 0;
  defs.forEach(([id, title, run, extra = {}]) => {
    const tm = (window.TIMINGS || {})[id];
    if (!tm) throw new Error(`Для бита «${id}» нет времён озвучки (timings): запустите озвучку или сборку`);
    const pre = extra.pre || 0;
    const p = mk('g', { display: 'none' }, svg);
    CUR = { id, title, panel: p, els: new Set(), progs: [], ticks: [], sfx: [], end: 0, pre, dur: tm.dur, start };
    BEAT_ID = id;
    // m('метка', сдвиг): время начала слова после [[метка]] на часах бита (с опережением LEAD)
    const m = (name, off = 0) => {
      if (!(name in tm.marks)) throw new Error(`В бите «${id}» нет метки «${name}»`);
      return Math.max(0, tm.marks[name] + pre + off - LEAD);
    };
    run(m, tm.dur);
    CUR.len = Math.max(pre + tm.dur, CUR.end) + FX.hold;
    start += CUR.len;
    BEAT_LIST.push(CUR);
    CUR = null;
  });
  return start;
}

function evalBeat(b, lt) {
  RENDERING = true;
  for (const e of b.els) {
    e._ov = null;
    const v = {};
    for (const k of KEYS) v[k] = e._sg && e._sg[k] ? valueAt(e, k, lt) : e._b[k];
    e._cur = v;
    paint(e, v);
  }
  for (const p of b.progs) p.f(p.ease(clamp01((lt - p.t0) / p.dur)));
  for (const f of b.ticks) f(lt);
  RENDERING = false;
}

let shown = null;
function renderAt(t) {
  let b = BEAT_LIST.find(x => t < x.start + x.len) || BEAT_LIST[BEAT_LIST.length - 1];
  if (shown !== b) { if (shown) shown.panel.setAttribute('display', 'none'); b.panel.setAttribute('display', 'inline'); shown = b; }
  BEAT_ID = b.id;
  evalBeat(b, Math.min(t - b.start, b.len));
}

// описание эпизода для рендера и озвучки: длительность, биты (где начинается голос), звуковые эффекты
function manifest() {
  const total = BEAT_LIST.reduce((s, b) => s + b.len, 0);
  return {
    w: W, h: H, duration: total,
    beats: BEAT_LIST.map(b => ({ id: b.id, start: b.start, len: b.len, voice_at: b.start + b.pre, voice_dur: b.dur })),
    sfx: BEAT_LIST.flatMap(b => b.sfx.map(s => ({ t: b.start + s.t, name: s.name, vol: s.vol }))),
  };
}

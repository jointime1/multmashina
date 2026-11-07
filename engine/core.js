/* core.js — ядро движка «Мультмашина».

   Идея: каждый кадр — чистая функция от времени. Сцена один раз строится кодом (SVG), все движения записываются как
   отрезки «ключ элемента: от значения к значению за такой-то промежуток», а на любое время t состояние считается заново.
   Поэтому перемотка, пауза и покадровый рендер дают один и тот же результат, а видео можно снимать в любом порядке.

   Эпизод состоит из битов: бит = одна реплика закадрового голоса + картинка к ней. Биты идут друг за другом, длина бита —
   максимум из (пауза до голоса + длина реплики) и конца последней анимации, плюс пауза после бита (эффекты → пауза_после_бита, по умолчанию 0,3 с).
   Пауза между репликами на видео = эта пауза + хвост голоса: длинные паузы почти всегда от анимации, которая кончается позже слов.

   Файл подключается обычным <script>; имена ниже — глобальные, чтобы код сцен был коротким. */
'use strict';

const SVG_NS = 'http://www.w3.org/2000/svg';
const STYLE = window.STYLE || {};                                   // style.js, собирает scripts/build.py из TOML
const STAGE = Object.assign({ w: 900, h: 1600 }, STYLE.stage);
const W = STAGE.w, H = STAGE.h, CX = W / 2;
const FX = Object.assign({ lead: .22, hold: .3, grain: true, vignette: .5 }, STYLE.effects);
const LEAD = FX.lead;
// движение: входы элементов, переходы между сценами, камера, реакция героев (стиль → анимации); по умолчанию всё выключено
// манера рисунка (стиль → манера, engine/manner.js): по умолчанию всё как нарисовано
const MN = Object.assign({ line: 1, wobble: 0, detail: .012, boil: 8, step: 0, tones: [], stepped: true, dots: 0, paper: '', flat: false, eyes: 'round', headW: 1, headH: 1, body: 1, neck: 1, rig: 'bust', pixels: 0 }, STYLE.manner);
const MO = Object.assign({ enters: [], trans: [], cam: [], camAmp: .04, transDur: .22, punch: 0, feel: 'smooth' }, STYLE.motion);                                               // картинка опережает слово на LEAD секунд: на самом слове она уже «приехала»

// ---------- плавности ----------
// Характер движения (стиль → анимации → характер): набор кривых на весь ролик. Сцены зовут out, io, soft, back, а какая это кривая, решает характер,
// поэтому один и тот же код сцены с пружиной «играет», а с механикой «едет по рельсам». out, io и soft не перелетают цель (по ним считают числа и рисуют линии),
// перелёт — только у back.
const lin = q => q;
const cubicOut = q => 1 - Math.pow(1 - q, 3);
const cubicIO = q => q < .5 ? 4 * q * q * q : 1 - Math.pow(-2 * q + 2, 3) / 2;
const cosSoft = q => (1 - Math.cos(Math.PI * q)) / 2;
const overshoot = q => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(q - 1, 3) + c1 * Math.pow(q - 1, 2); };
const elastic = q => q <= 0 ? 0 : q >= 1 ? 1 : Math.pow(2, -10 * q) * Math.sin((q * 10 - .75) * 2 * Math.PI / 3) + 1;   // раскачивается вокруг цели 3-4 раза и затухает
const FEELS = {
  smooth: { out: cubicOut, io: cubicIO, soft: cosSoft, back: overshoot },                                                   // как всегда
  spring: { out: cubicOut, io: cubicIO, soft: cosSoft, back: elastic },                                                     // всё, что «выпрыгивает», пружинит
  snap:   { out: q => 1 - Math.pow(1 - q, 7), io: q => q < .5 ? 8 * Math.pow(q, 4) : 1 - 8 * Math.pow(1 - q, 4), soft: q => q * q * q * (q * (6 * q - 15) + 10),
            back: q => 1 + 1.1 * Math.pow(q - 1, 3) + .4 * Math.pow(q - 1, 2) },                                           // почти мгновенный рывок и короткая посадка
  mech:   { out: lin, io: lin, soft: lin, back: lin },                                                                      // ровно, без разгона и перелёта: бумажные куклы на палочках, лента
};
const FEEL = FEELS[MO.feel] || FEELS.smooth;
const out = q => FEEL.out(q), io = q => FEEL.io(q), soft = q => FEEL.soft(q), back = q => FEEL.back(q);
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
  // толщина обводки из манеры: только тёмный контур, широкие штрихи (брови, лямки, руки) — это форма, а не линия
  if (MN.line !== 1 && attrs.stroke === INK && attrs['stroke-width'] <= 12) e.setAttribute('stroke-width', num(attrs['stroke-width'] * MN.line));
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
  markChange(t0, dur);
  return e;
}
const show =(e, t0, dur = .2, ease = lin) => tw(e, { o: 1 }, t0, dur, ease);
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
  markChange(t0, dur);
}

// смена картинки на часах бита: по этим моментам проверка находит застывшие куски. Долгое движение отмечается каждую секунду: пока оно идёт, картинка живёт.
// Субтитры, обновление героя (CUR.quiet) и фон на tick сменой не считаются.
function markChange(t0, dur = 0) {
  if (!CUR || CUR.quiet) return;
  const end = t0 + Math.min(dur, 600);
  for (let t = t0; t < end; t += 1) CUR.changes.push(t);
  CUR.changes.push(end);
}

// tick(f): f(t) на каждом кадре со временем бита t (секунды). Бит не растягивает — для постоянного движения: качание, вращение, мерцание
function tick(f) { CUR.ticks.push(f); }

// звуковой эффект на часах бита; файл — sfx/<имя>.mp3; громкость 1 — обычная (в смеси половина от голоса)
function sfx(_beat, t, name, vol = 1) { if (CUR) CUR.sfx.push({ t, name, vol }); }

// панель текущего бита (группа SVG, которую показывают только пока идёт бит)
const panel = () => CUR.world;                                      // слой сцены: его двигает камера; субтитры лежат в CUR.fixed и стоят на месте

// ---------- сборка эпизода ----------
function buildBeats(defs) {
  const svg = document.getElementById('mm-svg');
  let start = 0;
  defs.forEach(([id, title, run, extra = {}], idx) => {
    const tm = (window.TIMINGS || {})[id];
    if (!tm) throw new Error(`Для бита «${id}» нет времён озвучки (timings): запустите озвучку или сборку`);
    const pre = extra.pre || 0;
    const p = mk('g', { display: 'none' }, svg), art = mk('g', {}, p), world = mk('g', {}, art), fixed = mk('g', {}, p);   // art стоит на месте: на нём фильтр манеры, камера двигает world
    dress(art);
    CUR = { id, title, panel: p, world, fixed, idx, els: new Set(), progs: [], ticks: [], sfx: [], changes: [], end: 0, pre, dur: tm.dur, start };
    BEAT_ID = id;
    // m('метка', сдвиг): время начала слова после [[метка]] на часах бита (с опережением LEAD)
    const m = (name, off = 0) => {
      if (!(name in tm.marks)) throw new Error(`В бите «${id}» нет метки «${name}»`);
      return Math.max(0, tm.marks[name] + pre + off - LEAD);
    };
    run(m, tm.dur);
    // переход в этот бит и движение камеры: из стиля по кругу или явно в третьем элементе бита ({ trans: 'flash', cam: 'in' })
    CUR.trans = extra.trans || (idx > 0 && MO.trans.length ? MO.trans[(idx - 1) % MO.trans.length] : 'cut');
    CUR.cam = extra.cam || (MO.cam.length ? MO.cam[idx % MO.cam.length] : 'none');
    if (CUR.trans === 'flash' || CUR.trans === 'dip') CUR.ov = rect(p, -20, -20, W + 40, H + 40, { fill: CUR.trans === 'flash' ? '#fff' : '#000', opacity: 0 });
    if (CUR.trans === 'whip' || CUR.trans === 'push' || CUR.trans === 'zoom') CUR.sfx.push({ t: 0, name: 'whoosh', vol: .3 });
    CUR.len = Math.max(pre + tm.dur, CUR.end) + FX.hold;
    start += CUR.len;
    BEAT_LIST.push(CUR);
    CUR = null;
  });
  return start;
}

function evalBeat(b, lt, leave) {
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
  motion(b, lt, leave);
}

// камера и переход бита: преобразование слоя сцены (субтитры не двигаются). leave — как уходит предыдущая сцена при переходе {x, y}
function motion(b, lt, leave) {
  const w = b.world;
  if (window.__mmNoFx) { w.removeAttribute('transform'); w.removeAttribute('opacity'); if (b.ov) b.ov.setAttribute('opacity', 0); return; }   // проверка раскладки идёт без камеры
  const A = MO.camAmp, q = soft(clamp01(lt / b.len)), u = clamp01(lt / MO.transDur), e = out(u);
  let k = 1, dx = 0, ex = leave ? leave.x : 0, ey = leave ? leave.y : 0, op = 1;
  if (b.cam === 'in') k = 1 + A * q; else if (b.cam === 'out') k = 1 + A * (1 - q);
  else if (b.cam === 'left' || b.cam === 'right') { k = 1 + A; dx = (b.cam === 'left' ? -1 : 1) * A * W * .45 * (2 * q - 1); }
  if (!leave && u < 1) {
    if (b.trans === 'whip') ex = W * .55 * (1 - e);
    else if (b.trans === 'push') ey = H * .3 * (1 - e);
    else if (b.trans === 'zoom') { k *= 1 + .2 * (1 - e); op = .35 + .65 * e; }
  }
  if (b.ov) b.ov.setAttribute('opacity', u < 1 ? (b.trans === 'flash' ? .9 : 1) * Math.pow(1 - u, 1.6) : 0);
  const tr = [];
  if (ex || ey) tr.push(`translate(${num(ex)} ${num(ey)})`);
  if (k !== 1 || dx) tr.push(`translate(${num(CX + dx)} ${num(H / 2)}) scale(${num(k)}) translate(${-CX} ${-H / 2})`);
  if (tr.length) w.setAttribute('transform', tr.join(' ')); else w.removeAttribute('transform');
  if (op < 1) w.setAttribute('opacity', num(op)); else w.removeAttribute('opacity');
}
let shown = [];
// анимация рывками: время кадра падает на ступень, кадры внутри ступени совпадают (рендер их не снимает, см. план_съёмки в render.py)
const snap = t => MN.step > 0 ? Math.floor(t * MN.step + 1e-6) / MN.step : t;
function renderAt(t) {
  t = snap(t);
  mannerFrame(t);
  let bi = BEAT_LIST.findIndex(x => t < x.start + x.len);
  if (bi < 0) bi = BEAT_LIST.length - 1;
  const b = BEAT_LIST[bi], lt = Math.min(t - b.start, b.len), u = clamp01(lt / MO.transDur);
  // во время перехода под новой сценой видна уходящая (рывок и сдвиг двигают обе, зум — перекрёстное затухание)
  const prev = bi > 0 && u < 1 && !window.__mmNoFx && (b.trans === 'whip' || b.trans === 'push' || b.trans === 'zoom') ? BEAT_LIST[bi - 1] : null;
  const want = prev ? [prev, b] : [b];
  shown.forEach(x => { if (!want.includes(x)) x.panel.setAttribute('display', 'none'); });
  want.forEach(x => { if (!shown.includes(x)) x.panel.setAttribute('display', 'inline'); });
  shown = want;
  if (prev) {
    const e = out(u);
    BEAT_ID = prev.id;
    evalBeat(prev, prev.len, { x: b.trans === 'whip' ? -W * .35 * e : 0, y: b.trans === 'push' ? -H * .2 * e : 0 });
  }
  BEAT_ID = b.id;
  evalBeat(b, lt);
}

// описание эпизода для рендера и озвучки: длительность, биты (где начинается голос), звуковые эффекты
function manifest() {
  const total = BEAT_LIST.reduce((s, b) => s + b.len, 0);
  return {
    w: W, h: H, duration: total, step: MN.step,
    beats: BEAT_LIST.map(b => ({ id: b.id, start: b.start, len: b.len, voice_at: b.start + b.pre, voice_dur: b.dur, changes: [...new Set(b.changes.map(num))].sort((p, q) => p - q) })),
    sfx: BEAT_LIST.flatMap(b => b.sfx.map(s => ({ t: b.start + s.t, name: s.name, vol: s.vol }))),
  };
}

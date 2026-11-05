/* kit.js — базовые «кубики» для сцен: смена планов, крупные слова, ярлыки, штампы, счётчики, маркер, иконки.
   Всё рисуется кодом и зависит только от времени бита. Цвета и шрифты берутся из стиля (палитра и шрифты в TOML). */
'use strict';

const PAL = Object.assign({ dark: '#0b1220', light: '#f1f5f9', red: '#ff3b3b', accent: '#38bdf8', muted: '#94a3b8', mark: '#ffd23f',
  green: '#22c55e', ink: '#12141c', sea: '#0c4a6e', steel: '#94a3b8' }, STYLE.palette);
const DARK = PAL.dark, LIGHT = PAL.light, RED = PAL.red, ACCENT = PAL.accent, MUTED = PAL.muted, MARK = PAL.mark,
  GREEN = PAL.green, INK = PAL.ink, SEA = PAL.sea, STEEL = PAL.steel;
const FONTS = Object.assign({ display_stack: '"Oswald", "Arial Narrow", sans-serif', mono: 'Menlo, "SF Mono", "Courier New", monospace' }, STYLE.fonts);
const SANS = FONTS.display_stack, MONO = FONTS.mono;

// ширина текста в пикселях: нужна, чтобы подгонять слова под безопасную зону
const MEASURE = document.createElement('canvas').getContext('2d');
const inkW = (str, size, font = SANS, weight = 600) => { MEASURE.font = `${weight} ${size}px ${font}`; return MEASURE.measureText(str).width; };

// ---------- смена планов ----------
// shot(панель, от, до, {bg, whip, swipe}): полноэкранный кадр, виден с t0 до t1; whip — въезд сбоку с размытием, swipe — снизу, как лента
let fxN = 0;
function shot(p, t0, t1, { bg, whip = false, swipe = false } = {}) {
  const g = G(p, { o: 0 });
  if (bg) rect(g, -20, -20, W + 40, H + 40, { fill: bg });
  if (t0 <= .01) put(g, { o: 1 }); else show(g, t0, .01, lin);          // первый кадр бита на экране с нулевой секунды
  if (t1 !== undefined) hide(g, t1 + .28, .01, lin);                    // старый кадр уходит, когда новый уже доехал
  const slide = (dir, dur, sound) => {
    const id = 'mmfx' + (++fxN), f = mk('filter', { id, x: dir === 'x' ? '-30%' : 0, y: dir === 'x' ? 0 : '-30%', width: dir === 'x' ? '160%' : '100%', height: dir === 'x' ? '100%' : '160%' }, mk('defs', {}, g));
    const blur = mk('feGaussianBlur', { stdDeviation: '0 0' }, f);
    prog(q => {
      put(g, dir === 'x' ? { x: W * .6 * (1 - q) } : { y: H * (1 - q) });
      if (q < 1) { blur.setAttribute('stdDeviation', dir === 'x' ? `${(1 - q) * 60} 0` : `0 ${(1 - q) * 50}`); g.setAttribute('filter', `url(#${id})`); }
      else g.removeAttribute('filter');                                 // фильтр, оставленный на кадре, замедляет рендер
    }, t0, dur, out);
    sfx(BEAT_ID, t0, 'whoosh', sound);
  };
  if (whip) slide('x', .26, .5);
  if (swipe) slide('y', .2, swipe === 'quiet' ? .18 : .4);
  return g;
}

// ---------- входы: разные способы появления ----------
// Стиль (анимации → входы) задаёт набор; слова, ярлыки и иконки без явного enter берут из него по кругу (со сдвигом по номеру бита), так что
// соседние надписи появляются по-разному и два бита подряд не выглядят одинаково. Явно: word(…, { enter: 'drop' }). Штамп всегда «хлопает»,
// если enter не задан. pop — как раньше (масштаб + прозрачность).
const bounce = q => { const n = 7.5625, d = 2.75; if (q < 1 / d) return n * q * q; if (q < 2 / d) return n * (q -= 1.5 / d) * q + .75; if (q < 2.5 / d) return n * (q -= 2.25 / d) * q + .9375; return n * (q -= 2.625 / d) * q + .984375; };
const ENTERS = {
  pop:   null,
  drop:  { dur: .42, ease: bounce, from: f => ({ y: f.y - 280, o: 0 }) },
  left:  { dur: .3, ease: out, from: f => ({ x: f.x - 460, o: 0 }) },
  right: { dur: .3, ease: out, from: f => ({ x: f.x + 460, o: 0 }) },
  rise:  { dur: .3, ease: out, from: f => ({ y: f.y + 170, o: 0 }) },
  zoom:  { dur: .2, ease: out, from: f => ({ s: f.s * 2.6, o: 0 }) },
  spin:  { dur: .34, ease: back, from: f => ({ r: f.r - 28, s: f.s * .5, o: 0 }) },
};
function pickEnter(kind) {
  if (kind) return kind;
  const L = MO.enters;
  if (!L.length || !CUR) return 'pop';
  CUR.enterN = (CUR.enterN || 0) + 1;
  return L[(CUR.idx * 3 + CUR.enterN) % L.length];
}
// enter(e, kind, t0, fin, own): элемент приходит к конечному состоянию fin {x, y, s, r} с момента t0; own — длительность и плавность для pop
function enter(e, kind, t0, fin, own = {}) {
  const k = ENTERS[kind];
  if (k === undefined) throw new Error(`Нет входа «${kind}»; есть: ${Object.keys(ENTERS).join(', ')}`);
  fin = Object.assign({ x: 0, y: 0, s: 1, r: 0 }, fin);
  if (!k) return tw(e, { s: fin.s, o: 1 }, t0, own.dur, own.ease);
  put(e, k.from(fin));
  tw(e, { x: fin.x, y: fin.y, s: fin.s, r: fin.r }, t0, k.dur, k.ease);
  return tw(e, { o: 1 }, t0, Math.min(.12, k.dur), lin);
}

// ---------- текст ----------
// крупное слово капсом; слишком широкое уменьшается, чтобы не вылезти за безопасную зону
function word(g, str, x, y, t0, { size = 120, fill = DARK, anchor = 'middle', stroke, dur = .22, from = .82, maxW = 660, enter: how } = {}) {
  size = Math.min(size, size * maxW / inkW(str.toUpperCase(), size));
  const e = G(g, { x, y, s: from, o: 0 });
  const t = T(e, str.toUpperCase(), { x: 0, y: 0, size, fill, weight: 600, anchor });
  if (stroke) { t.setAttribute('stroke', stroke); t.setAttribute('stroke-width', size / 14); t.setAttribute('paint-order', 'stroke'); t.setAttribute('stroke-linejoin', 'round'); }
  if (t0 <= .01) put(e, { s: 1, o: 1 }); else enter(e, pickEnter(how), t0, { x, y }, { dur, ease: out });
  return e;
}

// ярлык: заглавные буквы на сплошном блоке
function label(g, str, x, y, t0, { size = 40, fill = DARK, colour = LIGHT, anchor = 'middle', pad = 18, enter: how } = {}) {
  const w = inkW(str.toUpperCase(), size) + pad * 2, x0 = anchor === 'middle' ? -w / 2 : anchor === 'end' ? -w : 0;
  const e = G(g, { x, y, s: .85, o: 0 });
  rect(e, x0, -size * .95, w, size * 1.3, { fill, rx: 4 });
  T(e, str.toUpperCase(), { x: x0 + pad, y: 0, size, fill: colour, weight: 600 });
  if (t0 <= .01) put(e, { s: 1, o: 1 }); else enter(e, pickEnter(how), t0, { x, y }, { dur: .18, ease: out });
  return e;
}

// резиновый штамп: с хлопком (звук bang)
function stamp(g, str, x, y, t0, { size = 110, colour = RED, r = -9, enter: how = 'pop' } = {}) {
  const w = inkW(str, size) + 60, e = G(g, { x, y, r, s: 1.7, o: 0 });
  rect(e, -w / 2, -size * .85, w, size * 1.2, { fill: 'none', stroke: colour, 'stroke-width': size / 11, rx: 10 });
  T(e, str, { y: size * .3, size, fill: colour, weight: 600, anchor: 'middle' });
  enter(e, how, t0, { x, y, r }, { dur: .16, ease: out });
  sfx(BEAT_ID, t0, 'bang', 1.4);
  return e;
}

// число, которое набегает от нуля до n; пробел как разделитель тысяч
const fmt = n => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
function counter(g, n, x, y, t0, { size = 90, fill = DARK, anchor = 'middle', dur = 1.1, pre = '', ticks = true, maxW = 660 } = {}) {
  size = Math.min(size, size * maxW / inkW(pre + fmt(n), size));
  const t = T(g, pre + '0', { x, y, size, fill, weight: 600, anchor, o: 0 });
  show(t, t0, .1, lin);
  prog(q => { t.textContent = pre + fmt(n * q); }, t0, dur, out);
  if (ticks) for (let k = 0; k < 6; k++) sfx(BEAT_ID, t0 + k * dur / 6, 'tick', .45);
  return t;
}

// жёлтый маркер, прочерченный под текстом
function marker(g, x, y, w, h, t0, dur = .3) {
  const r = rect(g, x, y, 0, h, { fill: MARK });
  prog(q => r.setAttribute('width', w * q), t0, dur, out);
  return r;
}

// ---------- иконки (набор Phosphor, fill-вариант, см. icons.js) ----------
function ico(g, name, x, y, size, fill, t0, { from = .5, dur = .25, enter: how } = {}) {
  if (!ICONS[name]) throw new Error(`Нет иконки «${name}»; доступные: ${Object.keys(ICONS).join(', ')}`);
  const e = G(g, { x, y, s: from, o: 0 });
  mk('svg', { x: -size / 2, y: -size / 2, width: size, height: size, viewBox: '0 0 256 256', fill }, e).innerHTML = ICONS[name];
  if (t0 === undefined) put(e, { s: 1, o: 1 }); else enter(e, pickEnter(how), t0, { x, y }, { dur, ease: out });
  return e;
}

// сетка из n иконок: cols в ряд, от (x, y), клетка c, появляются по очереди за dur
function icons(g, name, n, cols, x, y, c, colour, t0, dur = .8) {
  const res = [];
  for (let i = 0; i < Math.ceil(n); i++) {
    res.push(ico(g, name, x + (i % cols) * c + c / 2, y + Math.floor(i / cols) * c + c / 2, c * .86, colour, t0 + dur * i / Math.ceil(n), { from: .3, dur: .14 }));
  }
  return res;
}

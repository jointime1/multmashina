/* scenery.js — декорации и мелкий реквизит: комнаты с лампой и неоном, офис, зерно с виньеткой, бумага, искры, облако мыслей и т. п.

   Комнаты берутся из стиля (раздел «комнаты» в TOML): room(g, 'подвал', {вывеска…}) — готовый пресет с точечными правками.
   Вся картинка рисуется кодом и зависит только от времени бита. */
'use strict';

let sceneN = 0;
const gdefs = g => mk('defs', {}, g);
const gstops = (e, stops) => stops.forEach(([o, c, a = 1]) => mk('stop', { offset: o, 'stop-color': c, 'stop-opacity': a }, e));
function lgrad(g, stops) { const id = 'mmlg' + (++sceneN); gstops(mk('linearGradient', { id, x1: 0, y1: 0, x2: 0, y2: 1 }, gdefs(g)), stops); return `url(#${id})`; }
function rgrad(g, stops) { const id = 'mmrg' + (++sceneN); gstops(mk('radialGradient', { id }, gdefs(g)), stops); return `url(#${id})`; }
const mixWhite = (hex, k) => '#' + [1, 3, 5].map(i => Math.round(parseInt(hex.slice(i, i + 2), 16) * (1 - k) + 255 * k).toString(16).padStart(2, '0')).join('');

// неоновая вывеска: тёмная плашка и светящийся текст (светлая сердцевина, цветное свечение — так буквы читаются)
function neonSign(g, text, x, y, size, col) {
  text = text.toUpperCase();
  const w = inkW(text, size) + 76, s = G(g, { x, y });
  rect(s, -w / 2, -size * .95, w, size * 1.5, { fill: '#10131b', stroke: '#2e3544', 'stroke-width': 5, rx: 16 });
  const t = T(s, text, { x: 0, y: size * .2, size, fill: mixWhite(col, .62), weight: 600, anchor: 'middle' });
  t.style.filter = `drop-shadow(0 0 9px ${col}) drop-shadow(0 0 2px ${col})`;
  return s;
}

// комната с лампой на шнуре: облупленная стена, трубы, пол в лужах, тёплое свечение; spec — имя пресета из стиля или объект
function room(g, spec, over = {}) {
  const base = typeof spec === 'string' ? (STYLE.rooms || {})[spec] : spec;
  if (!base) throw new Error(`Нет комнаты «${spec}» в стиле. Есть: ${Object.keys(STYLE.rooms || {}).join(', ') || '(пусто)'}`);
  const { wall = '#3b4659', wall2 = '#212939', floor = '#232735', hz = 900, lampX = 640, glow = '#ffb347', sign, signCol = '#ffb347',
    signX = CX, signY = 270, signSize = 64, pipes = true, seed = 4 } = Object.assign({}, base, over);
  const Rn = seeded(seed);
  rect(g, -20, -20, W + 40, hz + 20, { fill: lgrad(g, [[0, wall], [1, wall2]]) });
  for (let i = 0; i < 14; i++) {                                            // облупившаяся штукатурка
    const x = Rn() * W, y = 60 + Rn() * (hz - 200), w = 70 + Rn() * 170, h = 40 + Rn() * 110;
    rect(g, x, y, w, h, { fill: 'rgba(255,255,255,.04)', rx: 18, transform: `rotate(${(Rn() - .5) * 16} ${x} ${y})` });
  }
  for (let i = 0; i < 7; i++) rect(g, Rn() * W, -10, 12 + Rn() * 16, 90 + Rn() * 330, { fill: 'rgba(0,0,0,.22)', rx: 8 });   // подтёки
  if (pipes) {
    rect(g, -20, 356, W + 40, 34, { fill: '#38455a' }); rect(g, -20, 362, W + 40, 8, { fill: 'rgba(255,255,255,.13)' });
    rect(g, -20, 420, W + 40, 22, { fill: '#303b4d' });
    rect(g, 52, -20, 30, hz + 20, { fill: '#38455a' }); rect(g, 58, -20, 7, hz + 20, { fill: 'rgba(255,255,255,.13)' });
    [380, 560, 740].forEach(y => rect(g, 46, y, 42, 16, { fill: '#2a3444', rx: 4 }));
  }
  rect(g, -20, hz, W + 40, H - hz + 20, { fill: lgrad(g, [[0, floor], [1, '#090b10']]) });
  rect(g, -20, hz - 6, W + 40, 12, { fill: '#0b0e15' });
  let d = '';
  for (let x = -600; x <= 1500; x += 150) d += `M ${CX} ${hz} L ${x} ${H}`;
  mk('path', { d, stroke: 'rgba(255,255,255,.05)', 'stroke-width': 3, fill: 'none' }, g);
  for (let i = 0; i < 4; i++) mk('ellipse', { cx: 100 + Rn() * 700, cy: hz + 90 + Rn() * 380, rx: 80 + Rn() * 120, ry: 12 + Rn() * 14, fill: glow, opacity: .09 }, g);
  mk('circle', { cx: lampX, cy: 250, r: 640, fill: rgrad(g, [[0, glow, .46], [1, glow, 0]]) }, g);   // свет лампы
  rect(g, lampX - 2, -20, 4, 210, { fill: '#0b0e15' });
  mk('path', { d: `M ${lampX - 72} 252 L ${lampX - 26} 188 L ${lampX + 26} 188 L ${lampX + 72} 252 Z`, fill: '#202938', stroke: '#0b0e15', 'stroke-width': 5, 'stroke-linejoin': 'round' }, g);
  mk('circle', { cx: lampX, cy: 258, r: 22, fill: '#ffe9a8' }, g);
  if (sign) neonSign(g, sign, signX, signY, signSize, signCol);
}

// большой открытый офис: потолочные светильники, окна с вечерним городом, ряд столов с мониторами, вывеска компании
function office(g, o = {}) {
  const Rn = seeded(8), hz = 930, name = o.name || 'Компания', signCol = o.signCol || '#e879f9';
  // цвета берутся из раздела «офис» стиля
  const C = Object.assign({ wall: '#2c3748', wall2: '#1b2230', ceiling: '#10141c', floor: '#1a2030', glass1: '#14203a', glass2: '#41567f', bldg: '#0e1626' }, STYLE.office);
  rect(g, -20, -20, W + 40, hz + 20, { fill: lgrad(g, [[0, C.wall], [1, C.wall2]]) });
  rect(g, -20, -20, W + 40, 250, { fill: C.ceiling });
  for (let i = 0; i < 3; i++) {
    const x = 80 + i * 280;
    mk('path', { d: `M ${x} 90 L ${x - 40} 232 L ${x + 260} 232 L ${x + 220} 90 Z`, fill: 'rgba(200,225,255,.07)' }, g);
    rect(g, x, 60, 220, 30, { fill: '#eaf3ff', rx: 8 });
  }
  for (let i = 0; i < 3; i++) {
    const x = 40 + i * 290;
    rect(g, x, 440, 250, 400, { fill: lgrad(g, [[0, C.glass1], [1, C.glass2]]), stroke: '#0c1018', 'stroke-width': 8, rx: 6 });
    for (let k = 0; k < 5; k++) {
      const bx = x + 10 + k * 46, bw = Math.min(34 + Rn() * 34, x + 242 - bx), bh = 70 + Rn() * 190;
      rect(g, bx, 832 - bh, bw, bh, { fill: C.bldg });
      for (let j = 0; j < Math.floor(bh / 38); j++) if (Rn() < .5) rect(g, bx + 6 + (Rn() < .5 ? 0 : 14), 832 - bh + 10 + j * 38, 10, 14, { fill: '#ffd27a', opacity: .8 });
    }
    rect(g, x + 121, 440, 8, 400, { fill: '#0c1018' });
  }
  neonSign(g, name, CX, 355, 100, signCol);
  rect(g, -20, hz, W + 40, H - hz + 20, { fill: lgrad(g, [[0, C.floor], [1, '#090b10']]) });
  for (let i = 0; i < 3; i++) {
    const x = 40 + i * 290;
    rect(g, x, 836, 240, 30, { fill: '#5b4636', stroke: INK, 'stroke-width': 5, rx: 4 });
    rect(g, x + 55, 730, 130, 100, { fill: '#0e1420', stroke: INK, 'stroke-width': 5, rx: 8 });
    rect(g, x + 64, 739, 112, 70, { fill: '#9bd5ff', opacity: .85, rx: 4 });
    rect(g, x + 112, 830, 16, 10, { fill: INK });
  }
}

// зерно и виньетка поверх всех кадров бита (создаётся последним, до субтитров); включаются в стиле: эффекты → зерно, виньетка
function finish(p) {
  const g = G(p, {});
  if (FX.vignette > 0) rect(g, -20, -20, W + 40, H + 40, { fill: rgrad(g, [[.5, '#000', 0], [1, '#000', FX.vignette]]) });
  if (FX.grain) {
    const id = 'mmgr' + (++sceneN), pat = mk('pattern', { id, width: 256, height: 256, patternUnits: 'userSpaceOnUse' }, gdefs(g));
    mk('image', { href: 'grain.png', width: 256, height: 256 }, pat);
    rect(g, 0, 0, W, H, { fill: `url(#${id})` });
  }
  return g;
}

// ---------- мелкий реквизит ----------
// тонкая сетка на фоне кадра
function bgGrid(g, colour = 'rgba(148,163,184,.07)') {
  let d = '';
  for (let x = 0; x <= W; x += 100) d += `M${x} 0V${H}`;
  for (let y = 0; y <= H; y += 100) d += `M0 ${y}H${W}`;
  mk('path', { d, fill: 'none', stroke: colour, 'stroke-width': 2 }, g);
}

// небольшая пометка в левом верхнем углу (например, «история вымышленная»)
function note(g, t0, str) {
  const t = T(g, str.toUpperCase(), { x: 50, y: 175, size: 26, fill: MUTED, weight: 500, o: 0 });
  t.setAttribute('letter-spacing', '.12em');
  show(t, t0, .3, lin);
  return t;
}

// покачивание на месте: y0 ± amp с периодом period на отрезке t0..t0+dur
const bob = (e, y0, amp, period, t0, dur) => dur <= .05 ? null : prog(q => put(e, { y: y0 + amp * Math.sin(q * dur / period * Math.PI * 2) }), t0, dur, lin);

// красная линия поверх (зачёркивание, крест)
function strike(g, x1, y1, x2, y2, t0, { w = 28, colour = RED, dur = .25 } = {}) {
  const p = path(g, `M${x1} ${y1}L${x2} ${y2}`, { fill: 'none', stroke: colour, 'stroke-width': w, 'stroke-linecap': 'round' }, { d: 0 });
  draw(p, t0, dur, out);
  sfx(BEAT_ID, t0, 'tick', .8);
  return p;
}

// искры сварки: частицы летят вверх-в стороны и падают, всё от времени бита
function sparks(g, x, y, t0, t1, { n = 34, seed = 5 } = {}) {
  const R = seeded(seed), grp = G(g, {}), ps = [];
  for (let i = 0; i < n; i++) ps.push({ a: -Math.PI * (.12 + R() * .76), v: 220 + R() * 420, ph: R(), life: .45 + R() * .45, el: mk('circle', { r: 3 + R() * 4, fill: R() < .5 ? '#ffd23f' : '#ff8a3d' }, grp) });
  const core = mk('circle', { cx: x, cy: y, r: 16, fill: '#fff7c2' }, grp);
  prog(q => {
    const t = t0 + q * (t1 - t0);
    ps.forEach(p => {
      const age = (((t / p.life) + p.ph) % 1) * p.life;
      p.el.setAttribute('cx', x + Math.cos(p.a) * p.v * age); p.el.setAttribute('cy', y + Math.sin(p.a) * p.v * age + 760 * age * age);
      p.el.setAttribute('opacity', 1 - age / p.life);
    });
    core.setAttribute('r', 13 + 6 * Math.abs(Math.sin(t * 41)));
  }, t0, t1 - t0, lin);
  return grp;
}

// облако мыслей: несколько кругов и два пузыря в сторону головы
function cloud(g, x, y, w, h, t0) {
  const e = G(g, { x, y, s: .6, o: 0 });
  [[-.28, .05, .3], [0, -.18, .34], [.28, .02, .3], [-.12, .22, .28], [.14, .24, .28]].forEach(([dx, dy, r]) => mk('circle', { cx: dx * w, cy: dy * h, r: r * h * 1.05, fill: '#f1f5f9', stroke: INK, 'stroke-width': 6 }, e));
  rect(e, -w * .38, -h * .22, w * .76, h * .5, { fill: '#f1f5f9' });
  mk('circle', { cx: -w * .34, cy: h * .78, r: 26, fill: '#f1f5f9', stroke: INK, 'stroke-width': 6 }, e);
  mk('circle', { cx: -w * .44, cy: h * 1.06, r: 14, fill: '#f1f5f9', stroke: INK, 'stroke-width': 5 }, e);
  tw(e, { s: 1, o: 1 }, t0, .3, back);
  return e;
}

// бумага с заголовком и красной печатью (приказ, справка, договор)
function paper(g, x, y, w, h, title, r = 0) {
  const e = G(g, { x, y, r });
  rect(e, -w / 2, -h / 2, w, h, { fill: '#f1f5f9', stroke: INK, 'stroke-width': 6, rx: 8 });
  T(e, title, { x: 0, y: -h / 2 + 54, size: 44, fill: '#1f2937', weight: 600, anchor: 'middle' });
  for (let i = 0; i < 5; i++) rect(e, -w / 2 + 24, -h / 2 + 90 + i * 30, (w - 48) * (.92 - (i % 3) * .15), 10, { fill: '#94a3b8', rx: 5 });
  mk('circle', { cx: w / 2 - 56, cy: h / 2 - 56, r: 34, fill: 'none', stroke: RED, 'stroke-width': 7 }, e);
  return e;
}

// окно терминала и строки в нём
function term(g, x, y, w, h, title, t0) {
  const e = G(g, { x, y, o: 0 });
  rect(e, 0, 0, w, h, { fill: '#020617', stroke: '#1e293b', 'stroke-width': 4, rx: 26 });
  [RED, MARK, GREEN].forEach((c, i) => mk('circle', { cx: 44 + i * 40, cy: 44, r: 12, fill: c }, e));
  T(e, title, { x: w - 70, y: 54, size: 28, fill: MUTED, font: MONO, weight: 400, anchor: 'end' });
  tw(e, { o: 1 }, t0, .2, out);
  return e;
}
function termLine(e, str, x, y, t0, colour = LIGHT, size = 32) {
  const t = T(e, str, { x, y, size, fill: colour, font: MONO, weight: 700, o: 0 });
  show(t, t0, .08, lin);
  sfx(BEAT_ID, t0, 'tick', .5);
  return t;
}

/* scenery.js — декорации и мелкий реквизит: комнаты с лампой и неоном, офис, зерно с виньеткой, бумага, искры, облако мыслей и т. п.

   Комнаты берутся из стиля (раздел «комнаты» в TOML): room(g, 'подвал', {вывеска…}) — готовый пресет с точечными правками.
   Вся картинка рисуется кодом и зависит только от времени бита. */
'use strict';

let sceneN = 0;
const gdefs = g => mk('defs', {}, g);
const gstops = (e, stops) => stops.forEach(([o, c, a = 1]) => mk('stop', { offset: o, 'stop-color': c, 'stop-opacity': a }, e));
// плоский цвет (манера → плоско): вместо градиента — первый его цвет, прозрачный градиент просто исчезает
const flatFill = ([, c, a = 1]) => a <= 0 ? 'none' : a >= 1 ? c : `rgba(${[1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16)).join(',')},${a * .5})`;
function lgrad(g, stops) { if (MN.flat) return flatFill(stops[0]); const id = 'mmlg' + (++sceneN); gstops(mk('linearGradient', { id, x1: 0, y1: 0, x2: 0, y2: 1 }, gdefs(g)), stops); return `url(#${id})`; }
function rgrad(g, stops) { if (MN.flat) return flatFill(stops[0]); const id = 'mmrg' + (++sceneN); gstops(mk('radialGradient', { id }, gdefs(g)), stops); return `url(#${id})`; }
const mixWhite = (hex, k) => '#' + [1, 3, 5].map(i => Math.round(parseInt(hex.slice(i, i + 2), 16) * (1 - k) + 255 * k).toString(16).padStart(2, '0')).join('');

// неоновая вывеска: тёмная плашка и светящийся текст (светлая сердцевина, цветное свечение — так буквы читаются)
function neonSign(g, text, x, y, size, col) {
  text = text.toUpperCase();
  const w = inkW(text, size) + 76, s = G(g, { x, y });
  rect(s, -w / 2, -size * .95, w, size * 1.5, { fill: '#10131b', stroke: '#2e3544', 'stroke-width': 5, rx: 16 });
  const t = T(s, text, { x: 0, y: size * .2, size, fill: mixWhite(col, .62), weight: 600, anchor: 'middle' });
  if (!MN.tones.length) t.style.filter = `drop-shadow(0 0 9px ${col}) drop-shadow(0 0 2px ${col})`;   // свечение после порога тонов — клякса поверх букв
  return s;
}

// комната с лампой на шнуре: облупленная стена, трубы, пол в лужах, тёплое свечение; spec — имя пресета из стиля или объект
function room(g, spec, over = {}) {
  const base = typeof spec === 'string' ? (STYLE.rooms || {})[spec] : spec;
  if (!base) throw new Error(`Нет комнаты «${spec}» в стиле. Есть: ${Object.keys(STYLE.rooms || {}).join(', ') || '(пусто)'}`);
  g.setAttribute('data-bg', typeof spec === 'string' ? spec : 'комната');          // по этой метке проверка считает, сколько длится один фон
  const { wall = '#3b4659', wall2 = '#212939', floor = '#232735', floor2 = '#090b10', hz = 900, lampX = 640, glow = '#ffb347', sign, signCol = '#ffb347',
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
  rect(g, -20, hz, W + 40, H - hz + 20, { fill: lgrad(g, [[0, floor], [1, floor2]]) });
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

// цвета офиса и всех локаций: раздел «офис» стиля, поверх него — настройки вызова
const indoors = o => Object.assign({ wall: '#2c3748', wall2: '#1b2230', ceiling: '#10141c', floor: '#1a2030', floor2: '#090b10', glass1: '#14203a', glass2: '#41567f', bldg: '#0e1626' }, STYLE.office, o);

// большой открытый офис: потолочные светильники, окна с вечерним городом, ряд столов с мониторами, вывеска компании
function office(g, o = {}) {
  g.setAttribute('data-bg', 'офис');
  const Rn = seeded(8), hz = 930, name = o.name || 'Компания', signCol = o.signCol || '#e879f9';
  const C = indoors(o);
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
  rect(g, -20, hz, W + 40, H - hz + 20, { fill: lgrad(g, [[0, C.floor], [1, C.floor2]]) });
  for (let i = 0; i < 3; i++) {
    const x = 40 + i * 290;
    rect(g, x, 836, 240, 30, { fill: '#5b4636', stroke: INK, 'stroke-width': 5, rx: 4 });
    rect(g, x + 55, 730, 130, 100, { fill: '#0e1420', stroke: INK, 'stroke-width': 5, rx: 8 });
    rect(g, x + 64, 739, 112, 70, { fill: '#9bd5ff', opacity: .85, rx: 4 });
    rect(g, x + 112, 830, 16, 10, { fill: INK });
  }
}

// ---------- локации ----------
// Готовые места действия: street, kitchen, metro, meeting, stairs. Вызов: street(s) или street(s, { wall: '#…' }). Цвета — из раздела «офис» стиля, поэтому локация
// следует за стилем сама. Важное стоит по краям и вверху: середину кадра (y 700–1200) занимает герой. Горизонт около y=1000, у героя ориентир y≈900.
const WHITEGOODS = '#f1f5f9';                                                 // белая техника и бумага: LIGHT не подходит, в светлых стилях это цвет текста
const floorOf = (g, C, hz) => rect(g, -20, hz, W + 40, H - hz + 20, { fill: lgrad(g, [[0, C.floor], [1, C.floor2]]) });
const windowsOf = (g, Rn, x, y, w, h, gap = 54) => {
  for (let wy = y + 24; wy < y + h - 40; wy += gap) for (let wx = x + 18; wx < x + w - 34; wx += 46) rect(g, wx, wy, 24, 32, { fill: Rn() < .45 ? '#ffd27a' : 'rgba(255,255,255,.1)' });
};

// улица: небо, дома в два ряда, тротуар, фонарь
function street(g, o = {}) {
  g.setAttribute('data-bg', 'улица');
  const C = indoors(o), Rn = seeded(o.seed || 12), hz = 1010;
  rect(g, -20, -20, W + 40, hz + 20, { fill: lgrad(g, [[0, C.glass1], [1, C.glass2]]) });
  for (let x = -30; x < W;) {                                                // дальний ряд
    const w = 120 + Rn() * 110, h = 340 + Rn() * 330;
    rect(g, x, hz - h, w, h, { fill: C.bldg, opacity: .6 });
    x += w + 8;
  }
  [[-40, 300, 620], [640, 300, 760]].forEach(([x, w, h]) => {                // ближние дома по краям
    rect(g, x, hz - h, w, h, { fill: C.bldg, stroke: INK, 'stroke-width': 6 });
    windowsOf(g, Rn, x, hz - h, w, h - 140);
    rect(g, x + w / 2 - 44, hz - 124, 88, 124, { fill: C.wall2, stroke: INK, 'stroke-width': 5 });
  });
  floorOf(g, C, hz);
  rect(g, -20, hz, W + 40, 16, { fill: STEEL });                             // бордюр
  for (let x = -40; x < W; x += 230) rect(g, x, 1420, 130, 16, { fill: WHITEGOODS, opacity: .5, rx: 4 });   // разметка
  rect(g, 742, 560, 14, 450, { fill: INK });                                 // фонарь
  mk('path', { d: 'M 749 562 Q 749 500 672 506', stroke: INK, 'stroke-width': 12, fill: 'none' }, g);
  mk('circle', { cx: 668, cy: 530, r: 120, fill: rgrad(g, [[0, '#ffe9a8', .5], [1, '#ffe9a8', 0]]) }, g);
  mk('ellipse', { cx: 668, cy: 520, rx: 34, ry: 16, fill: '#ffe9a8', stroke: INK, 'stroke-width': 5 }, g);
}

// кухня: плитка, шкафчики, окно, холодильник, стол с чайником
function kitchen(g, o = {}) {
  g.setAttribute('data-bg', 'кухня');
  const C = indoors(o), hz = 1000;
  rect(g, -20, -20, W + 40, hz + 20, { fill: lgrad(g, [[0, C.wall], [1, C.wall2]]) });
  let d = '';
  for (let x = 0; x <= W; x += 90) d += `M ${x} 420 V ${hz}`;
  for (let y = 420; y <= hz; y += 90) d += `M 0 ${y} H ${W}`;
  mk('path', { d, stroke: 'rgba(255,255,255,.08)', 'stroke-width': 3, fill: 'none' }, g);
  for (let i = 0; i < 4; i++) {                                              // шкафчики
    rect(g, 30 + i * 212, 130, 204, 270, { fill: C.ceiling, stroke: INK, 'stroke-width': 6, rx: 6 });
    rect(g, 118 + i * 212, 350, 28, 10, { fill: STEEL, rx: 4 });
  }
  rect(g, 50, 450, 280, 280, { fill: lgrad(g, [[0, C.glass1], [1, C.glass2]]), stroke: INK, 'stroke-width': 8, rx: 6 });   // окно
  rect(g, 186, 450, 8, 280, { fill: INK }); rect(g, 50, 586, 280, 8, { fill: INK });
  rect(g, 660, 440, 220, 560, { fill: WHITEGOODS, stroke: INK, 'stroke-width': 7, rx: 18 });   // холодильник
  rect(g, 660, 640, 220, 7, { fill: INK }); rect(g, 682, 540, 14, 80, { fill: STEEL, rx: 6 }); rect(g, 682, 668, 14, 110, { fill: STEEL, rx: 6 });
  rect(g, -20, 830, 680, 26, { fill: '#5b4636', stroke: INK, 'stroke-width': 6 });        // столешница
  rect(g, -20, 856, 680, 150, { fill: C.ceiling, stroke: INK, 'stroke-width': 6 });
  mk('path', { d: 'M 70 830 C 60 770 88 730 130 730 C 172 730 200 770 190 830 Z', fill: STEEL, stroke: INK, 'stroke-width': 6 }, g);   // чайник
  mk('path', { d: 'M 188 790 L 238 756 L 238 776 L 192 812', fill: STEEL, stroke: INK, 'stroke-width': 6, 'stroke-linejoin': 'round' }, g);
  mk('path', { d: 'M 92 740 Q 130 690 168 740', fill: 'none', stroke: INK, 'stroke-width': 8 }, g);
  floorOf(g, C, hz);
}

// вагон метро: тёмные окна, поручни, скамья, схема над окнами
function metro(g, o = {}) {
  g.setAttribute('data-bg', 'метро');
  const C = indoors(o), hz = 1040, Rn = seeded(o.seed || 21);
  rect(g, -20, -20, W + 40, hz + 20, { fill: lgrad(g, [[0, C.wall], [1, C.wall2]]) });
  rect(g, -20, -20, W + 40, 190, { fill: C.ceiling });
  for (let i = 0; i < 2; i++) rect(g, 110 + i * 390, 70, 290, 26, { fill: '#eaf3ff', rx: 12 });
  rect(g, 90, 214, 720, 74, { fill: WHITEGOODS, stroke: INK, 'stroke-width': 5, rx: 8 });      // схема линии
  mk('path', { d: 'M 130 250 H 770', stroke: ACCENT, 'stroke-width': 9, fill: 'none' }, g);
  for (let i = 0; i < 8; i++) mk('circle', { cx: 150 + i * 86, cy: 250, r: 11, fill: WHITEGOODS, stroke: INK, 'stroke-width': 5 }, g);
  [40, 330, 620].forEach(x => {                                              // окна: тёмный тоннель и огни
    rect(g, x, 340, 240, 330, { fill: C.glass1, stroke: INK, 'stroke-width': 8, rx: 26 });
    for (let k = 0; k < 3; k++) rect(g, x + 26 + Rn() * 130, 400 + k * 90, 44 + Rn() * 40, 7, { fill: '#ffd27a', opacity: .7, rx: 3 });
  });
  rect(g, -20, 318, W + 40, 12, { fill: STEEL });                            // верхний поручень и ручки
  for (let x = 90; x < W; x += 140) mk('path', { d: `M ${x} 330 v 58 m -20 26 a 20 26 0 1 0 40 0 a 20 26 0 1 0 -40 0`, stroke: INK, 'stroke-width': 5, fill: 'none' }, g);
  rect(g, -20, 846, W + 40, 44, { fill: C.ceiling, stroke: INK, 'stroke-width': 6 });     // спинка скамьи
  rect(g, -20, 890, W + 40, 150, { fill: C.wall2, stroke: INK, 'stroke-width': 6 });
  [70, 830].forEach(x => rect(g, x - 9, 320, 18, 720, { fill: STEEL, stroke: INK, 'stroke-width': 4 }));   // стойки
  floorOf(g, C, hz);
}

// переговорка: экран с графиком, стол, стулья, жалюзи
function meeting(g, o = {}) {
  g.setAttribute('data-bg', 'переговорка');
  const C = indoors(o), hz = 960, Rn = seeded(o.seed || 33);
  rect(g, -20, -20, W + 40, hz + 20, { fill: lgrad(g, [[0, C.wall], [1, C.wall2]]) });
  rect(g, -20, -20, W + 40, 130, { fill: C.ceiling });
  for (let y = 170; y < 760; y += 34) rect(g, 680, y, 240, 22, { fill: C.glass2, stroke: INK, 'stroke-width': 3 });   // жалюзи
  rect(g, 50, 170, 590, 370, { fill: '#0e1420', stroke: INK, 'stroke-width': 8, rx: 10 });                            // экран
  rect(g, 68, 188, 554, 334, { fill: WHITEGOODS, rx: 4 });
  for (let i = 0; i < 6; i++) { const h = 60 + Rn() * 210; rect(g, 112 + i * 84, 496 - h, 54, h, { fill: i % 2 ? ACCENT : RED, stroke: INK, 'stroke-width': 4 }); }
  mk('path', { d: 'M 90 496 H 600', stroke: INK, 'stroke-width': 5, fill: 'none' }, g);
  [120, 330, 570, 780].forEach(x => mk('path', { d: `M ${x - 64} 860 V 700 Q ${x - 64} 660 ${x - 24} 660 H ${x + 24} Q ${x + 64} 660 ${x + 64} 700 V 860 Z`, fill: C.ceiling, stroke: INK, 'stroke-width': 6 }, g));   // спинки стульев
  floorOf(g, C, hz);
  mk('path', { d: 'M 90 840 H 810 L 900 1000 H 0 Z', fill: '#5b4636', stroke: INK, 'stroke-width': 7, 'stroke-linejoin': 'round' }, g);   // стол
  rect(g, -20, 1000, W + 40, 34, { fill: '#46352a', stroke: INK, 'stroke-width': 6 });
}

// лестничная клетка: ступени наверх, перила, лампа
function stairs(g, o = {}) {
  g.setAttribute('data-bg', 'лестница');
  const C = indoors(o), hz = 1060;
  rect(g, -20, -20, W + 40, hz + 20, { fill: lgrad(g, [[0, C.wall], [1, C.wall2]]) });
  rect(g, -20, 620, W + 40, 8, { fill: 'rgba(0,0,0,.25)' });                 // граница покраски стены
  for (let i = 0; i < 12; i++) {
    const x = 900 - i * 88, y = 240 + (11 - i) * 74;
    rect(g, x - 20, y, W, hz - y, { fill: i % 2 ? C.floor : C.wall2, stroke: INK, 'stroke-width': 6 });
  }
  mk('path', { d: 'M -20 1000 L 900 150', stroke: '#5b4636', 'stroke-width': 18, 'stroke-linecap': 'round', fill: 'none' }, g);   // перила
  for (let i = 0; i < 12; i++) { const x = 900 - i * 88 + 30, y = 150 + i * 78; rect(g, x, y, 8, 170, { fill: INK }); }
  rect(g, 120, -20, 4, 190, { fill: INK });
  mk('circle', { cx: 122, cy: 196, r: 26, fill: '#ffe9a8', stroke: INK, 'stroke-width': 5 }, g);
  mk('circle', { cx: 122, cy: 196, r: 260, fill: rgrad(g, [[0, '#ffe9a8', .34], [1, '#ffe9a8', 0]]) }, g);
  floorOf(g, C, hz);
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

// покачивание на месте: y0 ± amp с периодом period на отрезке t0..t0+dur (через tick: бит не растягивается, даже если dur больше бита)
const bob = (e, y0, amp, period, t0, dur) => dur <= .05 ? null : tick(t => put(e, { y: y0 + amp * Math.sin(Math.min(Math.max(t - t0, 0), dur) / period * Math.PI * 2) }));

// стол поверх героя: закрывает нижний край торса (ног у героя нет); вызывать после героя. Лежит в зоне, где у платформ подписи и кнопки
function desk(g, y = 1290, colour = '#5b4636') {
  rect(g, -20, y, W + 40, H - y + 20, { fill: colour, stroke: INK, 'stroke-width': 6 });
  rect(g, -20, y + 14, W + 40, 6, { fill: 'rgba(255,255,255,.12)' });
}

// красная линия поверх (зачёркивание, крест)
function strike(g, x1, y1, x2, y2, t0, { w = 28, colour = RED, dur = .25 } = {}) {
  const p = path(g, `M${x1} ${y1}L${x2} ${y2}`, { fill: 'none', stroke: colour, 'stroke-width': w, 'stroke-linecap': 'round' }, { d: 0 });
  draw(p, t0, dur, out);
  sfx(BEAT_ID, t0, 'tick', .8);
  return p;
}

// искры сварки: частицы летят вверх-в стороны и падают, видны на отрезке t0..t1 (через tick: t1 не растягивает бит)
function sparks(g, x, y, t0, t1, { n = 34, seed = 5 } = {}) {
  const R = seeded(seed), grp = G(g, {}), ps = [];
  for (let i = 0; i < n; i++) ps.push({ a: -Math.PI * (.12 + R() * .76), v: 220 + R() * 420, ph: R(), life: .45 + R() * .45, el: mk('circle', { r: 3 + R() * 4, fill: R() < .5 ? '#ffd23f' : '#ff8a3d' }, grp) });
  const core = mk('circle', { cx: x, cy: y, r: 16, fill: '#fff7c2' }, grp);
  tick(t => {
    const on = t >= t0 && t <= t1;
    ps.forEach(p => {
      const age = (((t / p.life) + p.ph) % 1) * p.life;
      p.el.setAttribute('cx', x + Math.cos(p.a) * p.v * age); p.el.setAttribute('cy', y + Math.sin(p.a) * p.v * age + 760 * age * age);
      p.el.setAttribute('opacity', on ? 1 - age / p.life : 0);
    });
    core.setAttribute('r', on ? 13 + 6 * Math.abs(Math.sin(t * 41)) : 0);
  });
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

/* manner.js — манера рисунка (стиль → манера): то, чем один мультик отличается от другого, когда герои и сюжет те же.

   Линия, глаза и пропорции задаются при построении героя и реквизита. Дрожь, пиксели (клетки), тона и растр — один фильтр на слое рисунка: слой стоит на месте,
   камера двигает его содержимое, поэтому шум не едет за камерой, а субтитры лежат рядом со слоем и остаются чёткими.
   Цена кадра 1080×1920 (Chromium, снимок JPEG): без манеры 50 мс, тона 80 мс, дрожь 160 мс. Дрожь держите вместе с рывками: при рывках 12 снимается 12 кадров
   из 30, остальные — копии, и ролик снимается почти за то же время. */
'use strict';

const DRAWN = MN.wobble > 0 || MN.tones.length > 0 || MN.pixels > 0;          // нужен ли фильтр на слое рисунка
const BOIL_SHEETS = 4;                                       // сколько «перерисовок» идёт по кругу: так дрожит линия в рисованной анимации
const NOISE_SPREAD = 6;                                      // шум отклоняется от середины примерно на 1/6, поэтому сдвиг = амплитуда × 6
let turbulence = null;

// определения манеры: один раз на всю страницу, до сборки битов
// фактура краски: битмап из шума на нескольких масштабах, один на всю страницу. Светлый, ложится умножением: гуашь даёт пятна и зерно, бумага — мелкое волокно.
// Шум повторяемый (seeded), поэтому кадр можно снять в любом порядке; слой стоит на месте, камера его не двигает.
function textureImage(kind) {
  const w = 450, h = 800, c = document.createElement('canvas'), R = seeded(kind === 'paper' ? 71 : 17);
  c.width = w; c.height = h;
  const ctx = c.getContext('2d'), img = ctx.createImageData(w, h);
  const layers = kind === 'paper' ? [[3, .55], [1, .45]] : [[150, .34], [48, .28], [14, .2], [2, .18]], amp = kind === 'paper' ? 52 : 64;     // [размер ячейки в точках, вес]
  const lat = layers.map(([cell]) => { const gw = Math.ceil(w / cell) + 2, gh = Math.ceil(h / cell) + 2; return { cell, gw, v: Float32Array.from({ length: gw * gh }, R) }; });
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let n = 0;
    for (let i = 0; i < layers.length; i++) {
      const L = lat[i], fx = x / L.cell, fy = y / L.cell, ix = fx | 0, iy = fy | 0, tx = smooth(fx - ix), ty = smooth(fy - iy);
      const a = L.v[iy * L.gw + ix], b = L.v[iy * L.gw + ix + 1], d = L.v[(iy + 1) * L.gw + ix], e = L.v[(iy + 1) * L.gw + ix + 1];
      n += layers[i][1] * (a + (b - a) * tx + (d - a) * ty + (a - b - d + e) * tx * ty);
    }
    const g = 255 - amp * n, k = (y * w + x) * 4;
    img.data[k] = img.data[k + 1] = img.data[k + 2] = g; img.data[k + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return c.toDataURL('image/png');
}

function mannerDefs(svg) {
  if (!DRAWN && !MN.dots && !MN.paper && !MN.texture) return;
  const defs = mk('defs', {}, svg);
  if (MN.texture) mk('image', { id: 'mm-texture', x: -20, y: -20, width: W + 40, height: H + 40, preserveAspectRatio: 'none', href: textureImage(MN.texture) }, defs);
  if (DRAWN) {
    // область шире кадра: иначе смещение затягивает пустоту с края
    // пиксели: область фильтра кратна клетке, иначе границы клеток уедут от сетки и кадр «поплывёт» при смене размера
    const c = MN.pixels, ox = c ? -Math.ceil(20 / c) * c : -20, fw = c ? Math.ceil((W - ox + 20) / c) * c : W + 40, fh = c ? Math.ceil((H - ox + 20) / c) * c : H + 40;
    const f = mk('filter', { id: 'mm-manner', filterUnits: 'userSpaceOnUse', x: ox, y: ox, width: fw, height: fh, 'color-interpolation-filters': 'sRGB' }, defs);
    if (MN.wobble > 0) {
      turbulence = mk('feTurbulence', { type: 'fractalNoise', baseFrequency: MN.detail, numOctaves: 1, seed: 1, result: 'noise' }, f);
      mk('feDisplacementMap', { in: 'SourceGraphic', in2: 'noise', scale: MN.wobble * NOISE_SPREAD, xChannelSelector: 'R', yChannelSelector: 'G', result: 'drawn' }, f);
    }
    if (c) {                                                  // сетка: берём точку в центре каждой клетки и раздуваем до клетки (классический пиксельный фильтр SVG)
      mk('feFlood', { x: ox + c / 2 - 1, y: ox + c / 2 - 1, width: 2, height: 2, 'flood-color': '#000' }, f);
      mk('feComposite', { x: ox, y: ox, width: c, height: c }, f);
      mk('feTile', { result: 'tiles' }, f);
      mk('feComposite', { in: MN.wobble > 0 ? 'drawn' : 'SourceGraphic', in2: 'tiles', operator: 'in' }, f);
      mk('feMorphology', { operator: 'dilate', radius: c / 2 - 1, result: 'blocks' }, f);
    }
    if (MN.tones.length) {
      const luma = '.2126 .7152 .0722 0 0';                  // яркость точки выбирает тон: тёмное берёт первый цвет списка, светлое — последний
      mk('feColorMatrix', { in: c ? 'blocks' : MN.wobble > 0 ? 'drawn' : 'SourceGraphic', type: 'matrix', values: `${luma} ${luma} ${luma} 0 0 0 1 0` }, f);
      const map = mk('feComponentTransfer', {}, f), channels = [1, 3, 5].map(i => MN.tones.map(c => num(parseInt(c.slice(i, i + 2), 16) / 255)).join(' '));
      ['R', 'G', 'B'].forEach((c, i) => mk('feFunc' + c, { type: MN.stepped ? 'discrete' : 'table', tableValues: channels[i] }, map));
    }
  }
  if (MN.dots) {                                             // растр: светлые и тёмные ячейки поверх рисунка, порог тонов превращает их в точки разного размера
    // яркость падает так, что доля точек под порогом равна доле тона: серый 50% даёт половину чёрного. Ступени посчитаны по площади круга
    gstops(mk('radialGradient', { id: 'mm-dot', r: .7071 }, defs), [[0, '#fff'], [.4, '#bfbfbf'], [.564, '#808080'], [.707, '#373737'], [1, '#000']]);
    const cell = mk('pattern', { id: 'mm-dots', width: MN.dots, height: MN.dots, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' }, defs);
    rect(cell, 0, 0, MN.dots, MN.dots, { fill: 'url(#mm-dot)' });
  }
  if (MN.paper) {                                            // клетка или линейка: тонкие линии, под тонами серый попадает в средний цвет
    const step = MN.paper === 'grid' ? 56 : 72, cell = mk('pattern', { id: 'mm-paper', width: step, height: step, patternUnits: 'userSpaceOnUse' }, defs);
    mk('path', { d: MN.paper === 'grid' ? `M ${step} 0 H 0 V ${step}` : `M 0 0 H ${step}`, stroke: MN.tones.length ? '#6e6e6e' : MUTED, 'stroke-width': 3, fill: 'none' }, cell);
  }
}

// слой рисунка бита: фильтр на нём, растр поверх содержимого (вызывать после того, как создан слой сцены)
function dress(art) {
  if (MN.texture) { const u = mk('use', { href: '#mm-texture', opacity: MN.textureAmt }); u.style.mixBlendMode = 'multiply'; art.after(u); }   // между слоем рисунка и субтитрами: субтитры остаются чистыми
  if (DRAWN) art.setAttribute('filter', 'url(#mm-manner)');
  if (MN.dots) rect(art, -20, -20, W + 40, H + 40, { fill: 'url(#mm-dots)', opacity: .35 });   // чем слабее слой, тем чище белое и чёрное: точки остаются только в средних тонах
  if (MN.paper) rect(art, -20, -20, W + 40, H + 40, { fill: 'url(#mm-paper)' }).style.mixBlendMode = 'multiply';   // линии бумаги видны сквозь светлое и пропадают на тёмном
}

// дрожь на время t: перерисовка определяется только временем, поэтому кадр можно снять в любом порядке
function mannerFrame(t) {
  if (turbulence && MN.boil > 0) turbulence.setAttribute('seed', 1 + Math.floor(t * MN.boil + 1e-6) % BOIL_SHEETS);
}

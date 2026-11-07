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
function mannerDefs(svg) {
  if (!DRAWN && !MN.dots && !MN.paper) return;
  const defs = mk('defs', {}, svg);
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
  if (DRAWN) art.setAttribute('filter', 'url(#mm-manner)');
  if (MN.dots) rect(art, -20, -20, W + 40, H + 40, { fill: 'url(#mm-dots)', opacity: .35 });   // чем слабее слой, тем чище белое и чёрное: точки остаются только в средних тонах
  if (MN.paper) rect(art, -20, -20, W + 40, H + 40, { fill: 'url(#mm-paper)' }).style.mixBlendMode = 'multiply';   // линии бумаги видны сквозь светлое и пропадают на тёмном
}

// дрожь на время t: перерисовка определяется только временем, поэтому кадр можно снять в любом порядке
function mannerFrame(t) {
  if (turbulence && MN.boil > 0) turbulence.setAttribute('seed', 1 + Math.floor(t * MN.boil + 1e-6) % BOIL_SHEETS);
}

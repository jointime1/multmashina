/* plans.js — готовые планы: как собрать кадр, не считая координат.

   План сам ставит героя, закрывает то, что не должно быть видно (у героя нет ног), и возвращает подсказки:
     text — точка [x, y] для надписи, size — размер, который туда влезает: word(s, 'МИР', ...k.text, m('b'), { size: k.size });
     el — элемент героя или предмета, его можно двигать через tw.
   Планы, которые нельзя распознать по положению героя, ставят метку data-plan: проверка берёт название из неё.
   Всё зависит только от времени бита: панели и человечки считаются заново на каждом кадре. */
'use strict';

const tagPlan = (g, name) => g.setAttribute('data-plan', name);

// цвета и приметы героя для упрощённых рисунков: человечек, вид со спины, вид сверху
function tones(name) {
  const o = lookOf(name);
  return { o, skin: o.skin || SKIN, hair: o.hair || HAIR_COL, body: o.suit || (typeof o.armor === 'string' ? o.armor : '') || o.hoodCol || '#475569',
    glasses: o.glasses === undefined ? 1 : o.glasses, bald: !!o.bald, long: !!o.longHair, cap: o.capCol };
}

// перенос текста по словам: строки не шире maxW
function wrapText(str, size, maxW, font = SANS, weight = 500) {
  const lines = [];
  let cur = '';
  str.trim().split(/\s+/).forEach(w => {
    const next = cur ? `${cur} ${w}` : w;
    if (cur && inkW(next, size, font, weight) > maxW) { lines.push(cur); cur = w; } else cur = next;
  });
  if (cur) lines.push(cur);
  return lines;
}

// ---------- герой крупнее и ближе ----------

// крупно: лицо на весь кадр, торс уходит за низ
function closeUp(g, name, keys, t0, t1, o = {}) {
  const el = hero(g, name, o.x === undefined ? CX : o.x, 870, 2.4, keys, t0, t1, { punch: MO.punch * .5, ...o });
  return { el, text: [CX, 235], size: 130 };
}

// сверхкрупно: только глаза в полосе между чёрными шторками; реакция, страх, озарение
function eyes(g, name, keys, t0, t1, o = {}) {
  tagPlan(g, 'сверхкрупно');
  const el = hero(g, name, CX, 675, 4.4, keys, t0, t1, { punch: 0, ...o });
  rect(g, -20, -20, W + 40, 380, { fill: DARK });                   // шторки цвета фона: на них читаются те же надписи, что и на обычном кадре
  rect(g, -20, 900, W + 40, H - 880, { fill: DARK });
  return { el, text: [CX, 250], size: 150 };
}

// средний сбоку: герой за столом, рядом свободное место под то, о чём речь. side: 'left' | 'right'; o.desk — цвет стола
function medium(g, name, keys, t0, t1, o = {}) {
  const right = o.side === 'right', el = hero(g, name, right ? 640 : 260, 950, 1.2, keys, t0, t1, o);
  desk(g, 1290, o.desk);
  return { el, text: [CX, 470], size: 130, side: [right ? 270 : 630, 860] };
}

// двое лицом к лицу: крупные головы по краям кадра, смотрят друг на друга; ключ с px свой взгляд задаёт сам
function faceOff(g, a, keysA, b, keysB, t0, t1, o = {}) {
  tagPlan(g, 'лицом к лицу');
  const gaze = (keys, px) => keys.map(([t, name, over]) => [t, name, { px, ...over }]);
  const left = hero(g, a, 215, 880, 1.35, gaze(keysA, .9), t0, t1, { tilt: 5, ...o });
  const right = hero(g, b, 685, 880, 1.35, gaze(keysB, -.9), t0, t1, { tilt: -5, ...o });
  desk(g, 1290, o.desk);
  return { left, right, text: [CX, 400], size: 130 };
}

// через плечо: мы за спиной одного героя и смотрим на другого через стол. side: 'right' — спина справа
function overShoulder(g, back, front, keys, t0, t1, o = {}) {
  tagPlan(g, 'через плечо');
  const right = o.side === 'right', el = hero(g, front, right ? 300 : 600, 800, 1, keys, t0, t1, o);
  desk(g, 1090, o.desk);
  backView(g, back, right ? 690 : 210, 1250, 2.3);
  return { el, text: [CX, 300], size: 130 };
}

// голова и плечи со спины, на ближнем плане; чуть темнее, чем герой в глубине кадра
function backView(g, name, x, y, s) {
  const c = tones(name), e = G(g, { x, y, s });
  mk('path', { d: 'M -300 620 C -300 330 -190 200 -60 170 L 60 170 C 190 200 300 330 300 620 Z', fill: c.body, ...LINE }, e);
  mk('rect', { x: -60, y: 90, width: 120, height: 110, rx: 22, fill: c.skin, ...LINE }, e);
  mk('circle', { cx: -122, cy: 8, r: 26, fill: c.skin, ...LINE }, e); mk('circle', { cx: 122, cy: 8, r: 26, fill: c.skin, ...LINE }, e);
  mk('circle', { cx: 0, cy: 0, r: 122, fill: c.bald ? c.skin : c.hair, ...LINE }, e);
  if (c.long) mk('path', { d: 'M -128 -30 C -160 120 -150 220 -110 250 L 110 250 C 150 220 160 120 128 -30 Z', fill: c.hair, ...LINE }, e);
  else if (!c.bald) mk('path', { d: 'M -60 -104 L -88 -160 L -22 -118 Z M 10 -120 L 4 -176 L 54 -112 Z M 74 -92 L 116 -148 L 114 -70 Z', fill: c.hair, ...LINE }, e);
  if (c.cap) mk('path', { d: 'M -128 -10 C -134 -130 -50 -150 0 -150 C 50 -150 134 -130 128 -10 C 80 -40 -80 -40 -128 -10 Z', fill: c.cap, ...LINE }, e);
  mk('rect', { x: -320, y: -160, width: 640, height: 800, fill: '#000', opacity: .22 }, e);
  return e;
}

// реакция в кружке: лицо героя поверх экрана или предмета. x, y — центр, r — радиус
function inset(g, name, keys, t0, t1, o = {}) {
  const { x = 690, y = 330, r = 130 } = o, id = 'mmin' + (++sceneN), s = r / 190;
  const e = G(g, { x, y });
  mk('circle', { r: r + 9, fill: o.ring || MARK }, e);
  const clip = mk('clipPath', { id }, gdefs(e));
  mk('circle', { r }, clip);
  const c = G(e, {});
  c.setAttribute('clip-path', `url(#${id})`);
  mk('circle', { r, fill: o.bg || SEA }, c);
  hero(c, name, 0, r * .12, s, keys, t0, t1, { punch: 0, ...o, x: undefined, y: undefined });
  return e;
}

// ---------- герой маленький ----------

// человечек целиком: ноги, руки, походка. x, y — точка между ступнями, рост 600 px × s (s меньше 0,8 — это общий план).
// o: to — куда идёт, t0, t1 — когда, run — бегом, phase — сдвиг шага, чтобы толпа шла вразнобой
function figure(g, name, x, y, s = .5, o = {}) {
  const rig = RIGS[MN.rig];
  return rig && rig.figure ? rig.figure(g, name, x, y, s, o) : figureBust(g, name, x, y, s, o);   // другой способ построить героя: engine/rigs.js; без своего человечка — обычный
}
function figureBust(g, name, x, y, s = .5, o = {}) {
  const c = tones(name), moving = o.to !== undefined, dir = moving ? Math.sign(o.to - x) || 1 : 0;
  const t0 = o.t0 || 0, t1 = o.t1 === undefined ? t0 + 2 : o.t1, rate = o.run ? 10 : 6, amp = o.run ? 42 : 26, b = (c.o.build || 1) * MN.body;
  const e = G(g, { x, y, s });
  e.setAttribute('data-hero', '1');
  const body = mk('g', { 'data-body': 1 }, e);
  const limb = (px, py, len, w, col, foot) => {
    const l = mk('g', foot ? { 'data-leg': 1 } : {}, body);
    mk('path', { d: `M ${px} ${py} L ${px} ${py + len}`, stroke: INK, 'stroke-width': w + 12 * MN.line, 'stroke-linecap': 'round', fill: 'none' }, l);
    mk('path', { d: `M ${px} ${py} L ${px} ${py + len}`, stroke: col, 'stroke-width': w, 'stroke-linecap': 'round', fill: 'none' }, l);
    if (foot) mk('ellipse', { cx: px + (dir || 1) * 16, cy: py + len + 12, rx: 44, ry: 20, fill: '#111827', stroke: INK, 'stroke-width': 6 }, l);
    return l;
  };
  const armB = limb(-58 * b, -395, 170, 40 * b, c.o.arms ? c.skin : c.body), legB = limb(-30, -240, 228, 56, '#1f2937', true), legF = limb(30, -240, 228, 56, '#273449', true);
  mk('rect', { x: -66 * b, y: -424, width: 132 * b, height: 212, rx: 44, fill: c.body, ...LINE }, body);
  const fx = dir * 16, head = mk('g', { 'data-head': 1, transform: `translate(0 -520) scale(${MN.headW} ${MN.headH}) translate(0 520)` }, body);
  if (c.long) mk('path', { d: 'M -100 -560 C -124 -470 -112 -400 -84 -386 L 84 -386 C 112 -400 124 -470 100 -560 Z', fill: c.hair, ...LINE }, head);
  mk('circle', { cx: 0, cy: -520, r: 92, fill: c.skin, ...LINE }, head);
  [-1, 1].forEach(sd => mk('circle', { cx: fx + sd * 32, cy: -530, r: 10, fill: o.eye || '#1c1917' }, head));
  mk('path', { d: `M ${fx - 22} -486 Q ${fx} ${o.grin ? -462 : -482} ${fx + 22} -486`, stroke: '#3b0d0d', 'stroke-width': 8, 'stroke-linecap': 'round', fill: 'none' }, head);
  if (c.glasses) { [-1, 1].forEach(sd => mk('circle', { cx: fx + sd * 32, cy: -530, r: 28, fill: 'none', stroke: '#1e293b', 'stroke-width': 7 }, head)); }
  if (c.o.mustache) mk('path', { d: `M ${fx - 34} -494 Q ${fx} -516 ${fx + 34} -494 Q ${fx} -500 ${fx - 34} -494 Z`, fill: c.hair, ...LINE }, head);
  if (c.cap) mk('path', { d: 'M -96 -548 C -100 -634 96 -634 96 -548 C 50 -566 -50 -566 -96 -548 Z', fill: c.cap, ...LINE }, head);
  else if (!c.bald) {
    mk('path', { d: 'M -96 -540 C -106 -640 106 -640 96 -540 C 70 -574 -70 -574 -96 -540 Z', fill: c.hair, ...LINE }, head);
    if (!c.long) mk('path', { d: 'M -46 -600 L -60 -648 L -12 -610 Z M 8 -612 L 6 -660 L 42 -606 Z', fill: c.hair, ...LINE }, head);
  }
  const armF = limb(58 * b, -395, 170, 40 * b, c.o.arms ? c.skin : c.body);
  if (moving) tw(e, { x: o.to }, t0, t1 - t0, lin);
  const ph0 = o.phase || 0;
  tick(t => {
    const on = moving && t >= t0 && t <= t1, ph = (t - t0) * rate + ph0, a = on ? Math.sin(ph) * amp : 0;
    legF.setAttribute('transform', `rotate(${num(a)} 30 -240)`); legB.setAttribute('transform', `rotate(${num(-a)} -30 -240)`);
    armF.setAttribute('transform', `rotate(${num(-a * .8)} ${58 * b} -395)`); armB.setAttribute('transform', `rotate(${num(a * .8)} ${-58 * b} -395)`);
    const lift = on ? Math.abs(Math.sin(ph)) * 16 : Math.sin(t * 2 + ph0) * 3, lean = on && o.run ? dir * 10 : 0;
    body.setAttribute('transform', `translate(0 ${num(-lift)}) rotate(${lean} 0 -240)`);
  });
  return e;
}

// общий план: маленький герой в большом месте; главное — куда он идёт. o: x, y, s и всё, что понимает figure
function wide(g, name, o = {}) {
  const el = figure(g, name, o.x === undefined ? CX : o.x, o.y || 1130, o.s || .5, o);
  return { el, text: [CX, 420], size: 150 };
}

// вид сверху: стол в центре, вокруг него головы; names — герои, o.table: false — без стола, o.floor — цвет пола
function topView(g, names, o = {}) {
  tagPlan(g, 'сверху');
  const fx = CX, fy = 740, rx = 300, ry = 385, floor = o.floor || DARK;
  rect(g, -20, -20, W + 40, H + 40, { fill: floor });
  let d = '';
  for (let x = 0; x <= W; x += 150) d += `M${x} 0V${H}`;
  for (let y = 0; y <= H; y += 150) d += `M0 ${y}H${W}`;
  mk('path', { d, stroke: 'rgba(148,163,184,.14)', 'stroke-width': 4, fill: 'none' }, g);
  if (o.table !== false) {
    rect(g, fx - 200, fy - 262, 412, 540, { fill: 'rgba(0,0,0,.28)', rx: 26 });
    rect(g, fx - 210, fy - 280, 420, 560, { fill: '#5b4636', stroke: INK, 'stroke-width': 7, rx: 24 });
    rect(g, fx - 186, fy - 256, 372, 512, { fill: 'none', stroke: 'rgba(255,255,255,.1)', 'stroke-width': 5, rx: 14 });
  }
  const heads = names.map((name, i) => {
    const a = -Math.PI / 2 + i * Math.PI * 2 / names.length, x = fx + Math.cos(a) * rx, y = fy + Math.sin(a) * ry;
    return headTop(g, name, x, y, .95, a * 180 / Math.PI - 90);
  });
  return { heads, table: { x: fx, y: fy, w: 420, h: 560 }, text: [CX, 220], size: 110 };
}

// голова сверху: плечи, макушка, нос в сторону взгляда; r — поворот в градусах, 0 — смотрит вверх кадра
function headTop(g, name, x, y, s, r = 0) {
  const c = tones(name), e = G(g, { x, y, s, r });
  mk('ellipse', { cx: 0, cy: 0, rx: 176, ry: 76, fill: c.body, ...LINE }, e);
  mk('path', { d: 'M -14 -98 L 0 -128 L 14 -98 Z', fill: c.skin, ...LINE }, e);
  mk('circle', { cx: -100, cy: 0, r: 20, fill: c.skin, ...LINE }, e); mk('circle', { cx: 100, cy: 0, r: 20, fill: c.skin, ...LINE }, e);
  mk('circle', { cx: 0, cy: 0, r: 102, fill: c.cap || (c.bald ? c.skin : c.hair), ...LINE }, e);
  if (c.long) mk('path', { d: 'M -96 30 C -110 110 -60 200 0 212 C 60 200 110 110 96 30 Z', fill: c.hair, ...LINE }, e);
  else if (!c.bald && !c.cap) mk('path', { d: 'M -34 -18 C -8 -46 34 -36 38 -6 C 40 22 6 38 -14 22', stroke: 'rgba(255,255,255,.16)', 'stroke-width': 9, fill: 'none', 'stroke-linecap': 'round' }, e);
  return e;
}

// ---------- без героя ----------

// переписка на весь кадр. msgs: [[кто, текст, время], …]; кто: 0 — собеседник, 1 — свой. Лишнее уезжает вверх
function chat(g, title, msgs, o = {}) {
  tagPlan(g, 'экран');
  const size = o.size || 54, lh = size * 1.28, top = 290, bottom = 1130, list0 = G(g, {});
  const bg = rect(list0, -20, -2000, W + 40, H + 4000, { fill: o.bg || DARK });
  bg.setAttribute('data-decor', '1');
  const list = G(list0, {});
  let y = top;
  const shown = [];
  msgs.forEach(([who, text, t0]) => {
    const lines = wrapText(text, size, 560), bw = Math.max(...lines.map(l => inkW(l, size, SANS, 500))) + 56, bh = lines.length * lh + 34;
    const x = who ? 810 - bw : 60, e = G(list, { x, y, o: 0 });
    rect(e, 0, 0, bw, bh, { fill: who ? (o.mine || '#2563eb') : (o.theirs || '#334155'), rx: 28 });
    lines.forEach((l, i) => T(e, l, { x: 28, y: 17 + size * .9 + i * lh, size, fill: '#f8fafc', weight: 500 }));
    enter(e, 'rise', t0, { x, y });
    sfx(BEAT_ID, t0, 'tick', .6);
    if (y + bh > bottom) {                                            // новое сообщение не влезло: лента едет вверх, ушедшие под шапку гаснут
      const off = bottom - y - bh;
      tw(list, { y: off }, t0, .22, out);
      shown.forEach(q => { if (!q.gone && q.y + off < top - 30) { q.gone = true; hide(q.e, t0, .12); } });
    }
    shown.push({ e, y });
    y += bh + 20;
  });
  rect(g, -20, -20, W + 40, 260, { fill: o.head || '#1e293b' });
  rect(g, -20, 238, W + 40, 4, { fill: 'rgba(255,255,255,.12)' });
  T(g, title, { x: CX, y: 200, size: 52, fill: '#f8fafc', weight: 600, anchor: 'middle' });
  return { el: list, text: [CX, 1180], size: 80 };
}

// предмет крупно: стол в луче света, медленный наезд. draw(c) рисует в группе с центром в начале координат
function item(g, draw, o = {}) {
  tagPlan(g, 'предмет');
  const glow = o.glow || MARK;
  rect(g, -20, -20, W + 40, H + 40, { fill: o.bg || DARK });
  mk('circle', { cx: CX, cy: 620, r: 720, fill: rgrad(g, [[0, glow, .3], [1, glow, 0]]) }, g);
  const c = G(g, { x: CX, y: o.y || 620, s: .96 });
  draw(c);
  tick(t => put(c, { s: .96 + t * .018 }));
  return { el: c, text: [CX, 1100], size: 90 };
}

// ---------- несколько кадров сразу ----------

// панели комикса: n рядов над субтитрами, а при n = 2 и o.diag — косой разрез. Внутри панели обычные координаты кадра: её центр — точка (450, 800), торс обрезает край.
// o.at — когда появляется каждая панель (0 или пусто — сразу), o.gutter — цвет промежутков. Возвращает группы панелей
function panels(g, n, o = {}) {
  tagPlan(g, 'комикс');
  const gap = o.gap === undefined ? 14 : o.gap, bottom = 1150, h = (bottom - gap * n) / n, at = o.at || [], mid = bottom / 2, slant = 90;
  rect(g, -20, -20, W + 40, H + 40, { fill: o.gutter || INK });
  rect(g, -20, bottom, W + 40, H - bottom + 20, { fill: CAP.stroke });  // полоса цвета обводки субтитров: на ней они читаются в любой манере
  return Array.from({ length: n }, (_, i) => {
    const y = gap + i * (h + gap), id = 'mmpn' + (++sceneN), clip = mk('clipPath', { id }, gdefs(g));
    if (o.diag && n === 2) mk('path', { d: i ? `M 0 ${mid + slant + gap} L ${W} ${mid - slant + gap} V ${bottom} H 0 Z` : `M 0 0 H ${W} V ${mid - slant - gap} L 0 ${mid + slant - gap} Z` }, clip);
    else rect(clip, gap, y, W - 2 * gap, h);
    const late = at[i] > 0, wrap = G(g, { o: late ? 0 : 1 });
    wrap.setAttribute('clip-path', `url(#${id})`);
    wrap.setAttribute('data-panel', i);
    const inner = G(wrap, { x: late ? (i % 2 ? W : -W) : 0, y: y + h / 2 - H / 2 });
    if (late) { show(wrap, at[i], .01); tw(inner, { x: 0 }, at[i], .26, out); sfx(BEAT_ID, at[i], 'whoosh', .3); }
    return inner;
  });
}

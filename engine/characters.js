/* characters.js — герои: лицо, волосы, эмоции. Рисуются кодом (SVG), начало координат — центр головы, радиус головы 120.
   Контуры толстые и тёмные. Всё — чистая функция от времени бита (моргание, дыхание, слёзы тоже), поэтому перемотка и рендер точны.

   face(g, x, y, масштаб, ключи, от, до, настройки) — герой по пояс; ключи эмоций: [[время, 'имя', {добавки}], …];
   hero(g, 'имя героя из стиля', …) — то же, но настройки берутся из раздела «герои» стиля. */
'use strict';
const SKIN = '#f2c29b', SKIN_SH = '#dba27a', HAIR_COL = '#3b2a20';
const LINE = { stroke: INK, 'stroke-width': 6, 'stroke-linejoin': 'round' };

// Параметры лица. by/bt — брови (выше/ниже; bt > 0 — внутренние концы вниз, злое; bt < 0 — вверх, жалобное; ba — правая бровь выше),
// eo — открытость глаз (1 норма, >1 выпученные), px/py — взгляд, mw — полуширина рта, mc — высота уголков рта, mu/ml — верхняя и нижняя
// кривые рта, teeth/gap — зубы и дырка на месте двух передних, tear/sweat/blush/bags — слёзы, пот, румянец, мешки под глазами,
// hair — волосы дыбом, r — наклон головы, shk — дрожь, wink — подмигивание, shades — тёмные очки, rank — 0 Петя, 1 Петрович,
// helm — сварочная маска на голове, mask — забрало маски (0 поднято, 1 опущено на глаза).
const EMO0 = { by: 0, bt: 0, ba: 0, eo: 1, px: 0, py: 0, mw: 50, mc: 0, mu: 0, ml: 0, teeth: 0, gap: 0, tear: 0, sweat: 0, blush: 0,
  bags: .2, hair: 0, r: 0, shk: 0, wink: 0, shades: 0, rank: 0, helm: 0, mask: 0 };
const EMO = {
  neutral:  {},
  dead:     { eo: .5, py: .5, bags: 1, mw: 40, mc: 6, mu: 4, ml: 4 },
  tired:    { eo: .45, by: 8, bt: -8, py: .7, bags: 1, mw: 42, mc: 6, mu: 10, ml: 10 },
  sad:      { eo: .85, by: -4, bt: -18, py: .6, bags: .8, mw: 46, mu: -26, ml: -26 },
  cry:      { eo: .6, by: -2, bt: -22, py: .4, bags: 1, mw: 54, mc: 26, mu: -10, ml: 52, tear: 1, blush: .6 },
  shock:    { eo: 1.35, by: -30, mw: 30, mu: -26, ml: 86, sweat: 1, hair: .8 },
  rage:     { eo: .85, by: 2, bt: 24, mw: 66, mu: -4, ml: 78, teeth: 1, blush: 1, hair: 1, shk: 4, bags: .4 },
  stern:    { eo: .75, by: 4, bt: 20, mw: 44, mc: 8, mu: -2, ml: -2, blush: .5 },
  smug:     { eo: .7, by: -6, bt: 8, ba: -8, px: .5, mw: 54, mc: -4, mu: 26, ml: 30 },
  grin:     { eo: .8, by: -8, mw: 66, mc: -8, mu: 14, ml: 70, teeth: 1, blush: .2 },
  epiphany: { eo: 1.25, by: -24, py: -.5, mw: 60, mc: -6, mu: 10, ml: 76, teeth: 1, hair: .5 },
  skeptic:  { eo: .7, by: 2, bt: 10, ba: -16, px: -.5, mw: 40, mc: 2, mu: 8, ml: 8, bags: .5 },
  thinking: { eo: .9, by: -10, bt: -6, ba: -14, px: .8, py: -.7, mw: 34, mc: 8 },
  worry:    { eo: 1.1, by: -14, bt: -20, py: .3, mw: 48, mc: 10, mu: -6, ml: 14, sweat: 1, bags: .6, hair: .4 },
  drunk:    { eo: .55, by: 4, bt: 2, px: .4, py: .2, mw: 66, mc: -6, mu: 22, ml: 72, teeth: 1, blush: 1 },
};

// эмоция в момент tau: ключи [время, имя, добавки]; к каждому ключу лицо плавно приходит за последние 0.2 с
function emoAt(keys, tau) {
  const BL = .2;
  let i = -1;
  for (let k = 0; k < keys.length; k++) if (keys[k].t <= tau) i = k;
  const A = keys[Math.max(i, 0)].p, nxt = keys[i + 1];
  if (!nxt || tau < nxt.t - BL) return A;
  const q = smooth(ramp01(tau, nxt.t - BL, nxt.t)), out = {};
  for (const k in EMO0) out[k] = A[k] + (nxt.p[k] - A[k]) * q;
  return out;
}

let faceN = 0;
/* face(g, x, y, s, keys, t0, t1, opts): герой по пояс; x, y — центр головы, s — масштаб.
   keys — [[t, 'emo', {добавки}], …] во времени бита; t0..t1 — когда кадр живёт (рисуется на этом отрезке);
   opts: skin, hair (цвет), seed (сдвиг моргания), glasses (0 — без очков), in (когда выпрыгивает) + enter (как: drop, left, right, rise, zoom, spin), tilt,
         punch (сила «вздрагивания» при смене эмоции; по умолчанию из стиля, анимации → реакция),
         hoodCol, suit (цвет пиджака) + tie + shirt, bald, longHair, lips, noNose, box (коробка с вещами в руках);
         облик: armor (цвет доспеха: наплечники с шипами, нагрудник, плащ cloak), arms (голые руки), tattoo (цвет татуировок на руках и шее),
         build (ширина торса и рук, 1 — обычный, 1.5 — качок), mustache (усы), buzz (бритая голова со щетиной), eyeCol (цвет радужки),
         browCol (цвет бровей), emblem + emblemCol (надпись на толстовке вместо </>) */
function face(g, x, y, s, keys, t0, t1, o = {}) {
  const build = o.build || 1, nk = 1 + (build - 1) * .8;
  const shade = (hex, k) => '#' + [1, 3, 5].map(i => Math.round(parseInt(hex.slice(i, i + 2), 16) * k).toString(16).padStart(2, '0')).join('');
  const id = ++faceN, skin = o.skin || SKIN, hairC = o.hair || HAIR_COL, seed = o.seed || 0, glasses = o.glasses === undefined ? 1 : o.glasses;
  keys = keys.map(([t, name, over]) => ({ t, p: { ...EMO0, ...(EMO[name] || {}), ...(over || {}) } }));
  const own = o.enter && o.enter !== 'pop';                         // свой вход (drop, left, right, rise, zoom, spin) вместо прыжка по умолчанию
  const R = G(g, o.in === undefined || own ? { x, y, s } : { x, y, s: s * .7, o: 0 });
  R.setAttribute('data-hero', '1');                                 // по этой метке проверка находит героев в кадре и считает план
  if (o.in !== undefined) { if (own) enter(R, o.enter, o.in, { x, y, s }); else tw(R, { s, o: 1 }, o.in, .3, back); sfx(BEAT_ID, o.in, 'thud', .5); }

  // тело: Петя в толстовке, Петрович в комбинезоне поверх майки (переключаются по rank); массовка — в пиджаке (suit)
  const B = mk('g', {}, R), torso = 'M -196 340 C -196 232 -124 176 -46 166 L 46 166 C 124 176 196 232 196 340 Z';
  if (o.armor) mk('path', { d: 'M -190 340 L -240 206 C -150 112 150 112 240 206 L 190 340 Z', fill: o.cloak || '#1e3a8a', ...LINE }, B);   // плащ
  const hood = mk('g', {}, B);
  mk('ellipse', { cx: 0, cy: 150, rx: 118, ry: 56, fill: '#334155', ...LINE }, hood);
  mk('path', { d: torso, fill: o.hoodCol || '#475569', ...LINE }, hood);
  mk('path', { d: 'M -22 172 L -30 252 M 22 172 L 30 252', stroke: '#e2e8f0', 'stroke-width': 6, 'stroke-linecap': 'round', fill: 'none' }, hood);
  const emb = o.emblem || '</>';
  T(hood, emb, { x: 0, y: 312, size: emb.length > 3 ? 44 : 58, fill: o.emblemCol || ACCENT, font: MONO, weight: 700, anchor: 'middle' }).setAttribute('data-decor', '1');   // украшение: проверка безопасной зоны его пропускает
  const ov = mk('g', { opacity: 0 }, B);
  mk('path', { d: torso, fill: '#e2e8f0', ...LINE }, ov);
  mk('path', { d: 'M -150 340 L -150 252 L -100 210 L 100 210 L 150 252 L 150 340 Z', fill: '#2563eb', ...LINE }, ov);
  mk('path', { d: 'M -92 172 L -128 262 M 92 172 L 128 262', stroke: '#2563eb', 'stroke-width': 30, 'stroke-linecap': 'round', fill: 'none' }, ov);
  mk('rect', { x: -44, y: 262, width: 88, height: 58, rx: 8, fill: '#1d4ed8', ...LINE }, ov);
  mk('circle', { cx: -128, cy: 262, r: 9, fill: '#fbbf24' }, ov); mk('circle', { cx: 128, cy: 262, r: 9, fill: '#fbbf24' }, ov);
  const suit = o.suit ? mk('g', {}, B) : null;
  if (suit) {
    mk('path', { d: torso, fill: o.suit, ...LINE }, suit);
    mk('path', { d: 'M -64 168 L 0 270 L 64 168 Z', fill: o.shirt || '#f1f5f9', ...LINE }, suit);
    if (o.tie) mk('path', { d: 'M -16 190 L 16 190 L 24 300 L 0 336 L -24 300 Z', fill: o.tie, ...LINE }, suit);
  }
  // голые руки (капсулы: тёмная обводка + кожа), с татуировками по предплечью
  if (o.arms || o.tattoo) {
    const aw = 52 * build;
    [-1, 1].forEach(sd => {
      const x0 = sd * 196, x1 = sd * (212 + (build - 1) * 24);
      mk('path', { d: `M ${x0} 238 L ${x1} 352`, stroke: INK, 'stroke-width': aw + 12, 'stroke-linecap': 'round', fill: 'none' }, B);
      mk('path', { d: `M ${x0} 238 L ${x1} 352`, stroke: skin, 'stroke-width': aw, 'stroke-linecap': 'round', fill: 'none' }, B);
      if (build > 1.2) mk('ellipse', { cx: x0 + sd * 6, cy: 272, rx: aw * .36, ry: 34, fill: 'rgba(255,255,255,.12)' }, B);   // блик на бицепсе
      if (o.tattoo) {
        const t = mk('g', { stroke: o.tattoo, 'stroke-width': 5, fill: 'none', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, B);
        for (let k = 0; k < 4; k++) {
          const y = 262 + k * 24, cx = x0 + (x1 - x0) * (y - 238) / 114;
          mk('path', { d: `M ${cx - 17} ${y} L ${cx - 5} ${y + 11} L ${cx + 5} ${y - 2} L ${cx + 17} ${y + 10}`, }, t);
        }
        mk('path', { d: `M ${x0 - 14} 236 C ${x0 + sd * 12} 252 ${x0 - sd * 6} 276 ${x0 + sd * 14} 292 M ${x0} 238 L ${x0} 330`, 'stroke-width': 3, opacity: .7 }, t);
        mk('circle', { cx: x1, cy: 340, r: 6, fill: o.tattoo, stroke: 'none' }, t);
      }
    });
  }
  // доспех: подкладка, нагрудник с ледяными прожилками, высокий воротник, наплечники с шипами
  const armor = o.armor ? mk('g', {}, B) : null;
  if (armor) {
    const st = typeof o.armor === 'string' ? o.armor : '#475569';
    mk('path', { d: torso, fill: '#1f2937', ...LINE }, armor);
    mk('path', { d: 'M -150 340 L -140 236 Q 0 200 140 236 L 150 340 Z', fill: st, ...LINE }, armor);
    mk('path', { d: 'M 0 214 L 0 340 M -72 252 L -52 340 M 72 252 L 52 340', stroke: '#7dd3fc', 'stroke-width': 7, 'stroke-linecap': 'round', fill: 'none' }, armor);
    mk('ellipse', { cx: 0, cy: 170, rx: 100, ry: 40, fill: st, ...LINE }, armor);
    [-1, 1].forEach(sd => {
      mk('path', { d: `M ${sd * 150} 176 L ${sd * 176} 70 L ${sd * 214} 184 Z M ${sd * 214} 196 L ${sd * 286} 128 L ${sd * 262} 232 Z`, fill: '#94a3b8', ...LINE }, armor);   // шипы
      mk('path', { d: `M ${sd * 86} 190 C ${sd * 170} 148 ${sd * 250} 184 ${sd * 258} 266 C ${sd * 206} 292 ${sd * 140} 268 ${sd * 96} 244 Z`, fill: st, ...LINE }, armor);   // наплечник
      mk('path', { d: `M ${sd * 118} 200 Q ${sd * 180} 192 ${sd * 232} 236`, stroke: '#7dd3fc', 'stroke-width': 6, fill: 'none', 'stroke-linecap': 'round' }, armor);
    });
  }
  [hood, ov, suit, armor].forEach(g => g && build !== 1 && g.setAttribute('transform', `scale(${build} 1)`));
  mk('rect', { x: -34 * nk, y: 80, width: 68 * nk, height: 110, rx: 20, fill: o.skin ? shade(o.skin, .9) : SKIN_SH, ...LINE }, R);   // шея поверх воротника
  if (o.tattoo) mk('path', { d: 'M -22 126 L -10 142 L -22 158 M 22 126 L 10 142 L 22 158', stroke: o.tattoo, 'stroke-width': 5, fill: 'none', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, R);

  // коробка с вещами из офиса: растение, кружка, резиновая уточка
  if (o.box) {
    const bx = mk('g', {}, R);
    mk('path', { d: 'M -78 262 C -126 176 -64 124 -42 196 C -30 140 24 146 4 262 Z', fill: '#22c55e', ...LINE }, bx);
    mk('rect', { x: 52, y: 214, width: 62, height: 60, rx: 8, fill: '#f8fafc', ...LINE }, bx);
    mk('path', { d: 'M 114 228 C 146 228 146 262 114 262', fill: 'none', stroke: INK, 'stroke-width': 8 }, bx);
    mk('ellipse', { cx: -2, cy: 256, rx: 34, ry: 26, fill: '#fde047', ...LINE }, bx);
    mk('circle', { cx: 24, cy: 222, r: 20, fill: '#fde047', ...LINE }, bx);
    mk('path', { d: 'M 40 222 L 62 228 L 40 234 Z', fill: '#fb923c', stroke: INK, 'stroke-width': 4 }, bx);
    mk('circle', { cx: 28, cy: 216, r: 4, fill: INK }, bx);
    mk('rect', { x: -156, y: 262, width: 312, height: 150, rx: 8, fill: '#c19a6b', ...LINE }, bx);
    mk('path', { d: 'M -156 262 L -184 236 L -64 236 L -44 262 Z M 156 262 L 184 236 L 64 236 L 44 262 Z', fill: '#d6b48a', ...LINE }, bx);
    T(bx, 'ПЕТЯ', { x: 0, y: 352, size: 64, fill: '#3b2a20', font: SANS, weight: 600, anchor: 'middle' }).setAttribute('data-decor', '1');   // надпись на коробке — реквизит
  }

  // голова: волосы сзади, уши, лицо, потом щетина / нос / глаза / рот / волосы / кепка / очки
  const H = mk('g', {}, R);
  if (o.longHair && o.armor) {                         // длинные волосы с доспехом: две пряди по бокам лица падают на плечи
    mk('path', { d: 'M -122 -60 C -152 20 -156 150 -142 246 C -126 272 -102 258 -98 232 L -90 60 L 90 60 L 98 232 C 102 258 126 272 142 246 C 156 150 152 20 122 -60 Z', fill: hairC, ...LINE }, H);
    mk('path', { d: 'M -138 30 C -146 110 -140 190 -128 238 M -114 60 C -120 130 -116 190 -112 232 M 138 30 C 146 110 140 190 128 238 M 114 60 C 120 130 116 190 112 232', stroke: 'rgba(15,23,42,.35)', 'stroke-width': 4, fill: 'none', 'stroke-linecap': 'round' }, H);
  } else if (o.longHair) mk('path', { d: 'M -140 -50 C -176 120 -160 210 -112 224 L 112 224 C 160 210 176 120 140 -50 C 128 -160 -128 -160 -140 -50 Z', fill: hairC, ...LINE }, H);
  mk('circle', { cx: -122, cy: 8, r: 26, fill: skin, ...LINE }, H); mk('circle', { cx: 122, cy: 8, r: 26, fill: skin, ...LINE }, H);
  mk('circle', { cx: 0, cy: 0, r: 122, fill: skin, ...LINE }, H);
  const blush = [-1, 1].map(sd => mk('ellipse', { cx: sd * 80, cy: 42, rx: 28, ry: 17, fill: '#ef4444', opacity: 0 }, H));
  const stub = mk('g', { opacity: 0 }, H), Rn = seeded(31 + id);
  for (let i = 0; i < 54; i++) { const a = Rn() * Math.PI, rr = 40 + Rn() * 64; mk('circle', { cx: Math.cos(a) * rr * .76 * (Rn() < .5 ? -1 : 1), cy: 20 + Math.sin(a) * rr * .85, r: 2.3, fill: '#6b4f3a' }, stub); }
  mk('path', { d: 'M -2 -2 Q 16 30 -6 34', stroke: '#c98b6b', 'stroke-width': 8, 'stroke-linecap': 'round', fill: 'none' }, H);
  const nose = mk('circle', { cx: 2, cy: 28, r: 22, fill: '#ef4444', opacity: 0 }, H);

  const eyes = [-1, 1].map(sd => {
    const e = mk('g', { transform: `translate(${sd * 50} -8)` }, H);
    const white = mk('ellipse', { cx: 0, cy: 0, rx: 31, ry: 35, fill: '#fff', stroke: INK, 'stroke-width': 4 }, e);
    const pup = mk('g', {}, e);
    if (o.eyeCol) { mk('circle', { cx: 0, cy: 0, r: 25, fill: o.eyeCol, opacity: .9 }, pup); mk('circle', { cx: 0, cy: 0, r: 17, fill: '#e0f7ff' }, pup); mk('circle', { cx: 0, cy: 0, r: 8, fill: '#0b1220' }, pup); }
    else { mk('circle', { cx: 0, cy: 0, r: 14, fill: '#1c1917' }, pup); mk('circle', { cx: 4, cy: -5, r: 4.5, fill: '#fff' }, pup); }
    const lid = mk('rect', { x: -38, y: -38, width: 76, height: 0, fill: skin }, e);
    const line = mk('path', { d: 'M -26 2 Q 0 16 26 2', stroke: INK, 'stroke-width': 6, 'stroke-linecap': 'round', fill: 'none', opacity: 0 }, e);
    const bag = mk('path', { d: `M ${sd * 22} 36 Q ${sd * 0} 52 ${-sd * 22} 36`, stroke: '#c38663', 'stroke-width': 7, 'stroke-linecap': 'round', fill: 'none', opacity: 0 }, e);
    return { sd, white, pup, lid, line, bag };
  });
  const brows = [-1, 1].map(() => mk('path', { stroke: o.browCol || hairC, 'stroke-width': 15, 'stroke-linecap': 'round', fill: 'none' }, H));
  const tears = [-1, 1].map(sd => [0, 1].map(i => mk('ellipse', { rx: 8, ry: 12, fill: '#7dd3fc', opacity: 0, cx: sd * 58 + (i ? 7 : -7) }, H)));
  const sweat = mk('path', { d: 'M 0 -18 C 14 2 14 16 0 16 C -14 16 -14 2 0 -18 Z', fill: '#7dd3fc', opacity: 0 }, H);
  const glass = mk('g', { opacity: glasses }, H);
  [-1, 1].forEach(sd => mk('circle', { cx: sd * 50, cy: -8, r: 46, fill: 'rgba(255,255,255,.07)', stroke: '#1e293b', 'stroke-width': 7 }, glass));
  mk('path', { d: 'M -6 -12 Q 0 -20 6 -12', stroke: '#1e293b', 'stroke-width': 7, fill: 'none' }, glass);
  const shades = mk('g', { opacity: 0 }, H);
  [-1, 1].forEach(sd => mk('rect', { x: sd * 50 - 36, y: -34, width: 72, height: 52, rx: 16, fill: '#0b1220', stroke: '#334155', 'stroke-width': 3 }, shades));
  mk('path', { d: 'M -14 -22 L 14 -22', stroke: '#0b1220', 'stroke-width': 8, 'stroke-linecap': 'round' }, shades);
  mk('path', { d: 'M -70 -24 L -62 -14 M 56 -24 L 64 -14', stroke: 'rgba(255,255,255,.35)', 'stroke-width': 5, 'stroke-linecap': 'round' }, shades);

  // рот: контур от параметров, зубы и язык обрезаны по его форме
  const mouthG = mk('g', { transform: 'translate(0 78)' }, H), clip = mk('clipPath', { id: 'mc' + id }, mouthG), cpath = mk('path', {}, clip);
  const mpath = mk('path', { fill: o.lips ? '#7f1d1d' : '#5b1a1a', stroke: o.lips || '#3b0d0d', 'stroke-width': o.lips ? 9 : 6, 'stroke-linejoin': 'round' }, mouthG);
  const inner = mk('g', { 'clip-path': `url(#mc${id})` }, mouthG);
  const tongue = mk('ellipse', { cx: 0, cy: 0, rx: 30, ry: 14, fill: '#f43f5e', opacity: 0 }, inner);
  const teeth = [0, 1, 2, 3, 4, 5].map(k => mk('rect', { x: -102 + k * 34 + 1, y: 0, width: 32, height: 34, rx: 8, fill: '#f8fafc', stroke: '#cbd5e1', 'stroke-width': 2, opacity: 0 }, inner));
  const must = mk('path', { d: 'M -66 54 C -52 34 -14 38 0 52 C 14 38 52 34 66 54 C 50 76 16 68 0 60 C -16 68 -50 76 -66 54 Z', fill: o.mustCol || hairC, opacity: 0, ...(o.mustache ? LINE : {}), 'stroke-width': 4 }, H);

  // волосы и кепка
  const hair = mk('g', { opacity: o.bald ? 0 : 1 }, H);
  mk('path', { d: 'M -128 -22 C -142 -150 -62 -198 4 -192 C 84 -198 144 -132 128 -22 C 112 -68 84 -92 46 -88 C 28 -116 -22 -114 -44 -84 C -84 -96 -114 -66 -128 -22 Z', fill: hairC, ...LINE }, hair);
  if (!o.longHair) mk('path', { d: 'M -60 -176 L -88 -236 L -22 -190 Z M 10 -190 L 4 -254 L 54 -186 Z M 74 -170 L 116 -226 L 114 -148 Z', fill: hairC, ...LINE }, hair);
  if (o.buzz) {            // бритая голова: тёмная тень от линии волос и щетина по макушке
    const bz = mk('g', {}, H), Rb = seeded(77 + id);
    mk('path', { d: 'M -118 -30 C -128 -128 128 -128 118 -30 C 98 -84 -98 -84 -118 -30 Z', fill: hairC, opacity: .5 }, bz);
    for (let i = 0; i < 70; i++) { const a = Math.PI * (1.27 + Rb() * .46), rr = 98 + Rb() * 18; mk('circle', { cx: Math.cos(a) * rr, cy: Math.sin(a) * rr, r: 2.6, fill: hairC, opacity: .8 }, bz); }
  }
  const cap = mk('g', { opacity: 0 }, H);
  mk('path', { d: 'M -132 -34 C -136 -152 -50 -178 14 -174 C 98 -170 140 -116 136 -34 C 90 -52 30 -62 -20 -58 C -70 -56 -108 -48 -132 -34 Z', fill: o.capCol || '#374151', ...LINE }, cap);
  mk('path', { d: 'M -10 -52 C 50 -72 124 -62 162 -38 C 130 -22 50 -30 -10 -46 Z', fill: '#1f2937', ...LINE }, cap);
  mk('circle', { cx: 14, cy: -174, r: 9, fill: '#4b5563', ...LINE }, cap);

  // сварочная маска: купол и откидное забрало с тёмно-зелёным стеклом (опускается на глаза по mask)
  const hel = mk('g', { opacity: 0 }, H);
  mk('path', { d: 'M -134 -30 C -140 -166 -40 -196 14 -192 C 104 -188 142 -124 138 -30 C 92 -50 30 -62 -20 -58 C -70 -56 -110 -46 -134 -30 Z', fill: '#6b7280', ...LINE }, hel);
  mk('path', { d: 'M -90 -150 C -50 -176 20 -182 70 -168', stroke: 'rgba(255,255,255,.35)', 'stroke-width': 12, 'stroke-linecap': 'round', fill: 'none' }, hel);
  const visor = mk('g', {}, hel);
  mk('rect', { x: -122, y: -58, width: 244, height: 118, rx: 22, fill: '#4b5563', ...LINE }, visor);
  mk('rect', { x: -98, y: -38, width: 196, height: 62, rx: 12, fill: '#0f2a1d', stroke: INK, 'stroke-width': 4 }, visor);
  mk('path', { d: 'M -80 -26 L -20 -26 L -50 14 Z', fill: 'rgba(255,255,255,.14)' }, visor);

  // реакция: когда эмоция меняется, герой вздрагивает (голова подпрыгивает, тело на миг вытягивается) — оживляет разговорные сцены
  const punch = o.punch !== undefined ? o.punch : MO.punch, moved = keys.map((k, i) => i > 0 && JSON.stringify(k.p) !== JSON.stringify(keys[i - 1].p));
  keys.forEach((k, i) => moved[i] && markChange(k.t));              // смена эмоции — тоже смена картинки
  const render = tau => {
    let bump = 0;
    if (punch) for (let k = 1; k < keys.length; k++) if (moved[k]) { const a = (tau - keys[k].t + .1) / .34; if (a >= 0 && a < 1) bump = Math.max(bump, Math.sin(a * Math.PI)); }
    const pk = punch * bump;
    const p = emoAt(keys, tau), tt = tau + seed, ph = tt % 3.3, blink = ph < .13 ? Math.sin(ph / .13 * Math.PI) : 0;
    B.setAttribute('transform', `translate(0 ${Math.sin(tt * 2.2) * 3 - pk * 120}) scale(${1 + pk * .6} ${1 + Math.sin(tt * 2.2) * .012 + pk * 1.2})`);
    hood.setAttribute('opacity', suit || armor ? 0 : 1 - p.rank); ov.setAttribute('opacity', suit || armor ? 0 : p.rank);
    H.setAttribute('transform', `translate(${p.shk ? Math.sin(tt * 46) * p.shk : 0} ${Math.sin(tt * 2.2 + 1) * 2 - pk * 220}) rotate(${p.r + (o.tilt || 0) + Math.sin(tt * 1.3) * 1.2})`);
    hair.setAttribute('opacity', (o.bald ? 0 : 1) * (1 - p.rank) * (1 - p.helm));
    hair.setAttribute('transform', `rotate(${Math.sin(tt * 2.6) * 1.4 * (1 + p.hair * 3)}) translate(0 ${-p.hair * 20}) scale(${1 + p.hair * .05} ${1 + p.hair * .15})`);
    cap.setAttribute('opacity', p.rank > .02 && p.helm < .5 ? 1 : 0);
    hel.setAttribute('opacity', p.helm > .02 ? 1 : 0); hel.setAttribute('transform', `translate(0 ${-(1 - p.helm) * 320 - 8})`);
    visor.setAttribute('transform', `rotate(${-150 * (1 - p.mask)} 0 -58)`); cap.setAttribute('transform', `translate(0 ${-(1 - p.rank) * 320 - 14})`);
    must.setAttribute('opacity', Math.max(p.rank, o.mustache || 0)); stub.setAttribute('opacity', p.rank * .6); nose.setAttribute('opacity', o.noNose ? 0 : p.rank * .55);
    glass.setAttribute('opacity', glasses * (1 - p.rank) * (1 - p.shades)); shades.setAttribute('opacity', p.shades);
    blush.forEach(b => b.setAttribute('opacity', p.blush * .45));
    sweat.setAttribute('opacity', p.sweat); sweat.setAttribute('transform', `translate(94 ${-92 + ((tt * .8) % 1) * 46}) scale(${.6 + p.sweat * .3})`);
    eyes.forEach((E, i) => {
      const sd = E.sd, open = Math.max(0, p.eo * (1 - blink) * (sd > 0 ? 1 - p.wink : 1)), ry = 35 * Math.max(1, p.eo), rx = 31 + Math.max(0, p.eo - 1) * 12;
      E.white.setAttribute('ry', ry); E.white.setAttribute('rx', rx);
      E.lid.setAttribute('y', -ry - 4); E.lid.setAttribute('height', Math.max(0, (1 - Math.min(open, 1)) * ry * 2 + 4));
      E.pup.setAttribute('transform', `translate(${p.px * 12} ${p.py * 10})`);
      E.line.setAttribute('opacity', Math.max(0, Math.min(1, (.3 - open) * 4)));
      E.bag.setAttribute('opacity', p.bags * .8);
      const by = -66 + p.by + (sd > 0 ? p.ba : 0), ox = sd * 94, ix = sd * 14, oy = by - p.bt * .35, iy = by + p.bt;
      brows[i].setAttribute('d', `M ${ox} ${oy} Q ${(ox + ix) / 2} ${(oy + iy) / 2 - 9} ${ix} ${iy}`);
      tears[i].forEach((t, k) => { const f = (tt * 1.5 + k * .5 + (sd > 0 ? .25 : 0)) % 1; t.setAttribute('cy', -8 + 30 + f * 150); t.setAttribute('opacity', p.tear * (1 - f) * .95); });
    });
    const d = `M ${-p.mw} ${p.mc} Q 0 ${p.mu} ${p.mw} ${p.mc} Q 0 ${p.ml} ${-p.mw} ${p.mc} Z`;
    mpath.setAttribute('d', d); cpath.setAttribute('d', d);
    const ty = (p.mc + p.mu) / 2 - 3;
    teeth.forEach((t, k) => { t.setAttribute('y', ty); t.setAttribute('opacity', p.teeth * (k === 2 || k === 3 ? 1 - p.gap : 1)); });
    tongue.setAttribute('cy', (p.mc + p.ml) / 2 - 7); tongue.setAttribute('rx', p.mw * .5);
    tongue.setAttribute('opacity', Math.max(0, Math.min(1, (p.ml - p.mu - 40) / 40)));
  };
  CUR.quiet = true;                                                 // герой обновляется каждый кадр, сменой картинки считаются только его события
  prog(q => render(t0 + q * (t1 - t0)), t0, t1 - t0, lin);
  CUR.quiet = false;
  return R;
}

// выбитый зуб: вылетает из точки (x, y) с кувырком и пропадает
function flyTooth(g, x, y, t0, dx, dy, spin) {
  const e = G(g, { x, y, r: 0, o: 0 });
  mk('rect', { x: -17, y: -22, width: 34, height: 44, rx: 9, fill: '#f8fafc', stroke: INK, 'stroke-width': 4 }, e);
  put(e, { o: 1 });
  tw(e, { x: x + dx, y: y + dy, r: spin }, t0, .75, out);
  tw(e, { o: 0 }, t0 + .5, .25, lin);
  return e;
}

// герой по имени из стиля (раздел «герои»); остальные настройки поверх пресета
function hero(g, name, x, y, s, keys, t0, t1, o = {}) {
  const look = (STYLE.characters || {})[name];
  if (!look) throw new Error(`Нет героя «${name}» в стиле. Есть: ${Object.keys(STYLE.characters || {}).join(', ') || '(пусто)'}`);
  return face(g, x, y, s, keys, t0, t1, Object.assign({}, look, o));
}

/* rigs.js — три способа построить и оживить героя, кроме обычного (characters.js). Выбирает стиль: манера → персонаж.

   Те же герои (цвета, очки, усы, доспех — из раздела «герои»), те же эмоции и те же вызовы face/hero/figure, но другое устройство и другое движение:
     каракуля   — линейный человечек; руки играют эмоцию: вскидывает при шоке, закрывает лицо при плаче, трясёт кулаками в ярости;
     марионетка — бумажные детали на шарнирах: форма деталей не меняется, меняются готовые рты и веки, всё сидит ступенями (анимация подменой, как в вырезной);
     желе       — всё тело пружинит после каждой реакции и колышется в покое.
   Рисуют они по-разному, а ведут себя одинаково: общее (вход, ключи эмоций, моргание, смена эмоции) делает actor() из characters.js.
   Метки для проверки те же: data-hero, data-body, data-head. Облик из стиля читается не весь: рисуются цвет кожи и волос, очки, усы, лысина, длинные волосы, кепка,
   цвет одежды, доспех (шипы на плечах), галстук, комплекция, цвет глаз. Коробка, татуировки и сварочная маска только у обычного героя. */
'use strict';

const kq = (v, step) => Math.round(v / step) * step;                   // сесть на ступень: у бумажных деталей нет промежуточных положений
const shadeHex = (hex, k) => '#' + [1, 3, 5].map(i => Math.round(parseInt(hex.slice(i, i + 2), 16) * k).toString(16).padStart(2, '0')).join('');
const bigHead = () => MN.headW !== 1 || MN.headH !== 1 ? ` scale(${MN.headW} ${MN.headH})` : '';

// облик героя из настроек: то, что читается издалека
function rigLook(o) {
  const hair = o.hair || HAIR_COL;
  return { skin: o.skin || SKIN, hair, glasses: o.glasses === undefined ? 1 : o.glasses, bald: !!o.bald, long: !!o.longHair, cap: o.capCol || '#374151',
    must: o.mustache || 0, mustCol: o.mustCol || hair, body: o.suit || (typeof o.armor === 'string' ? o.armor : '') || o.hoodCol || '#475569',
    armor: !!o.armor, cloak: o.armor ? (o.cloak || '#1e3a8a') : '', tie: o.suit ? o.tie : '', build: o.build || 1, eye: o.eyeCol || '', brow: o.browCol || hair };
}

// руки по эмоции: на сколько градусов повёрнута каждая от «висит вдоль тела» вокруг плеча. Первая — левая на экране, вторая — правая.
// «наружу» у левой — плюс, у правой — минус; «к лицу» — наоборот. Всё считается из тех же параметров эмоции, что и лицо
function armPose(p, tt) {
  const shock = clamp01((p.eo - 1) / .35), rage = clamp01(p.teeth * clamp01(p.bt / 24)), hands = clamp01(p.tear), think = clamp01(-p.py * 1.4), tired = clamp01((p.bags - .2) / .8);
  return [-1, 1].map(sd => {
    let away = 8 + 142 * shock + 38 * rage - 5 * tired + Math.sin(tt * 1.7 + sd * 1.3) * 3 + Math.sin(tt * 38 + sd) * 6 * rage, near = 140 * hands + (sd > 0 ? 125 * think : 0);
    return -sd * (away - near);
  });
}

// слёзы и пот одинаковы у всех: те же формулы, что у обычного героя
const dropPath = 'M 0 -18 C 14 2 14 16 0 16 C -14 16 -14 2 0 -18 Z';

// форма рта из параметров эмоции, как у обычного героя
const mouthD = p => `M ${-p.mw} ${p.mc} Q 0 ${p.mu} ${p.mw} ${p.mc} Q 0 ${p.ml} ${-p.mw} ${p.mc} Z`;

const RIGS = {};

// ============================== каракуля ==============================
RIGS.doodle = {
  face(g, x, y, s, keys, t0, t1, o = {}) {
    const A = actor(g, x, y, s, keys, t0, t1, o, 'doodle'), R = A.R, L = rigLook(o), neckUp = (MN.neck - 1) * 110;
    const pen = { stroke: INK, 'stroke-width': 8, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' };
    const B = mk('g', { 'data-body': 1 }, R);
    mk('path', { d: 'M -26 96 V 190 M 26 96 V 190', ...pen, fill: 'none' }, B);                                           // шея
    const torso = mk('g', {}, B);
    if (L.cloak) mk('path', { d: 'M -150 340 L -210 200 C -120 130 120 130 210 200 L 150 340 Z', fill: L.cloak, ...pen }, torso);
    mk('path', { d: 'M -150 340 C -150 238 -110 192 -48 180 Q 0 198 48 180 C 110 192 150 238 150 340 Z', fill: L.body, ...pen }, torso);
    if (L.tie) mk('path', { d: 'M -14 196 L 14 196 L 20 292 L 0 322 L -20 292 Z', fill: L.tie, ...pen }, torso);
    if (L.armor) [-1, 1].forEach(sd => mk('path', { d: `M ${sd * 96} 192 L ${sd * 176} 108 L ${sd * 168} 226 Z`, fill: '#94a3b8', ...pen }, torso));
    if (L.build !== 1) torso.setAttribute('transform', `scale(${L.build} 1)`);

    const H = mk('g', { 'data-head': 1 }, R);
    if (L.long) [-1, 1].forEach(sd => mk('path', { d: `M ${sd * 118} -40 C ${sd * 160} 60 ${sd * 150} 190 ${sd * 108} 224 L ${sd * 88} 190 L ${sd * 96} 20 Z`, fill: L.hair, ...pen }, H));
    [-1, 1].forEach(sd => mk('circle', { cx: sd * 118, cy: 10, r: 24, fill: L.skin, ...pen }, H));
    mk('circle', { r: 120, fill: L.skin, ...pen }, H);
    const blush = [-1, 1].map(sd => mk('path', { d: `M ${sd * 74} 32 l ${sd * 20} -8 M ${sd * 66} 48 l ${sd * 20} -8 M ${sd * 58} 64 l ${sd * 20} -8`, stroke: '#ef4444', 'stroke-width': 6, 'stroke-linecap': 'round', fill: 'none', opacity: 0 }, H));
    mk('path', { d: 'M 3 4 L 15 34 L -3 34', stroke: INK, 'stroke-width': 6, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', fill: 'none' }, H);
    const eyes = [-1, 1].map(sd => {
      const e = mk('g', { transform: `translate(${sd * 50} -8)` }, H), pup = mk('g', {}, e);
      return { sd, dot: mk('ellipse', { rx: 14, ry: 14, fill: L.eye || INK }, pup), pup };
    });
    const brows = [-1, 1].map(() => mk('path', { stroke: INK, 'stroke-width': 10, 'stroke-linecap': 'round', fill: 'none' }, H));
    const glass = mk('g', { opacity: L.glasses }, H);
    [-1, 1].forEach(sd => mk('circle', { cx: sd * 52, cy: -8, r: 44, fill: 'none', ...pen, 'stroke-width': 7 }, glass));
    mk('path', { d: 'M -8 -14 Q 0 -22 8 -14', ...pen, 'stroke-width': 7, fill: 'none' }, glass);
    const mouth = mk('path', { stroke: INK, 'stroke-width': 8, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', fill: '#7f1d1d', 'fill-opacity': 0, transform: 'translate(0 78)' }, H);
    const must = mk('path', { d: 'M -64 54 C -50 34 -14 38 0 52 C 14 38 50 34 64 54 C 48 74 16 66 0 58 C -16 66 -48 74 -64 54 Z', fill: L.mustCol, ...pen, 'stroke-width': 5, opacity: L.must ? 1 : 0 }, H);
    const tears = [-1, 1].map(sd => [0, 1].map(i => mk('ellipse', { rx: 8, ry: 12, fill: '#7dd3fc', opacity: 0, cx: sd * 58 + (i ? 7 : -7) }, H)));
    const sweat = mk('path', { d: dropPath, fill: '#7dd3fc', stroke: INK, 'stroke-width': 4, opacity: 0 }, H);
    const hair = mk('g', { opacity: L.bald ? 0 : 1 }, H);
    mk('path', { d: 'M -120 -36 C -112 -124 -60 -152 0 -152 C 60 -152 112 -124 120 -36 C 92 -80 40 -94 0 -92 C -40 -94 -92 -80 -120 -36 Z', fill: L.hair, ...pen }, hair);
    if (!L.long) mk('path', { d: 'M -70 -130 L -94 -200 L -30 -144 Z M -6 -150 L 4 -218 L 40 -146 Z M 60 -134 L 108 -192 L 100 -114 Z', fill: L.hair, ...pen }, hair);
    const cap = mk('g', { opacity: 0 }, H);
    mk('path', { d: 'M -124 -44 C -124 -150 124 -150 124 -44 C 60 -66 -60 -66 -124 -44 Z', fill: L.cap, ...pen }, cap);
    mk('path', { d: 'M 30 -58 L 160 -46 L 36 -28 Z', fill: shadeHex(L.cap, .7), ...pen }, cap);

    const AR = mk('g', {}, R);                                          // руки поверх головы: при плаче ладони закрывают лицо
    const arms = [-1, 1].map(sd => {
      const a = mk('g', { 'data-arm': 1 }, AR);
      mk('path', { d: 'M 0 0 L 0 150', ...pen, 'stroke-width': 10, fill: 'none' }, a);
      mk('circle', { cy: 164, r: 20, fill: L.skin, ...pen, 'stroke-width': 7 }, a);
      return a;
    });

    A.run(({ p, tt, blink, pk }) => {
      const bt = `translate(0 ${Math.sin(tt * 2.2) * 3 - pk * 120 + neckUp}) scale(${(1 + pk * .6) * MN.body} ${1 + pk * 1.2})`;
      B.setAttribute('transform', bt); AR.setAttribute('transform', bt);
      H.setAttribute('transform', `translate(${p.shk ? Math.sin(tt * 46) * p.shk : 0} ${Math.sin(tt * 2.2 + 1) * 2 - pk * 220 + neckUp}) rotate(${p.r + (o.tilt || 0) + Math.sin(tt * 1.3) * 1.2})${bigHead()}`);
      const pose = armPose(p, tt);
      arms.forEach((a, i) => a.setAttribute('transform', `translate(${(i ? 1 : -1) * 120 * L.build * MN.body} 214) rotate(${num(pose[i])})`));
      hair.setAttribute('opacity', (L.bald ? 0 : 1) * (1 - p.rank));
      hair.setAttribute('transform', `translate(0 ${-p.hair * 24}) scale(${1 + p.hair * .05} ${1 + p.hair * .15})`);
      cap.setAttribute('opacity', p.rank > .5 ? 1 : 0);
      must.setAttribute('opacity', Math.max(p.rank > .5 ? 1 : 0, L.must ? 1 : 0));
      glass.setAttribute('opacity', L.glasses * (1 - p.rank) * (1 - p.shades));
      blush.forEach(b => b.setAttribute('opacity', p.blush * .8));
      sweat.setAttribute('opacity', p.sweat); sweat.setAttribute('transform', `translate(96 ${-92 + ((tt * .8) % 1) * 46})`);
      eyes.forEach((E, i) => {
        const open = Math.max(.1, p.eo * (1 - blink) * (E.sd > 0 ? 1 - p.wink : 1));
        E.dot.setAttribute('ry', 14 * Math.min(1.5, open)); E.dot.setAttribute('rx', 14 * Math.max(1, Math.min(1.4, p.eo)));
        E.pup.setAttribute('transform', `translate(${p.px * 14} ${p.py * 12})`);
        const by = -66 + p.by + (E.sd > 0 ? p.ba : 0), ox = E.sd * 96, ix = E.sd * 14, oy = by - p.bt * .35, iy = by + p.bt;
        brows[i].setAttribute('d', `M ${ox} ${oy} Q ${(ox + ix) / 2} ${(oy + iy) / 2 - 9} ${ix} ${iy}`);
        tears[i].forEach((t, k) => { const f = (tt * 1.5 + k * .5 + (E.sd > 0 ? .25 : 0)) % 1; t.setAttribute('cy', 22 + f * 150); t.setAttribute('opacity', p.tear * (1 - f) * .95); });
      });
      mouth.setAttribute('d', mouthD(p)); mouth.setAttribute('fill-opacity', clamp01((p.ml - p.mu - 24) / 30));
    });
    return R;
  },

  // человечек-палочка целиком: ноги и руки — линии, голова — кружок
  figure(g, name, x, y, s = .5, o = {}) {
    const c = tones(name), moving = o.to !== undefined, dir = moving ? Math.sign(o.to - x) || 1 : 0, t0 = o.t0 || 0, t1 = o.t1 === undefined ? t0 + 2 : o.t1;
    const rate = o.run ? 10 : 6, amp = o.run ? 42 : 26, ph0 = o.phase || 0;
    const e = G(g, { x, y, s });
    e.setAttribute('data-hero', '1'); e.setAttribute('data-rig', 'doodle');
    const pen = { stroke: INK, 'stroke-width': 11, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', fill: 'none' };
    const body = mk('g', { 'data-body': 1 }, e);
    const limb = (px, py, len, leg) => { const l = mk('g', leg ? { 'data-leg': 1 } : {}, body); mk('path', { d: `M ${px} ${py} L ${px} ${py + len}`, ...pen }, l); return l; };
    const legB = limb(-28, -250, 250, true), legF = limb(28, -250, 250, true), armB = limb(-46, -420, 170), armF = limb(46, -420, 170);
    mk('path', { d: 'M -50 -440 L -64 -250 L 64 -250 L 50 -440 Z', fill: c.body, ...pen }, body);
    const head = mk('g', { 'data-head': 1, transform: `translate(0 -520) scale(${MN.headW} ${MN.headH}) translate(0 520)` }, body);
    if (c.long) mk('path', { d: 'M -76 -560 C -104 -470 -92 -420 -70 -400 L 70 -400 C 92 -420 104 -470 76 -560 Z', fill: c.hair, ...pen }, head);
    mk('circle', { cy: -520, r: 76, fill: c.skin, ...pen, 'stroke-width': 9 }, head);
    [-1, 1].forEach(sd => mk('circle', { cx: dir * 14 + sd * 28, cy: -530, r: 9, fill: o.eye || INK }, head));
    mk('path', { d: `M ${dir * 14 - 22} -490 Q ${dir * 14} ${o.grin ? -462 : -484} ${dir * 14 + 22} -490`, ...pen, 'stroke-width': 7 }, head);
    if (c.glasses) [-1, 1].forEach(sd => mk('circle', { cx: dir * 14 + sd * 28, cy: -530, r: 25, ...pen, 'stroke-width': 6 }, head));
    if (c.o.mustache) mk('path', { d: `M ${dir * 14 - 32} -494 Q ${dir * 14} -516 ${dir * 14 + 32} -494 Q ${dir * 14} -500 ${dir * 14 - 32} -494 Z`, fill: c.hair, ...pen, 'stroke-width': 5 }, head);
    if (c.cap) mk('path', { d: 'M -78 -548 C -80 -632 80 -632 78 -548 C 40 -566 -40 -566 -78 -548 Z', fill: c.cap, ...pen, 'stroke-width': 7 }, head);
    else if (!c.bald) mk('path', { d: 'M -78 -540 C -86 -626 86 -626 78 -540 L 52 -566 L 30 -540 L 6 -574 L -16 -540 L -42 -572 Z', fill: c.hair, ...pen, 'stroke-width': 7 }, head);
    if (moving) tw(e, { x: o.to }, t0, t1 - t0, lin);
    tick(t => {
      const on = moving && t >= t0 && t <= t1, ph = (t - t0) * rate + ph0, a = on ? Math.sin(ph) * amp : 0;
      legF.setAttribute('transform', `rotate(${num(a)} 28 -250)`); legB.setAttribute('transform', `rotate(${num(-a)} -28 -250)`);
      armF.setAttribute('transform', `rotate(${num(-a * .9)} 46 -420)`); armB.setAttribute('transform', `rotate(${num(a * .9)} -46 -420)`);
      const lift = on ? Math.abs(Math.sin(ph)) * 16 : Math.sin(t * 2 + ph0) * 3, lean = on && o.run ? dir * 10 : 0;
      body.setAttribute('transform', `translate(0 ${num(-lift)}) rotate(${lean} 0 -250)`);
    });
    return e;
  },
};

// ============================== марионетка ==============================
// Бумажные детали на шарнирах. Ничего не гнётся: деталь только едет и поворачивается ступенями; выражение лица — это какой из готовых ртов и какое веко сейчас на месте.
RIGS.puppet = {
  face(g, x, y, s, keys, t0, t1, o = {}) {
    const A = actor(g, x, y, s, keys, t0, t1, o, 'puppet'), R = A.R, L = rigLook(o), neckUp = (MN.neck - 1) * 110;
    const edge = { stroke: INK, 'stroke-width': 6, 'stroke-linejoin': 'round' };
    const card = (parent, tag, attrs) => {                              // деталь из бумаги: тень чуть ниже и правее, сверху сама деталь
      mk(tag, { ...attrs, fill: 'rgba(0,0,0,.3)', transform: 'translate(8 11)' }, parent);
      return mk(tag, { ...attrs, ...edge }, parent);
    };
    const B = mk('g', { 'data-body': 1 }, R);
    card(B, 'rect', { x: -34, y: 92, width: 68, height: 112, rx: 12, fill: shadeHex(L.skin, .9) });
    if (L.cloak) card(B, 'path', { d: 'M -200 340 L -240 196 Q 0 120 240 196 L 200 340 Z', fill: L.cloak });
    card(B, 'path', { d: 'M -176 340 L -128 188 Q 0 160 128 188 L 176 340 Z', fill: L.body });
    if (L.tie) card(B, 'path', { d: 'M -16 196 L 16 196 L 24 300 L 0 336 L -24 300 Z', fill: L.tie });
    if (L.armor) [-1, 1].forEach(sd => card(B, 'path', { d: `M ${sd * 110} 190 L ${sd * 190} 100 L ${sd * 170} 226 Z`, fill: '#94a3b8' }));

    const H = mk('g', { 'data-head': 1 }, R);
    if (L.long) [-1, 1].forEach(sd => card(H, 'path', { d: `M ${sd * 120} -40 C ${sd * 164} 60 ${sd * 152} 190 ${sd * 108} 226 L ${sd * 86} 190 L ${sd * 96} 20 Z`, fill: L.hair }));
    [-1, 1].forEach(sd => card(H, 'circle', { cx: sd * 126, cy: 10, r: 26, fill: L.skin }));
    card(H, 'ellipse', { cx: 0, cy: 0, rx: 128, ry: 122, fill: L.skin });
    const blush = [-1, 1].map(sd => mk('ellipse', { cx: sd * 82, cy: 44, rx: 28, ry: 18, fill: '#ef4444', opacity: 0 }, H));
    mk('path', { d: 'M 2 0 L 18 34 L -6 34 Z', fill: shadeHex(L.skin, .85), ...edge, 'stroke-width': 4 }, H);

    const eyes = [-1, 1].map(sd => {                                    // глаз: белая деталь, зрачок-картонка и веко в одном из четырёх положений
      const E = mk('g', { transform: `translate(${sd * 52} -8)` }, H), cid = `mpe${A.id}${sd > 0 ? 'r' : 'l'}`;
      mk('ellipse', { rx: 34, ry: 38, fill: '#fff', ...edge, 'stroke-width': 5 }, E);
      const pupil = mk('g', {}, E);                                       // зрачок поверх белка, веко поверх зрачка
      mk('circle', { r: 12, fill: L.eye || INK }, pupil);
      mk('ellipse', { rx: 34, ry: 38 }, mk('clipPath', { id: cid }, E));
      const lidBox = mk('g', { 'clip-path': `url(#${cid})` }, E), lid = mk('g', { 'data-lid': 1 }, lidBox);
      mk('rect', { x: -40, y: -90, width: 80, height: 90, fill: L.skin }, lid);
      mk('path', { d: 'M -40 0 H 40', stroke: INK, 'stroke-width': 5 }, lid);
      return { sd, E, pupil, lid };
    });
    const brows = [-1, 1].map(sd => { const b = mk('g', {}, H); mk('rect', { x: -40, y: -9, width: 80, height: 18, rx: 9, fill: L.brow }, b); return { sd, b }; });
    const glass = mk('g', { opacity: L.glasses }, H);
    [-1, 1].forEach(sd => mk('circle', { cx: sd * 52, cy: -8, r: 46, fill: 'rgba(255,255,255,.12)', ...edge, 'stroke-width': 7 }, glass));
    mk('path', { d: 'M -6 -12 Q 0 -20 6 -12', ...edge, 'stroke-width': 7, fill: 'none' }, glass);

    // готовые рты: в каждый момент виден ровно один, переключение мгновенное
    const MOUTHS = ['line', 'smile', 'frown', 'open', 'grin', 'shout'], dark = '#4a1414';
    const mouthG = mk('g', { transform: 'translate(0 80)' }, H), mouths = MOUTHS.map(() => mk('g', { 'data-mouth': 1, opacity: 0 }, mouthG));
    mk('rect', { x: -40, y: -5, width: 80, height: 11, rx: 5.5, fill: INK }, mouths[0]);
    mk('path', { d: 'M -54 -10 Q 0 38 54 -10', ...edge, 'stroke-width': 11, fill: 'none', 'stroke-linecap': 'round' }, mouths[1]);
    mk('path', { d: 'M -50 18 Q 0 -28 50 18', ...edge, 'stroke-width': 11, fill: 'none', 'stroke-linecap': 'round' }, mouths[2]);
    mk('ellipse', { cy: 6, rx: 38, ry: 32, fill: dark, ...edge }, mouths[3]); mk('ellipse', { cy: 20, rx: 22, ry: 11, fill: '#f43f5e' }, mouths[3]);
    mk('path', { d: 'M -68 -8 Q 0 84 68 -8 Z', fill: dark, ...edge }, mouths[4]); mk('rect', { x: -52, y: -6, width: 104, height: 20, rx: 6, fill: '#f8fafc' }, mouths[4]);
    mk('ellipse', { cy: 6, rx: 56, ry: 50, fill: dark, ...edge }, mouths[5]); mk('rect', { x: -42, y: -36, width: 84, height: 20, rx: 6, fill: '#f8fafc' }, mouths[5]); mk('ellipse', { cy: 30, rx: 28, ry: 14, fill: '#f43f5e' }, mouths[5]);
    const pick = p => {
      const open = p.ml - p.mu, curve = (p.mu + p.ml) / 2 - p.mc;
      if (open >= 75) return 5;
      if (open >= 40) return curve > 20 ? 4 : 3;
      if (open >= 14) return 3;
      return curve > 14 ? 1 : curve < -8 ? 2 : 0;
    };
    const must = mk('path', { d: 'M -66 56 C -52 36 -14 40 0 54 C 14 40 52 36 66 56 C 50 78 16 70 0 62 C -16 70 -50 78 -66 56 Z', fill: L.mustCol, ...edge, 'stroke-width': 4, opacity: 0 }, H);
    const tears = [-1, 1].map(sd => mk('ellipse', { cx: sd * 60, cy: 20, rx: 9, ry: 14, fill: '#7dd3fc', opacity: 0 }, H));
    const sweat = mk('path', { d: dropPath, fill: '#7dd3fc', ...edge, 'stroke-width': 4, opacity: 0 }, H);
    const hair = mk('g', {}, H);
    card(hair, 'path', { d: 'M -128 -30 C -124 -132 -64 -156 0 -156 C 64 -156 124 -132 128 -30 C 96 -80 40 -96 0 -94 C -40 -96 -96 -80 -128 -30 Z', fill: L.hair });
    if (!L.long) card(hair, 'path', { d: 'M -72 -134 L -98 -206 L -30 -148 Z M -6 -152 L 4 -224 L 42 -150 Z M 62 -138 L 112 -198 L 104 -116 Z', fill: L.hair });
    const cap = mk('g', { opacity: 0 }, H);
    card(cap, 'path', { d: 'M -132 -42 C -132 -156 132 -156 132 -42 C 62 -66 -62 -66 -132 -42 Z', fill: L.cap });
    card(cap, 'path', { d: 'M 30 -58 L 166 -44 L 36 -26 Z', fill: shadeHex(L.cap, .7) });

    const AR = mk('g', {}, R);
    const arms = [-1, 1].map(sd => { const a = mk('g', { 'data-arm': 1 }, AR); card(a, 'rect', { x: -24, y: -6, width: 48, height: 168, rx: 22, fill: L.body }); card(a, 'circle', { cy: 170, r: 26, fill: L.skin }); return a; });

    A.run(({ p, tt, blink, pk }) => {
      const rock = [-2, 0, 2, 0][Math.floor(tt * 3) % 4];                // кукла на палочке: качается четырьмя положениями, а не плавно
      const lift = kq(-pk * 60, 30) + neckUp, bt = `translate(0 ${lift}) scale(${MN.body * L.build} 1)`;
      B.setAttribute('transform', bt); AR.setAttribute('transform', bt);
      H.setAttribute('transform', `translate(${p.shk ? Math.sign(Math.sin(tt * 46)) * p.shk * 1.5 : 0} ${kq(-pk * 100, 50) + neckUp}) rotate(${kq(p.r + (o.tilt || 0), 4) + rock})${bigHead()}`);
      const pose = armPose(p, tt);
      arms.forEach((a, i) => a.setAttribute('transform', `translate(${(i ? 1 : -1) * 150 * L.build * MN.body} 206) rotate(${kq(pose[i], 12)})`));
      hair.setAttribute('opacity', (L.bald ? 0 : 1) * (p.rank > .5 ? 0 : 1)); hair.setAttribute('transform', `translate(0 ${-kq(p.hair * 28, 14)})`);
      cap.setAttribute('opacity', p.rank > .5 ? 1 : 0);
      must.setAttribute('opacity', p.rank > .5 || L.must ? 1 : 0);
      glass.setAttribute('opacity', p.rank > .5 || p.shades > .5 ? 0 : L.glasses);
      blush.forEach(b => b.setAttribute('opacity', p.blush > .4 ? .55 : 0));
      sweat.setAttribute('opacity', p.sweat > .5 ? 1 : 0); sweat.setAttribute('transform', `translate(100 ${-90 + Math.floor((tt * .8) % 1 * 3) * 22})`);
      eyes.forEach((E, i) => {
        const open = p.eo * (1 - (blink > .5 ? 1 : 0)) * (E.sd > 0 ? 1 - p.wink : 1);
        const edgeY = open >= .9 ? -46 : open >= .65 ? -20 : open >= .35 ? 2 : 44;       // нижний край века: открыт, прищур, сонный, закрыт
        E.lid.setAttribute('transform', `translate(0 ${edgeY})`);
        const wide = p.eo > 1.15 ? 1.14 : 1;
        E.E.setAttribute('transform', `translate(${E.sd * 52} -8) scale(${wide})`);
        E.pupil.setAttribute('transform', `translate(${kq(p.px * 12, 6)} ${kq(p.py * 12, 6)})`);
        const a = kq(Math.atan2(p.bt * 1.35, 80) * 57.3, 8), by = kq(-66 + p.by + (E.sd > 0 ? p.ba : 0) - p.bt * .2, 6);
        brows[i].b.setAttribute('transform', `translate(${E.sd * 56} ${by}) rotate(${-E.sd * a})`);
        const f = Math.floor((tt * 1.5 + (E.sd > 0 ? .25 : 0)) % 1 * 4) / 4;
        tears[i].setAttribute('opacity', p.tear > .5 ? 1 : 0); tears[i].setAttribute('transform', `translate(0 ${f * 150})`);
      });
      const w = pick(p);
      mouths.forEach((m, i) => m.setAttribute('opacity', i === w ? 1 : 0));
    });
    return R;
  },

  // бумажная кукла целиком: ноги не гнутся, ходит раскачиваясь с ноги на ногу
  figure(g, name, x, y, s = .5, o = {}) {
    const c = tones(name), moving = o.to !== undefined, dir = moving ? Math.sign(o.to - x) || 1 : 0, t0 = o.t0 || 0, t1 = o.t1 === undefined ? t0 + 2 : o.t1;
    const rate = o.run ? 5 : 3, ph0 = o.phase || 0, edge = { stroke: INK, 'stroke-width': 6, 'stroke-linejoin': 'round' };
    const e = G(g, { x, y, s });
    e.setAttribute('data-hero', '1'); e.setAttribute('data-rig', 'puppet');
    const card = (parent, tag, attrs) => { mk(tag, { ...attrs, fill: 'rgba(0,0,0,.3)', transform: 'translate(8 10)' }, parent); return mk(tag, { ...attrs, ...edge }, parent); };
    const body = mk('g', { 'data-body': 1 }, e);
    [-1, 1].forEach(sd => { const l = mk('g', { 'data-leg': 1 }, body); card(l, 'rect', { x: sd * 32 - 26, y: -250, width: 52, height: 236, rx: 16, fill: sd < 0 ? '#1f2937' : '#273449' }); card(l, 'ellipse', { cx: sd * 32 + dir * 14, cy: -12, rx: 44, ry: 20, fill: '#111827' }); });
    card(body, 'path', { d: 'M -78 -250 L -62 -440 Q 0 -460 62 -440 L 78 -250 Z', fill: c.body });
    const armB = mk('g', {}, body), armF = mk('g', {}, body);
    [armB, armF].forEach((a, i) => card(a, 'rect', { x: (i ? 1 : -1) * 78 - 20, y: -430, width: 40, height: 170, rx: 18, fill: c.o.arms ? c.skin : c.body }));
    const head = mk('g', { 'data-head': 1, transform: `translate(0 -520) scale(${MN.headW} ${MN.headH}) translate(0 520)` }, body);
    if (c.long) card(head, 'path', { d: 'M -100 -560 C -124 -470 -112 -400 -84 -386 L 84 -386 C 112 -400 124 -470 100 -560 Z', fill: c.hair });
    card(head, 'ellipse', { cx: 0, cy: -520, rx: 98, ry: 92, fill: c.skin });
    [-1, 1].forEach(sd => mk('circle', { cx: dir * 14 + sd * 34, cy: -530, r: 10, fill: o.eye || INK }, head));
    mk('rect', { x: dir * 14 - 22, y: -494, width: 44, height: 9, rx: 4.5, fill: INK }, head);
    if (c.glasses) [-1, 1].forEach(sd => mk('circle', { cx: dir * 14 + sd * 34, cy: -530, r: 28, fill: 'none', ...edge, 'stroke-width': 6 }, head));
    if (c.o.mustache) mk('path', { d: `M ${dir * 14 - 36} -494 Q ${dir * 14} -518 ${dir * 14 + 36} -494 Q ${dir * 14} -500 ${dir * 14 - 36} -494 Z`, fill: c.hair, ...edge, 'stroke-width': 4 }, head);
    if (c.cap) card(head, 'path', { d: 'M -100 -548 C -104 -640 100 -640 100 -548 C 52 -566 -52 -566 -100 -548 Z', fill: c.cap });
    else if (!c.bald) card(head, 'path', { d: 'M -100 -540 C -110 -644 110 -644 100 -540 C 70 -576 -70 -576 -100 -540 Z M -46 -604 L -62 -652 L -12 -614 Z M 8 -616 L 6 -664 L 44 -610 Z', fill: c.hair });
    if (moving) tw(e, { x: o.to }, t0, t1 - t0, lin);
    tick(t => {
      const on = moving && t >= t0 && t <= t1, step = Math.floor(((t - t0) * rate + ph0 / 3) * 2), side = step % 2 ? 1 : -1;
      const rock = on ? side * (o.run ? 9 : 6) : [-2, 0, 2, 0][Math.floor(t * 3 + ph0) % 4];
      armF.setAttribute('transform', `rotate(${on ? -side * 12 : 0} 78 -430)`); armB.setAttribute('transform', `rotate(${on ? side * 12 : 0} -78 -430)`);
      body.setAttribute('transform', `translate(0 ${on && side > 0 ? -8 : 0}) rotate(${rock} 0 0)`);
    });
    return e;
  },
};

// ============================== желе ==============================
// Колобок: голова и тело — один пружинящий комок. После каждой смены эмоции тело вытягивается, сжимается и качается, затухая; в покое колышется.
const jig = since => since === Infinity ? 0 : Math.exp(-4.4 * since) * Math.sin(2 * Math.PI * 2.4 * since);
RIGS.jelly = {
  face(g, x, y, s, keys, t0, t1, o = {}) {
    const A = actor(g, x, y, s, keys, t0, t1, o, 'jelly'), R = A.R, L = rigLook(o), neckUp = (MN.neck - 1) * 110;
    const edge = { stroke: INK, 'stroke-width': 9, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' };
    const B = mk('g', { 'data-body': 1 }, R);                           // всё желе целиком: сжимается вокруг точки у пояса
    const arms = [-1, 1].map(sd => {                                    // толстые короткие ручки, запаздывают за телом
      const a = mk('g', { 'data-arm': 1 }, B);
      mk('path', { d: 'M 0 0 L 0 112', stroke: INK, 'stroke-width': 58, 'stroke-linecap': 'round', fill: 'none' }, a);
      mk('path', { d: 'M 0 0 L 0 112', stroke: o.arms ? L.skin : L.body, 'stroke-width': 44, 'stroke-linecap': 'round', fill: 'none' }, a);
      return a;
    });
    if (L.cloak) mk('path', { d: 'M -200 340 C -230 220 -150 150 0 146 C 150 150 230 220 200 340 Z', fill: L.cloak, ...edge }, B);
    mk('path', { d: 'M -184 340 C -196 224 -126 172 0 166 C 126 172 196 224 184 340 Z', fill: L.body, ...edge }, B);
    mk('ellipse', { cx: -80, cy: 232, rx: 22, ry: 40, fill: '#fff', opacity: .18, transform: 'rotate(18 -80 232)' }, B);
    if (L.tie) mk('path', { d: 'M -18 190 L 18 190 L 26 296 L 0 330 L -26 296 Z', fill: L.tie, ...edge, 'stroke-width': 6 }, B);
    if (L.armor) [-1, 1].forEach(sd => mk('path', { d: `M ${sd * 110} 180 L ${sd * 190} 96 L ${sd * 176} 224 Z`, fill: '#94a3b8', ...edge, 'stroke-width': 6 }, B));

    const H = mk('g', { 'data-head': 1 }, B);
    const blob = 'M 0 -126 C 78 -126 136 -76 138 -4 C 140 74 84 124 0 124 C -84 124 -140 74 -138 -4 C -136 -76 -78 -126 0 -126 Z';
    if (L.long) [-1, 1].forEach(sd => mk('path', { d: `M ${sd * 124} -50 C ${sd * 176} 70 ${sd * 160} 190 ${sd * 110} 230 L ${sd * 84} 186 L ${sd * 98} 20 Z`, fill: L.hair, ...edge }, H));
    mk('path', { d: blob, fill: L.skin, ...edge }, H);
    mk('ellipse', { cx: -64, cy: -74, rx: 30, ry: 16, fill: '#fff', opacity: .4, transform: 'rotate(-24 -64 -74)' }, H);
    const cheeks = [-1, 1].map(sd => mk('ellipse', { cx: sd * 92, cy: 46, rx: 30, ry: 20, fill: '#fb7185', opacity: .25 }, H));
    const eyes = [-1, 1].map(sd => {                                    // крупные блестящие глаза
      const e = mk('g', { transform: `translate(${sd * 52} -10)` }, H);
      const white = mk('ellipse', { rx: 40, ry: 44, fill: '#fff', ...edge, 'stroke-width': 6 }, e), pup = mk('g', {}, e);
      mk('circle', { r: 21, fill: L.eye || '#1c1917' }, pup); mk('circle', { cx: 7, cy: -8, r: 7, fill: '#fff' }, pup);
      const lid = mk('rect', { x: -46, y: -48, width: 92, height: 0, fill: L.skin }, e);
      return { sd, white, pup, lid };
    });
    const brows = [-1, 1].map(() => mk('path', { stroke: L.brow, 'stroke-width': 19, 'stroke-linecap': 'round', fill: 'none' }, H));
    const glass = mk('g', { opacity: L.glasses }, H);
    [-1, 1].forEach(sd => mk('circle', { cx: sd * 52, cy: -10, r: 54, fill: 'rgba(255,255,255,.1)', stroke: '#1e293b', 'stroke-width': 8 }, glass));
    mk('path', { d: 'M -4 -14 Q 0 -22 4 -14', stroke: '#1e293b', 'stroke-width': 8, fill: 'none' }, glass);
    const mouthG = mk('g', { transform: 'translate(0 80)' }, H);
    const mpath = mk('path', { fill: '#5b1a1a', ...edge, 'stroke-width': 8 }, mouthG), tongue = mk('ellipse', { rx: 30, ry: 14, fill: '#f43f5e', opacity: 0 }, mouthG);
    const must = mk('path', { d: 'M -70 52 C -54 30 -16 36 0 52 C 16 36 54 30 70 52 C 54 80 16 70 0 62 C -16 70 -54 80 -70 52 Z', fill: L.mustCol, ...edge, 'stroke-width': 5, opacity: 0 }, H);
    const tears = [-1, 1].map(sd => [0, 1].map(i => mk('ellipse', { rx: 9, ry: 14, fill: '#7dd3fc', opacity: 0, cx: sd * 60 + (i ? 8 : -8) }, H)));
    const sweat = mk('path', { d: dropPath, fill: '#7dd3fc', stroke: INK, 'stroke-width': 4, opacity: 0 }, H);
    const hair = mk('g', { opacity: L.bald ? 0 : 1 }, H);
    mk('path', { d: 'M -122 -50 C -128 -150 -40 -170 0 -150 C 40 -178 128 -150 122 -50 C 96 -96 48 -108 0 -102 C -48 -108 -96 -96 -122 -50 Z', fill: L.hair, ...edge }, hair);
    mk('path', { d: 'M -20 -146 C -24 -186 6 -214 30 -206 C 20 -192 22 -170 24 -146 Z', fill: L.hair, ...edge, 'stroke-width': 7 }, hair);
    const cap = mk('g', { opacity: 0 }, H);
    mk('path', { d: 'M -132 -50 C -134 -168 134 -168 132 -50 C 64 -76 -64 -76 -132 -50 Z', fill: L.cap, ...edge }, cap);
    mk('path', { d: 'M 30 -66 L 168 -50 L 36 -30 Z', fill: shadeHex(L.cap, .7), ...edge }, cap);

    A.run(({ p, tt, blink, pk, since }) => {
      const d = .3 * jig(since) + .03 * Math.sin(2 * Math.PI * 1.5 * tt) + pk * .5, sx = (1 - d * .75) * MN.body * L.build, sy = 1 + d;
      B.setAttribute('transform', `translate(0 ${neckUp}) translate(0 300) scale(${num(sx)} ${num(sy)}) translate(0 -300)`);
      const lag = jig(since === Infinity ? since : since - .07);
      H.setAttribute('transform', `translate(${p.shk ? Math.sin(tt * 46) * p.shk : 0} ${-pk * 120}) rotate(${p.r + (o.tilt || 0) + Math.sin(tt * 1.3 + 1) * 2 + lag * 7})${bigHead()}`);
      const pose = armPose(p, tt);
      arms.forEach((a, i) => a.setAttribute('transform', `translate(${(i ? 1 : -1) * 160} 232) rotate(${num(pose[i] + lag * 26 * (i ? -1 : 1))})`));
      hair.setAttribute('opacity', (L.bald ? 0 : 1) * (1 - p.rank) * (1 - p.helm));
      hair.setAttribute('transform', `rotate(${-lag * 14 + Math.sin(tt * 2.6) * 2}) translate(0 ${-p.hair * 24})`);
      cap.setAttribute('opacity', p.rank > .5 ? 1 : 0); must.setAttribute('opacity', Math.max(p.rank, L.must ? 1 : 0));
      glass.setAttribute('opacity', L.glasses * (1 - p.rank) * (1 - p.shades));
      cheeks.forEach(c => c.setAttribute('opacity', .25 + p.blush * .5));
      sweat.setAttribute('opacity', p.sweat); sweat.setAttribute('transform', `translate(100 ${-96 + ((tt * .8) % 1) * 46})`);
      eyes.forEach((E, i) => {
        const open = Math.max(0, p.eo * (1 - blink) * (E.sd > 0 ? 1 - p.wink : 1)), ry = 44 * Math.max(1, p.eo), rx = 40 + Math.max(0, p.eo - 1) * 14;
        E.white.setAttribute('ry', ry); E.white.setAttribute('rx', rx);
        E.lid.setAttribute('y', -ry - 4); E.lid.setAttribute('height', Math.max(0, (1 - Math.min(open, 1)) * ry * 2 + 4));
        E.pup.setAttribute('transform', `translate(${p.px * 14} ${p.py * 12})`);
        const by = -72 + p.by + (E.sd > 0 ? p.ba : 0), ox = E.sd * 96, ix = E.sd * 16, oy = by - p.bt * .35, iy = by + p.bt;
        brows[i].setAttribute('d', `M ${ox} ${oy} Q ${(ox + ix) / 2} ${(oy + iy) / 2 - 10} ${ix} ${iy}`);
        tears[i].forEach((t, k) => { const f = (tt * 1.5 + k * .5 + (E.sd > 0 ? .25 : 0)) % 1; t.setAttribute('cy', 24 + f * 150); t.setAttribute('opacity', p.tear * (1 - f) * .95); });
      });
      const m = { ...p, mw: p.mw * 1.15, mu: p.mu * 1.2, ml: p.ml * 1.2 };
      mpath.setAttribute('d', mouthD(m));
      tongue.setAttribute('cy', (m.mc + m.ml) / 2 - 7); tongue.setAttribute('rx', m.mw * .45); tongue.setAttribute('opacity', clamp01((m.ml - m.mu - 40) / 40));
    });
    return R;
  },

  // колобок целиком: прыгает вместо шагов, на приземлении сплющивается
  figure(g, name, x, y, s = .5, o = {}) {
    const c = tones(name), moving = o.to !== undefined, dir = moving ? Math.sign(o.to - x) || 1 : 0, t0 = o.t0 || 0, t1 = o.t1 === undefined ? t0 + 2 : o.t1;
    const rate = o.run ? 9 : 5.5, ph0 = o.phase || 0, edge = { stroke: INK, 'stroke-width': 9, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' };
    const e = G(g, { x, y, s });
    e.setAttribute('data-hero', '1'); e.setAttribute('data-rig', 'jelly');
    const body = mk('g', { 'data-body': 1 }, e), feet = [-1, 1].map(sd => { const f = mk('g', { 'data-leg': 1 }, body); mk('ellipse', { cx: sd * 34, cy: -18, rx: 40, ry: 22, fill: '#1f2937', ...edge, 'stroke-width': 7 }, f); return f; });
    mk('path', { d: 'M 0 -470 C 110 -470 150 -380 146 -300 C 140 -200 100 -34 0 -34 C -100 -34 -140 -200 -146 -300 C -150 -380 -110 -470 0 -470 Z', fill: c.body, ...edge }, body);
    const head = mk('g', { 'data-head': 1, transform: `translate(0 -520) scale(${MN.headW} ${MN.headH}) translate(0 520)` }, body);
    mk('ellipse', { cx: 0, cy: -520, rx: 108, ry: 98, fill: c.skin, ...edge }, head);
    [-1, 1].forEach(sd => { mk('circle', { cx: dir * 14 + sd * 38, cy: -530, r: 22, fill: '#fff', ...edge, 'stroke-width': 5 }, head); mk('circle', { cx: dir * 22 + sd * 38, cy: -530, r: 11, fill: o.eye || '#1c1917' }, head); });
    mk('path', { d: `M ${dir * 14 - 26} -488 Q ${dir * 14} ${o.grin ? -452 : -476} ${dir * 14 + 26} -488`, stroke: '#3b0d0d', 'stroke-width': 8, fill: 'none', 'stroke-linecap': 'round' }, head);
    if (c.glasses) [-1, 1].forEach(sd => mk('circle', { cx: dir * 14 + sd * 38, cy: -530, r: 34, fill: 'none', stroke: '#1e293b', 'stroke-width': 7 }, head));
    if (c.o.mustache) mk('path', { d: `M ${dir * 14 - 38} -492 Q ${dir * 14} -520 ${dir * 14 + 38} -492 Q ${dir * 14} -498 ${dir * 14 - 38} -492 Z`, fill: c.hair, ...edge, 'stroke-width': 4 }, head);
    if (c.cap) mk('path', { d: 'M -108 -550 C -112 -650 108 -650 108 -550 C 54 -570 -54 -570 -108 -550 Z', fill: c.cap, ...edge }, head);
    else if (!c.bald) mk('path', { d: 'M -108 -540 C -118 -660 118 -660 108 -540 C 74 -578 -74 -578 -108 -540 Z', fill: c.hair, ...edge }, head);
    if (moving) tw(e, { x: o.to }, t0, t1 - t0, lin);
    tick(t => {
      const on = moving && t >= t0 && t <= t1, ph = (t - t0) * rate + ph0, hop = on ? Math.abs(Math.sin(ph)) : 0;
      const sq = on ? .2 * Math.cos(2 * ph) : .06 * Math.sin(t * 6 + ph0);    // на земле сплющен, в воздухе вытянут
      body.setAttribute('transform', `translate(0 ${num(-hop * 90)}) translate(0 -20) scale(${num(1 - sq * .8)} ${num(1 + sq)}) translate(0 20)`);
      feet.forEach((f, i) => f.setAttribute('transform', `translate(0 ${num((i ? 1 : -1) * Math.sin(ph) * (on ? 14 : 0))})`));
    });
    return e;
  },
};

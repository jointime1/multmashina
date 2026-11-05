/* props.js — детали эпизода «JobTurbo»: письма-отказы, резюме, телефон, оффер, бутылка, труба, маска сварщика.
   Общие вещи (комнаты, штампы, иконки, искры, облако) живут в движке; здесь только то, что нужно этому эпизоду. */
'use strict';
const fiction = (g, t0 = 0, str = 'история и цифры вымышлены') => note(g, t0, str);   // пометка «вымышлено» в углу
const PNL = '#111a2e', EDG = '#1e293b';

// маленький штамп «ОТКАЗ» без звука (большой — stamp() из кита)
function rej(g, x, y, t0, r = -8, { size = 64 } = {}) {
  const w = inkW('ОТКАЗ', size) + 36, e = G(g, { x, y, r, s: 1.6, o: 0 });
  rect(e, -w / 2, -size * .85, w, size * 1.15, { fill: 'none', stroke: RED, 'stroke-width': size / 12, rx: 8 });
  T(e, 'ОТКАЗ', { y: size * .2, size, fill: RED, font: SANS, weight: 600, anchor: 'middle' });
  tw(e, { s: 1, o: .92 }, t0, .14, out);
  return e;
}

// стена писем-отказов, которая едет вверх всё время, пока идёт хук
const REFUSALS = ['К сожалению, мы выбрали другого кандидата', 'Спасибо за интерес. Мы вам перезвоним', 'Ваш опыт нам не подходит',
  'Вы слишком опытный… и дорогой', 'Вы недостаточно опытный', 'Позиция уже закрыта', 'Мы вас услышали', 'Желаем успехов в поиске'];
function mailWall(g, dur, { n = 16, seed = 11 } = {}) {
  const R = seeded(seed);
  for (let i = 0; i < n; i++) {
    const x = 60 + R() * 100, y0 = 120 + i * 230, c = G(g, { x, y: y0, o: .55 });
    rect(c, 0, 0, 680, 124, { fill: PNL, stroke: EDG, 'stroke-width': 3, rx: 16 });
    T(c, 'RE: ВАШ ОТКЛИК', { x: 28, y: 44, size: 26, fill: MUTED, font: SANS, weight: 500 });
    T(c, REFUSALS[i % REFUSALS.length], { x: 28, y: 95, size: 34, fill: LIGHT, font: SANS, weight: 600 });
    tw(c, { y: y0 - 1800 }, 0, dur, lin);
  }
}

// резюме: «было» (длинная простыня серых строк) и «стало» (шапка, галочки, короткие пункты)
function resumeDoc(g, cx, cy, w, h, good) {
  const e = G(g, { x: cx, y: cy }), x0 = -w / 2, y0 = -h / 2;
  rect(e, x0, y0, w, h, { fill: '#f8fafc', rx: 22 });
  if (good) {
    rect(e, x0, y0, w, 150, { fill: ACCENT, rx: 22 });
    rect(e, x0, y0 + 100, w, 50, { fill: ACCENT });
    rect(e, x0 + 36, y0 + 40, w * .5, 26, { fill: '#fff', rx: 13 });
    rect(e, x0 + 36, y0 + 84, w * .32, 18, { fill: 'rgba(255,255,255,.7)', rx: 9 });
    const step = Math.min(118, (h - 260) / 3.4);
    for (let i = 0; i < 4; i++) {
      const yy = y0 + 200 + i * step;
      mk('circle', { cx: x0 + 52, cy: yy + 12, r: 14, fill: GREEN }, e);
      rect(e, x0 + 90, yy, w * (.6 - i * .05), 22, { fill: '#334155', rx: 11 });
      rect(e, x0 + 90, yy + 36, w * (.44 - i * .04), 16, { fill: '#cbd5e1', rx: 8 });
    }
  } else {
    rect(e, x0 + 30, y0 + 34, w * .55, 28, { fill: '#475569', rx: 6 });
    const R = seeded(5);
    for (let i = 0; i < Math.floor((h - 100) / 36); i++) rect(e, x0 + 30, y0 + 90 + i * 36, (w - 60) * (.75 + R() * .25), 14, { fill: '#cbd5e1', rx: 7 });
  }
  return e;
}

// пуш: «ответ на отклик — слесарь», падает сверху
function notif(g, cx, cy, w, t0, o = {}) {
  const { icon = 'wrench', top = 'НОВЫЙ ОТВЕТ НА ОТКЛИК', title = 'Слесарь-сантехник', sub = '«Приходи в понедельник»' } = o;
  const e = G(g, { x: cx, y: cy - 500, o: 0 }), x0 = -w / 2;
  rect(e, x0, -130, w, 260, { fill: '#f8fafc', rx: 36 });
  mk('circle', { cx: x0 + 100, cy: 0, r: 64, fill: ACCENT }, e);
  ico(e, icon, x0 + 100, 0, 84, DARK);
  T(e, top, { x: x0 + 190, y: -38, size: 28, fill: '#64748b', font: SANS, weight: 500 });
  T(e, title, { x: x0 + 190, y: 22, size: 50, fill: DARK, font: SANS, weight: 600 });
  T(e, sub, { x: x0 + 190, y: 80, size: 34, fill: '#64748b', font: SANS, weight: 500 });
  tw(e, { y: cy, o: 1 }, t0, .4, out);
  sfx(BEAT_ID, t0, 'whoosh', .6);
  return e;
}

// бутылка водки: растёт «с отскоком»
function bottle(g, x, y, s, t0) {
  const e = G(g, { x, y, s: s * .6, o: 0 });
  rect(e, -26, -270, 52, 30, { fill: RED, rx: 6 });
  rect(e, -22, -242, 44, 100, { fill: '#cbd5e1', rx: 10 });
  rect(e, -58, -160, 116, 300, { fill: '#e2e8f0', rx: 30 });
  rect(e, -42, -140, 16, 260, { fill: 'rgba(255,255,255,.55)', rx: 8 });   // блик — под этикеткой, чтобы не резал буквы
  rect(e, -58, -50, 116, 120, { fill: '#fff' });
  T(e, 'ВОДКА', { x: 0, y: 24, size: 34, fill: RED, font: SANS, weight: 600, anchor: 'middle' });
  tw(e, { s, o: 1 }, t0, .3, back);
  sfx(BEAT_ID, t0, 'thud', .8);
  return e;
}

// труба, которая влетает справа и бьёт в рот; после удара улетает обратно
function pipeHit(g, cx, cy, t0) {
  const e = G(g, { x: 1150, y: cy - 250, r: 35, o: 0 });
  rect(e, -300, -38, 600, 76, { fill: STEEL, rx: 38 });
  rect(e, -300, -38, 600, 20, { fill: 'rgba(255,255,255,.35)', rx: 10 });
  rect(e, 100, -56, 70, 112, { fill: '#64748b', rx: 8 });
  tw(e, { x: cx + 260, y: cy, r: -8, o: 1 }, t0, .28, io);
  tw(e, { x: 1300, y: cy - 150, r: 30, o: 0 }, t0 + .45, .4, out);
  sfx(BEAT_ID, t0 + .1, 'whoosh', .7);
  sfx(BEAT_ID, t0 + .28, 'thud', 1.3);
  return e;
}

// резюме «как у CEO»: золотая рамка, печать, пункты, от которых хочется нанять немедленно
function ceoDoc(g, cx, cy, w, h, t0) {
  const e = G(g, { x: cx, y: cy, o: 0, s: .9 }), x0 = -w / 2, y0 = -h / 2;
  rect(e, x0, y0, w, h, { fill: '#fffbeb', stroke: '#d4a017', 'stroke-width': 10, rx: 14 });
  rect(e, x0 + 18, y0 + 18, w - 36, h - 36, { fill: 'none', stroke: '#d4a017', 'stroke-width': 3, rx: 8 });
  T(e, 'ПЁТР П.', { x: 0, y: y0 + 108, size: 76, fill: '#1f2937', font: SANS, weight: 600, anchor: 'middle' });
  T(e, 'C.E.O. · ВСЕЛЕННОЙ', { x: 0, y: y0 + 160, size: 34, fill: '#b45309', font: SANS, weight: 500, anchor: 'middle' });
  ['Выручка × 300%', '40 команд в подчинении', 'Спас прод в пятницу', 'Ментор для 100 джунов', 'Знает Kubernetes'].forEach((str, i) => {
    const yy = y0 + 250 + i * 80;
    mk('circle', { cx: x0 + 62, cy: yy - 12, r: 13, fill: '#d4a017' }, e);
    T(e, str, { x: x0 + 92, y: yy, size: 40, fill: '#374151', font: SANS, weight: 500 });
  });
  mk('circle', { cx: w / 2 - 80, cy: h / 2 - 80, r: 52, fill: '#d4a017', stroke: '#92400e', 'stroke-width': 6 }, e);
  T(e, 'TOP', { x: w / 2 - 80, y: h / 2 - 66, size: 44, fill: '#fffbeb', font: SANS, weight: 600, anchor: 'middle' });
  tw(e, { o: 1, s: 1 }, t0, .3, back);
  sfx(BEAT_ID, t0, 'thud', .8);
  return e;
}

// телефон с пустым списком звонков: «входящих: 0»
function phone(g, cx, cy, w, h, t0) {
  const e = G(g, { x: cx, y: cy, o: 0, s: .9 });
  rect(e, -w / 2, -h / 2, w, h, { fill: '#0b0d14', stroke: '#3a4150', 'stroke-width': 8, rx: 44 });
  rect(e, -w / 2 + 16, -h / 2 + 16, w - 32, h - 32, { fill: '#111827', rx: 30 });
  T(e, 'ВХОДЯЩИЕ', { x: 0, y: -h / 2 + 96, size: 46, fill: MUTED, font: SANS, weight: 500, anchor: 'middle' });
  T(e, '0', { x: 0, y: 70, size: 320, fill: RED, font: SANS, weight: 600, anchor: 'middle' });
  T(e, 'звонков', { x: 0, y: h / 2 - 80, size: 50, fill: LIGHT, font: SANS, weight: 500, anchor: 'middle' });
  tw(e, { o: 1, s: 1 }, t0, .3, back);
  sfx(BEAT_ID, t0, 'thud', .8);
  return e;
}

// сварочная маска отдельной картинкой (в облаке мыслей)
function helmetPic(g, x, y, size, t0) {
  const e = G(g, { x, y, s: size / 220 * .6, o: 0 });
  mk('path', { d: 'M -110 20 C -118 -110 -30 -140 8 -136 C 84 -132 120 -80 114 20 C 70 0 20 -10 -20 -6 C -60 -4 -90 6 -110 20 Z', fill: '#6b7280', stroke: INK, 'stroke-width': 6, 'stroke-linejoin': 'round' }, e);
  mk('rect', { x: -104, y: 10, width: 208, height: 96, rx: 20, fill: '#4b5563', stroke: INK, 'stroke-width': 6 }, e);
  mk('rect', { x: -82, y: 28, width: 164, height: 52, rx: 10, fill: '#0f2a1d', stroke: INK, 'stroke-width': 4 }, e);
  tw(e, { s: size / 220, o: 1 }, t0, .3, back);
  return e;
}

// резюме сварщика: стальная рамка, пункты, печать
function weldDoc(g, cx, cy, w, h, t0) {
  const e = G(g, { x: cx, y: cy, o: 0, s: .9 }), x0 = -w / 2, y0 = -h / 2;
  rect(e, x0, y0, w, h, { fill: '#f1f5f9', stroke: '#64748b', 'stroke-width': 10, rx: 14 });
  rect(e, x0, y0, w, 150, { fill: '#ea580c', rx: 14 });
  rect(e, x0, y0 + 100, w, 50, { fill: '#ea580c' });
  T(e, 'ПЁТР ПЕТРОВИЧ', { x: 0, y: y0 + 70, size: 52, fill: '#fff', font: SANS, weight: 600, anchor: 'middle' });
  T(e, 'СВАРЩИК · 6 РАЗРЯД', { x: 0, y: y0 + 120, size: 34, fill: '#ffedd5', font: SANS, weight: 500, anchor: 'middle' });
  ['Варю всё, что варится', 'И то, что не варится', 'Без созвонов', 'Перекур по ТК'].forEach((str, i) => {
    const yy = y0 + 230 + i * 80;
    mk('circle', { cx: x0 + 62, cy: yy - 12, r: 13, fill: '#ea580c' }, e);
    T(e, str, { x: x0 + 92, y: yy, size: 33, fill: '#374151', font: SANS, weight: 500 });
  });
  mk('circle', { cx: w / 2 - 80, cy: h / 2 - 80, r: 50, fill: 'none', stroke: RED, 'stroke-width': 7 }, e);
  T(e, 'ГОСТ', { x: w / 2 - 80, y: h / 2 - 66, size: 40, fill: RED, font: SANS, weight: 600, anchor: 'middle' });
  tw(e, { o: 1, s: 1 }, t0, .3, back);
  sfx(BEAT_ID, t0, 'thud', .8);
  return e;
}

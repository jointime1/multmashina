/* Сцены эпизода «Не тот сервер». Справочник по вызовам — docs/scenes.md.
   В светлом стиле DARK — это светлый фон, а LIGHT — тёмный текст (палитра названа по роли, а не по цвету).
   Раскладка кадра: герой масштаба 1,3–1,4 с центром головы на y≈1000 оставляет подбородок выше субтитров (y≈1200);
   всё над головой (до y≈560) свободно под слова, штампы и окна. */
'use strict';

const ТЕРМИНАЛ = '#e2e8f0';                           // текст в чёрном окне терминала не зависит от стиля

const BEATS = [
  ['hook', 'Хук', (m, D) => {
    const p = panel(), s = shot(p, 0, undefined, { bg: DARK });
    room(s, 'офис-вечер');
    hero(s, 'вася', CX, 1000, 1.4, [[0, 'neutral'], [m('a'), 'shock'], [m('b'), 'dead']], 0, D);
    word(s, 'БАЗА', CX, 400, m('a'), { size: 230, fill: LIGHT });
    strike(s, 170, 350, 730, 310, m('b'));
    stamp(s, 'НЕ ТУ', CX, 560, m('b'), { size: 110, colour: RED });
    finish(p); caps(p, 'hook');
  }, { pre: .3 }],

  ['friday', 'Пятница', (m, D) => {
    const p = panel(), s = shot(p, 0, undefined, { bg: DARK });
    room(s, 'офис-вечер'); note(s, 0, 'пятница');
    const t = term(s, 80, 330, 740, 250, 'test-стенд', .1);
    termLine(t, '$ psql -h stand-test', 40, 130, .3, ТЕРМИНАЛ);
    termLine(t, '$ чистим базу…', 40, 190, m('six'), ТЕРМИНАЛ);
    word(s, '18:00', CX, 280, m('six'), { size: 110, fill: LIGHT });
    hero(s, 'вася', CX, 1000, 1.3, [[0, 'tired'], [m('six'), 'dead'], [m('same'), 'smug']], 0, D);
    label(s, 'ОКНО ТО ЖЕ', CX, 650, m('same'), { size: 56, fill: MARK, colour: LIGHT });
    finish(p); caps(p, 'friday');
  }],

  ['oops', 'Не тот', (m, D) => {
    const p = panel(), s = shot(p, 0, undefined, { bg: DARK });
    room(s, 'офис-вечер');
    const t = term(s, 80, 250, 740, 300, '', .05);
    const test = T(t, 'test-стенд', { x: 670, y: 54, size: 28, fill: MUTED, font: MONO, weight: 400, anchor: 'end' });
    const prod = T(t, 'PROD', { x: 670, y: 54, size: 28, fill: RED, font: MONO, weight: 700, anchor: 'end', o: 0 });
    hide(test, m('prod'), .05); show(prod, m('prod'), .05);
    termLine(t, '$ drop database app;', 40, 140, m('cmd'), ТЕРМИНАЛ);
    termLine(t, 'готово', 40, 210, m('done'), GREEN);
    hero(s, 'вася', CX, 1000, 1.3, [[0, 'smug'], [m('luck'), 'grin'], [m('prod'), 'shock', { sweat: 1, eo: 1.4 }]], 0, D);
    stamp(s, 'ЭТО ПРОД', CX, 700, m('prod'), { size: 100, colour: RED });
    finish(p); caps(p, 'oops');
  }],

  ['monday', 'Понедельник', (m, D) => {
    const p = panel(), s = shot(p, 0, undefined, { bg: DARK });
    room(s, 'офис-вечер'); note(s, 0, 'понедельник');
    word(s, 'СОВЕЩАНИЕ', CX, 450, m('boss'), { size: 130, fill: LIGHT });
    label(s, 'БЭКАПЫ ЕСТЬ?', CX, 590, m('bk'), { size: 70, fill: MARK, colour: LIGHT });
    hero(s, 'начальник', 230, 1000, .95, [[0, 'stern'], [m('bk'), 'rage']], 0, D);
    hero(s, 'вася', 670, 1000, .95, [[0, 'worry'], [m('was'), 'dead']], 0, D);
    stamp(s, 'БЫЛИ', CX, 760, m('was'), { size: 110, colour: RED });
    finish(p); caps(p, 'monday');
  }],

  ['outro', 'Финал', (m, D) => {
    const p = panel(), s = shot(p, 0, undefined, { bg: DARK });
    room(s, 'офис-вечер');
    word(s, 'НАЗВАНИЕ СЕРВЕРА', CX, 330, m('rule'), { size: 100, fill: LIGHT });
    const cv = paper(s, CX, 540, 520, 260, 'РЕЗЮМЕ', -3);
    put(cv, { o: 0 }); show(cv, m('cv'), .2);
    hero(s, 'вася', CX, 1010, 1.25, [[0, 'neutral'], [m('rule'), 'thinking'], [m('cv'), 'grin', { wink: 1 }]], 0, D);
    stamp(s, 'ОПЫТ: КАТАСТРОФЫ', CX, 545, m('cv') + 1.2, { size: 64, colour: GREEN, r: -5 });
    finish(p); caps(p, 'outro');
  }],
];

start(BEATS);

/* scenes.js — сцены эпизода «{{название}}». Справочник по всем вызовам — docs/scenes.md.
   Бит = [id, название, (m, D) => { … }, {pre}]: m('метка') — время слова, D — длина реплики, всё внутри от нуля.
   Слова держите в зоне x 50–810, y 130–1290: платформы закрывают остальное кнопками. */
'use strict';

const BEATS = [
  // Хук: первый кадр уже в движении, говорящая картинка в первые две секунды
  ['hook', 'Хук', (m, D) => {
    const p = panel(), s = shot(p, 0, undefined, { bg: DARK });
    room(s, 'комната');
    word(s, 'мир', CX, 560, m('b'), { size: 200, fill: MARK, stroke: DARK });           // слово вылетает, когда звучит «мир»
    hero(s, 'главный', CX, 960, 1.3, [[0, 'neutral'], [m('a'), 'smug'], [m('b'), 'grin']], 0, D);
    finish(p); caps(p, 'hook');                                                           // зерно/виньетка, затем субтитры
  }],

  ['middle', 'Середина', (m, D) => {
    const p = panel(), s = shot(p, 0, undefined, { bg: DARK });
    room(s, 'комната');
    hero(s, 'главный', CX, 900, 1.3, [[0, 'dead'], [m('c'), 'shock']], 0, D);
    stamp(s, 'ВАУ', CX, 520, m('c'), { size: 120, colour: RED });
    finish(p); caps(p, 'middle');
  }],

  ['outro', 'Финал', (m, D) => {
    const p = panel(), s = shot(p, 0, undefined, { bg: DARK });
    room(s, 'комната');
    hero(s, 'главный', CX, 900, 1.3, [[0, 'grin', { wink: 1 }]], 0, D);
    label(s, 'подписывайтесь', CX, 560, m('d'), { size: 90, fill: MARK, colour: DARK });
    finish(p); caps(p, 'outro');
  }],
];

start(BEATS);

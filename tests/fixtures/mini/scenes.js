'use strict';
const BEATS = [['один', 'Тест', (m, D) => {
  const p = panel(0), s = shot(p, 0, undefined, { bg: DARK });
  room(s, 'комната');
  word(s, 'мир', CX, 600, m('w'), { size: 160, fill: LIGHT });
  hero(s, 'петя', CX, 1000, 1, [[0, 'neutral'], [m('w'), 'grin']], 0, D);
  finish(p); caps(p, 'один');
}]];
start(BEATS);

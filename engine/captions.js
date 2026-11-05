/* captions.js — субтитры по словам: по 1–3 слова за раз внизу кадра, строго под голос.
   Слова и времена приходят из озвучки (data.js → window.WORDS: бит → [[секунда, слово], …]). Внешний вид — в стиле, раздел «субтитры». */
'use strict';

const CAP = Object.assign({ y: 1228, size: 72, color: MARK, stroke: '#0b0d14', words: 3, chars: 22, gap: .45, max_width: 700 }, STYLE.captions);

function caps(p, id, pre = 0) {
  const ws = (window.WORDS || {})[id], dur = (window.TIMINGS[id] || {}).dur;
  if (!ws || !ws.length) return;
  const конец = CUR.end;                                              // затухание последнего субтитра не должно удлинять бит
  // слова собираются в короткие группы: до CAP.words слов и CAP.chars знаков, новая группа после паузы длиннее CAP.gap
  const chunks = [];
  let cur = null;
  ws.forEach(([t, w], i) => {
    const next = i + 1 < ws.length ? ws[i + 1][0] : dur;
    if (cur && (cur.n >= CAP.words || cur.text.length + 1 + w.length > CAP.chars || t - cur.end > CAP.gap)) { chunks.push(cur); cur = null; }
    if (!cur) cur = { t, text: '', n: 0, end: t };
    cur.text += (cur.n ? ' ' : '') + w; cur.n++; cur.end = Math.min(next, t + .8);
  });
  if (cur) chunks.push(cur);
  chunks.forEach((c, i) => {
    const nx = chunks[i + 1], t0 = pre + c.t, t1 = pre + (nx && nx.t - c.end < .3 ? nx.t : c.end + .12);
    const e = G(CUR.fixed || p, { x: CX, y: CAP.y, s: .88, o: 0 }), size = Math.min(CAP.size, CAP.size * CAP.max_width / inkW(c.text, CAP.size));
    const t = T(e, c.text, { x: 0, y: 0, size, fill: CAP.color, weight: 600, anchor: 'middle' });
    t.setAttribute('stroke', CAP.stroke); t.setAttribute('stroke-width', size / 6); t.setAttribute('paint-order', 'stroke'); t.setAttribute('stroke-linejoin', 'round');
    tw(e, { s: 1, o: 1 }, t0, .07, out);
    hide(e, t1, .05, lin);
  });
  CUR.end = конец;
}

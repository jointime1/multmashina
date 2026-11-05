/* scenes.js — сцены эпизода «JobTurbo: слесарь, нахуй» (мем-рилс про вымышленного айтишника Петю).
   Бит = реплика + картинка. m('метка') — время слова, к которому приурочено действие (метки стоят в narration.yaml),
   D — длина реплики. Всё внутри бита считается от нуля; пока бит не кончился, картинку можно менять сколько угодно раз. */
'use strict';

const OPEN_PRE = .3;      // первый бит: картинка идёт на 0,3 с раньше голоса, чтобы первый кадр уже был «в движении»
const RANK1 = { rank: 1, gap: 1 };   // Петрович: кепка, усы, комбинезон, дырка на месте двух зубов
// вывеска-неон над комнатой: room(g, 'комната', NEON('Текст', '#цвет'))
const NEON = (text, col, y = 300, size = 96) => ({ sign: text, signCol: col, glow: col, signY: y, signSize: size, lampX: 130 });

const BEATS = [
  // 0. Начало: Петра сократили из Шмяндекса (большой офис, HR с приказом, охрана, коллеги в слезах)
  ['fired', 'Сократили', (m, D) => {
    const p = panel(0), tS = m('sh'), s = shot(p, 0, undefined, { bg: DARK });
    office(s, { name: 'Шмяндекс' });
    [['коллега1', 120, 'sad'], ['коллега2', 300, 'shock'], ['коллега3', 600, 'cry'], ['коллега4', 780, 'sad']]
      .forEach(([кто, x, эмоция], i) => hero(s, кто, x, 660 + (i % 2) * 10, .5, [[0, эмоция]], 0, D, { seed: i * .9 }));
    hero(s, 'hr', 175, 900, .9, [[0, 'stern'], [tS, 'smug']], 0, D, { seed: .4 });
    hero(s, 'охранник', 725, 900, .9, [[0, 'stern', { rank: 1 }]], 0, D, { seed: 1.2 });
    hero(s, 'петя', CX, 880, 1.3, [[0, 'shock'], [tS - .1, 'cry']], 0, D, { box: true, seed: .2 });
    paper(s, 160, 1040, 210, 270, 'ПРИКАЗ', -8);
    stamp(s, 'СОКРАЩЁН', CX, 480, tS, { size: 100, colour: RED, r: -8 });
    fiction(s, .2);
    finish(p); caps(p, 'fired');
  }],

  // 1. Хук: стена писем-отказов уже едет, счётчик крутится, Петя плачет и орёт «блядь»
  ['hook', 'Хук', (m, D) => {
    const p = panel(0), s = shot(p, 0, undefined, { bg: DARK }), E = D + OPEN_PRE;
    bgGrid(s);
    mailWall(s, E);
    rect(s, 0, 170, W, 1010, { fill: DARK, opacity: .66 });
    counter(s, 347, CX, 400, 0, { size: 280, fill: RED, dur: 1.0 });
    hero(s, 'петя', CX, 910, 1.25, [[0, 'tired'], [.8, 'cry'], [m('bl') - .05, 'rage']], 0, E, { seed: .2 });
    rej(s, CX + 50, 790, 1.0, -12, { size: 56 });
    rej(s, 170, 300, .5, -10, { size: 54 }); rej(s, 735, 320, .8, 9, { size: 54 });
    stamp(s, 'БЛЯДЬ', CX, 560, m('bl'), { size: 120, colour: MARK, r: -6 });
    finish(p); caps(p, 'hook', OPEN_PRE);
  }, { pre: OPEN_PRE }],

  // 2. Петя в своей комнате: шесть лет опыта, резюме ахуенное, как у CEO, а не зовут
  ['resume', 'Резюме', (m, D) => {
    const p = panel(0), tS = m('six'), tC = m('ceo'), tK = m('call');
    const a = shot(p, 0, tS, { bg: DARK }); room(a, 'комната');
    hero(a, 'петя', CX, 700, 1.5, [[0, 'smug'], [tS - .5, 'grin']], 0, tS, { seed: .5 });
    const b = shot(p, tS, tC, { bg: DARK, whip: true }); room(b, 'комната');
    marker(b, 40, 700, 820, 160, tS + .1);
    counter(b, 6, CX, 610, tS, { size: 420, fill: MARK, dur: .6 });
    word(b, 'лет опыта', CX, 830, tS + .3, { size: 140, fill: DARK });
    hero(b, 'петя', CX, 1080, .8, [[tS, 'smug'], [tC - .5, 'grin']], tS, tC, { seed: 1 });
    const c = shot(p, tC, tK, { bg: DARK, whip: true }); room(c, 'комната');
    ceoDoc(c, 320, 640, 520, 700, tC);
    ico(c, 'crown', 520, 270, 170, MARK, tC + .3, { from: .2, dur: .35 });
    hero(c, 'петя', 700, 880, .8, [[tC, 'smug', { shades: 1 }]], tC, tK, { seed: 1.9, suit: '#0f172a', tie: '#ef4444', glasses: 0 });
    ico(c, 'sparkle', 640, 430, 110, MARK, tC + .5, { from: .2, dur: .4 });
    const d = shot(p, tK, undefined, { bg: DARK, whip: true }); room(d, 'комната');
    phone(d, CX, 500, 380, 640, tK);
    hero(d, 'петя', CX, 1030, .95, [[tK, 'dead'], [tK + 1.2, 'sad'], [tK + 2.4, 'cry']], tK, D, { seed: 1.7 });
    finish(p); caps(p, 'resume');
  }],

  // 3. JobTurbo: вывеска включается, сто самолётиков-откликов
  ['turbo', 'Джобтурбо', (m, D) => {
    const p = panel(0), tJ = m('jt'), tH = m('hun');
    const a = shot(p, 0, tH, { bg: DARK }); room(a, 'комната');
    const sg = neonSign(a, 'JobTurbo', CX, 300, 96, '#38bdf8');
    put(sg, { o: 0 }); tw(sg, { o: 1 }, tJ, .08, lin); tw(sg, { o: .25 }, tJ + .12, .06, lin); tw(sg, { o: 1 }, tJ + .24, .06, lin);
    sfx(BEAT_ID, tJ, 'bang', 1);
    hero(a, 'петя', CX, 880, 1.35, [[0, 'dead'], [tJ - .3, 'epiphany'], [tJ + .6, 'grin']], 0, tH, { seed: .1 });
    stamp(a, 'ВРУБИЛ', CX, 470, tJ + .1, { size: 90, colour: MARK, r: -6 });
    const c = shot(p, tH, undefined, { bg: DARK, whip: true }); room(c, 'комната');
    counter(c, 100, CX, 370, tH, { size: 230, fill: ACCENT, dur: .9 });
    icons(c, 'airplane-tilt', 100, 10, 130, 420, 64, ACCENT, tH, .9);
    label(c, 'вакансий за запуск', CX, 1130, tH + .5, { size: 56, fill: MARK, colour: DARK });
    hero(c, 'петя', 790, 300, .45, [[tH, 'epiphany'], [tH + 1.2, 'grin']], tH, D, { seed: 3.1 });
    finish(p); caps(p, 'turbo');
  }],

  // 4. Через неделю оффер, скучный айтишный; Петя задумался: а если всё поменять нахуй
  ['offer', 'Оффер', (m, D) => {
    const p = panel(0), tO = m('off'), tT = m('th');
    const a = shot(p, 0, tT, { bg: DARK }); room(a, 'комната');
    notif(a, CX, 400, 780, tO, { icon: 'briefcase', top: 'НОВОЕ ПИСЬМО', title: 'ОФФЕР: Senior Developer', sub: '«Добро пожаловать в команду»' });
    hero(a, 'петя', CX, 830, 1.15, [[0, 'grin'], [tT - .3, 'dead']], 0, tT, { seed: .3 });
    stamp(a, 'ОФФЕР', 690, 640, tO + .3, { size: 90, colour: GREEN, r: -8 });
    const b = shot(p, tT, undefined, { bg: DARK, whip: true }); room(b, 'комната');
    hero(b, 'петя', CX, 800, 1.3, [[tT, 'thinking']], tT, D, { seed: 1.4 });
    cloud(b, 650, 300, 380, 230, tT + .1);
    helmetPic(b, 650, 300, 150, tT + .4);
    word(b, '?', 800, 560, tT + .5, { size: 200, fill: MARK, stroke: DARK });
    finish(p); caps(p, 'offer');
  }],

  // 5. Джобтурбо переписал резюме: было разработчик, стало сварщик
  ['swap', 'Резюме', (m, D) => {
    const p = panel(0), tW = m('was'), tN = m('now');
    const a = shot(p, 0, tW, { bg: DARK }); room(a, 'комната');
    neonSign(a, 'JobTurbo', CX, 300, 96, '#38bdf8');
    hero(a, 'петя', CX, 880, 1.2, [[0, 'thinking'], [tW - .3, 'epiphany']], 0, tW, { seed: .7 });
    ico(a, 'sparkle', 170, 560, 140, MARK, .2, { from: .2, dur: .4 }); ico(a, 'sparkle', 730, 520, 110, ACCENT, .4, { from: .2, dur: .4 });
    const b = shot(p, tW, tN, { bg: DARK, whip: true }); room(b, 'комната');
    resumeDoc(b, 270, 700, 440, 600, false);
    label(b, 'было', 190, 350, tW, { size: 56, fill: RED, colour: '#fff' });
    strike(b, 80, 440, 460, 960, tW + .3, { w: 30 }); strike(b, 460, 440, 80, 960, tW + .45, { w: 30 });
    hero(b, 'петя', 735, 880, .75, [[tW, 'sad']], tW, tN, { seed: 1.5 });
    const c = shot(p, tN, undefined, { bg: DARK, whip: true }); room(c, 'комната');
    weldDoc(c, 270, 700, 440, 600, tN);
    label(c, 'стало', 190, 350, tN + .2, { size: 56, fill: GREEN, colour: DARK });
    hero(c, 'петя', 735, 880, .75, [[tN, 'grin', { helm: 1 }]], tN, D, { seed: 2.4 });
    sparks(c, 730, 800, tN, D);
    finish(p); caps(p, 'swap');
  }],

  // 6. Сто откликов, девяносто девять приглашений; не позвонил один — Шмяндекс
  ['nn', 'Девяносто девять', (m, D) => {
    const p = panel(0), tH = m('hun2'), tNi = m('nine'), tO = m('one');
    const grid = (g, t0, col) => { for (let i = 0; i < 100; i++) ico(g, 'airplane-tilt', 162 + (i % 10) * 64, 452 + Math.floor(i / 10) * 64, 55, i === 99 && col !== ACCENT ? RED : col, t0 + .7 * i / 100, { from: .3, dur: .14 }); };
    const a = shot(p, 0, tNi, { bg: DARK }); room(a, 'комната');
    counter(a, 100, CX, 370, tH, { size: 230, fill: ACCENT, dur: .8 });
    grid(a, tH, ACCENT);
    hero(a, 'петя', 790, 300, .45, [[0, 'epiphany']], 0, tNi, { seed: 3.1 });
    const b = shot(p, tNi, tO, { bg: DARK, whip: true }); room(b, 'комната');
    counter(b, 99, CX, 370, tNi, { size: 230, fill: GREEN, dur: .6 });
    grid(b, tNi, GREEN);
    label(b, 'приглашений', CX, 1130, tNi + .3, { size: 56, fill: GREEN, colour: DARK });
    hero(b, 'петя', 790, 300, .45, [[tNi, 'grin', { rank: 1, gap: 1, helm: 1 }]], tNi, tO, { seed: 3.7 });
    const c = shot(p, tO, undefined, { bg: DARK, whip: true }); room(c, 'комната');
    neonSign(c, 'Шмяндекс', CX, 330, 100, '#e879f9');
    ico(c, 'airplane-tilt', CX, 700, 300, RED, tO + .1, { from: .3, dur: .3 });
    strike(c, 300, 540, 600, 860, tO + .4, { w: 36, colour: LIGHT });
    stamp(c, 'НЕ ПОЗВОНИЛ', CX, 1000, tO + .5, { size: 100, colour: RED, r: -5 });
    hero(c, 'петя', 780, 640, .5, [[tO, 'smug', { ...RANK1, shades: 1 }]], tO, D, { seed: 4.2 });
    fiction(c, .2);
    finish(p); caps(p, 'nn');
  }],

  // 7. Год спустя Петя стал Петровичем: бригада, тачка, ноль созвонов
  ['life', 'Год спустя', (m, D) => {
    const p = panel(0), tP = m('pet'), tC = m('crew'), tK = m('car'), tS = m('sync');
    const a = shot(p, 0, tC, { bg: DARK }); room(a, 'подвал');
    label(a, 'год спустя', CX, 255, 0, { size: 84, fill: LIGHT, colour: DARK });
    hero(a, 'петя', CX, 720, 1.4, [[0, 'dead'], [tP - .5, 'shock'], [tP, 'grin', RANK1]], 0, tC, { seed: .8 });
    label(a, 'Петя', CX, 960, .15, { size: 90, fill: ACCENT, colour: DARK });
    strike(a, 300, 928, 600, 928, tP - .15, { w: 16 });
    word(a, 'Петрович', CX, 1140, tP, { size: 160, fill: MARK, stroke: DARK });
    sfx(BEAT_ID, tP, 'bang', 1.2);
    const b = shot(p, tC, tK, { bg: DARK, whip: true }); room(b, 'подвал');
    neonSign(b, 'Бригада Петровича', CX, 270, 52, '#ffb347');
    hero(b, 'петя', CX, 600, 1.0, [[tC, 'grin', RANK1]], tC, tK, { in: tC, seed: .1 });
    hero(b, 'петя', 160, 740, .7, [[tC, 'smug', { rank: 1 }]], tC, tK, { in: tC + .1, seed: .9, skin: '#e8b48a', hair: '#6b7280' });
    hero(b, 'петя', 740, 740, .7, [[tC, 'drunk', { rank: 1 }]], tC, tK, { in: tC + .2, seed: 1.6, skin: '#f5d0b0', hair: '#7c2d12' });
    const c = shot(p, tK, tS, { bg: DARK, whip: true }); room(c, 'подвал');
    hero(c, 'петя', CX, 470, 1.0, [[tK, 'smug', { ...RANK1, shades: 1 }]], tK, tS, { seed: 2.1 });
    for (let i = 0; i < 5; i++) {
      const ln = G(c, { x: -500, y: 840 + i * 50, o: .7 });
      rect(ln, 0, 0, 360, 10, { fill: '#475569', rx: 5 });
      tw(ln, { x: 1000 }, tK, 1.1, lin);
    }
    const car = ico(c, 'car-profile', -300, 930, 340, MARK);
    tw(car, { x: 1200 }, tK, 1.2, lin);
    sfx(BEAT_ID, tK + .1, 'whoosh', .8);
    const d = shot(p, tS, undefined, { bg: DARK, whip: true }); room(d, 'подвал');
    word(d, '09:00', CX, 560, tS, { size: 260, fill: LIGHT, stroke: DARK });
    strike(d, 120, 330, 780, 590, tS + .35, { w: 36 }); strike(d, 780, 330, 120, 590, tS + .55, { w: 36 });
    sfx(BEAT_ID, tS + .6, 'thud', 1);
    word(d, 'ноль созвонов', CX, 760, tS + .7, { size: 130, fill: MARK, stroke: DARK });
    hero(d, 'петя', CX, 960, .95, [[tS, 'grin', { ...RANK1, shades: 1 }]], tS, D, { seed: 2.9 });
    finish(p); caps(p, 'life');
  }],

  // 8. Вместо Джиры сварочный аппарат, вместо смузи водка, два зуба выбила труба, дедлайнов нет, красота
  ['life2', 'Красота', (m, D) => {
    const p = panel(0), tV = m('vod'), tT = m('teeth'), tD = m('dl'), tK = m('kr'), tHit = tT + .53;
    const a = shot(p, 0, tV, { bg: DARK }); room(a, 'подвал');
    word(a, 'JIRA', CX, 330, 0, { size: 210, fill: LIGHT, stroke: DARK });
    strike(a, 120, 262, 780, 262, .45, { w: 32 });
    ico(a, 'arrow-down', CX, 440, 100, MARK, .75);
    hero(a, 'петя', CX, 760, 1.0, [[0, 'smug', { ...RANK1, helm: 1, mask: 1 }]], 0, tV, { seed: .4 });
    sparks(a, CX + 20, 850, .3, tV);
    const w = ico(a, 'lightning', 710, 930, 260, MARK, .95, { from: .3, dur: .35 }); bob(w, 930, 12, 1.1, 1.3, tV - 1.3);
    const b = shot(p, tV, tT, { bg: DARK, whip: true }); room(b, 'подвал');
    word(b, 'смузи', CX, 390, tV, { size: 190, fill: LIGHT, stroke: DARK });
    strike(b, 130, 320, 770, 320, tV + .3, { w: 32 });
    ico(b, 'arrow-down', CX, 500, 90, MARK, tV + .5);
    hero(b, 'петя', 260, 840, .95, [[tV, 'grin', RANK1], [tV + 1, 'drunk', RANK1]], tV, tT, { seed: 1.3 });
    bottle(b, 690, 900, 1.3, tV + .65);
    const c = shot(p, tT, tD, { bg: DARK, whip: true }); room(c, 'подвал');
    hero(c, 'петя', CX, 760, 1.5, [[tT, 'grin', { rank: 1 }], [tHit, 'grin', { rank: 1 }], [tHit + .2, 'shock', { ...RANK1, r: -8, shk: 3 }], [tHit + .8, 'grin', RANK1]], tT, tD, { seed: 2.4 });
    pipeHit(c, 470, 885, tT + .25);
    flyTooth(c, CX - 25, 880, tHit, -230, 330, -540); flyTooth(c, CX + 25, 880, tHit, 260, 380, 600);
    word(c, 'бам!', CX, 330, tHit, { size: 220, fill: MARK, stroke: DARK });
    label(c, 'минус два зуба', CX, 1130, tHit + .4, { size: 56, fill: RED, colour: '#fff' });
    const d = shot(p, tD, tK, { bg: DARK, whip: true }); room(d, 'подвал');
    word(d, 'нет', CX, 560, tD, { size: 360, fill: RED, stroke: DARK });
    word(d, 'дедлайнов', CX, 730, tD + .2, { size: 160, fill: LIGHT, stroke: DARK });
    hero(d, 'петя', CX, 1050, .95, [[tD, 'grin', { ...RANK1, shades: 1 }]], tD, tK, { seed: 3.3 });
    const e = shot(p, tK, undefined, { bg: DARK, whip: true }); room(e, 'подвал');
    hero(e, 'петя', CX, 640, 1.3, [[tK, 'drunk', RANK1], [tK + .9, 'grin', { ...RANK1, wink: 1 }]], tK, D, { seed: 4.1 });
    ico(e, 'sparkle', 140, 400, 120, MARK, tK + .3); ico(e, 'sparkle', 770, 540, 90, ACCENT, tK + .45); ico(e, 'sparkle', 150, 900, 80, ACCENT, tK + .55);
    bottle(e, 735, 930, .6, tK + .35);
    finish(p); caps(p, 'life2');
  }],

  // 9. Финал: рифма с хуком, шов вместо ключа, «был Петей — стал Петровичем», JobTurbo и ссылка
  ['outro', 'Финал', (m, D) => {
    const p = panel(0), tK = m('k'), tP = m('pv'), tJ = m('jt');
    const a = shot(p, 0, tK, { bg: DARK }); room(a, 'комната');
    word(a, '347', CX, 560, 0, { size: 400, fill: RED, stroke: DARK });
    strike(a, 110, 380, 790, 540, .6, { w: 40, colour: LIGHT });
    word(a, 'отказов', CX, 700, .2, { size: 140, fill: LIGHT, stroke: DARK });
    hero(a, 'петя', CX, 1020, .85, [[0, 'cry'], [tK - .5, 'sad']], 0, tK, { seed: .6 });
    fiction(a, .2);
    const b = shot(p, tK, tP, { bg: DARK, whip: true }); room(b, 'подвал');
    hero(b, 'петя', CX, 560, 1.2, [[tK, 'smug', { ...RANK1, helm: 1 }]], tK, tP, { seed: 1.4 });
    let sd = 'M 120 900';
    for (let i = 0; i < 14; i++) sd += ' a 24 24 0 0 1 48 0';
    draw(path(b, sd, { fill: 'none', stroke: '#cbd5e1', 'stroke-width': 12, 'stroke-linecap': 'round' }, { d: 0 }), tK, Math.max(.4, tP - tK - .2), lin);
    sparks(b, CX, 880, tK, tP, { seed: 8 });
    const c = shot(p, tP, tJ, { bg: DARK, whip: true }); room(c, 'подвал');
    hero(c, 'петя', CX, 690, 1.4, [[tP, 'dead'], [tP + .3, 'shock'], [tP + .5, 'grin', RANK1]], tP, tJ, { seed: 2.2 });
    label(c, 'Петя', CX, 960, tP, { size: 90, fill: ACCENT, colour: DARK });
    strike(c, 300, 928, 600, 928, tP + .3, { w: 16 });
    word(c, 'Петрович', CX, 1150, tP + .5, { size: 160, fill: MARK, stroke: DARK });
    sfx(BEAT_ID, tP + .5, 'bang', 1.2);
    const d = shot(p, tJ, undefined, { bg: DARK, whip: true }); room(d, 'комната', NEON('JobTurbo', '#38bdf8', 330, 110));
    label(d, 'jobturbo.ru', CX, 640, tJ + .3, { size: 100, fill: MARK, colour: DARK });
    word(d, 'ссылка в шапке', CX, 800, tJ + .55, { size: 90, fill: LIGHT, stroke: DARK });
    hero(d, 'петя', CX, 1010, .7, [[tJ + .3, 'grin', { ...RANK1, wink: 1 }]], tJ, D, { seed: 3.8 });
    const f = T(d, 'ИСТОРИЯ И ЦИФРЫ ВЫМЫШЛЕНЫ · СОВПАДЕНИЯ СЛУЧАЙНЫ', { x: CX, y: 1282, size: 24, fill: LIGHT, font: SANS, weight: 500, anchor: 'middle', o: 0 });
    f.setAttribute('letter-spacing', '.06em'); show(f, tJ + .8, .3, lin);
    finish(p); caps(p, 'outro');
  }],
];

start(BEATS);

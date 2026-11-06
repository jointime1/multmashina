/* player.js — страница-плеер: собирает сцену, рисует кадр на любое время, играет голос и эффекты.

   Адрес страницы понимает параметры:
     ?clean        без интерфейса (так страницу снимает рендер);
     ?t=12.5       открыть на 12,5-й секунде эпизода;
     ?beat=3&t=1.2 открыть на 1,2-й секунде третьего бита (биты считаются с нуля);
     ?auto         сразу играть (браузеры часто требуют сперва клик по странице).
   Для рендера наружу выставлено window.MM: manifest() — раскладка эпизода, seek(t) — нарисовать кадр, ready — страница готова. */
'use strict';

const MM = window.MM = { manifest, ready: false, t: 0 };
const QUERY = new URLSearchParams(location.search);
const CLEAN = QUERY.has('clean');
let TOTAL = 0, svgEl = null;

MM.seek = t => { MM.t = Math.max(0, Math.min(t, TOTAL)); renderAt(MM.t); updateUi(); };

function fit() {
  const k = Math.min(innerWidth / W, innerHeight / H);
  Object.assign(svgEl.style, { width: W * k + 'px', height: H * k + 'px', left: (innerWidth - W * k) / 2 + 'px', top: (innerHeight - H * k) / 2 + 'px' });
}

// ---------- интерфейс предпросмотра ----------
let ui = null;
function buildUi() {
  ui = document.createElement('div');
  ui.style.cssText = 'position:fixed;left:0;right:0;bottom:0;display:flex;gap:12px;align-items:center;padding:10px 16px;background:rgba(0,0,0,.65);color:#fff;font:14px system-ui,sans-serif;z-index:9';
  ui.innerHTML = '<button id="mm-play" style="font-size:18px;width:40px">▶</button><input id="mm-bar" type="range" min="0" max="1000" value="0" style="flex:1"><span id="mm-time" style="min-width:110px;text-align:right"></span>';
  document.body.appendChild(ui);
  ui.querySelector('#mm-play').onclick = () => (playing ? pause() : play());
  ui.querySelector('#mm-bar').oninput = e => { const was = playing; if (was) pause(); MM.seek(e.target.value / 1000 * TOTAL); if (was) play(); };
  addEventListener('keydown', e => { if (e.code === 'Space') { e.preventDefault(); playing ? pause() : play(); } });
}
const mmss = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
function updateUi() {
  if (!ui) return;
  ui.querySelector('#mm-bar').value = TOTAL ? MM.t / TOTAL * 1000 : 0;
  ui.querySelector('#mm-time').textContent = `${mmss(MM.t)} / ${mmss(TOTAL)}`;
  ui.querySelector('#mm-play').textContent = playing ? '⏸' : '▶';
}

// ---------- звук предпросмотра (в видео звук собирает рендер сам) ----------
let actx = null, playing = false, sources = [], ctxStart = 0, tStart = 0;
const buffers = {};
async function loadBuffers() {
  actx = actx || new AudioContext();
  const man = manifest(), need = new Set(man.beats.map(b => `audio/${b.id}.mp3`));
  man.sfx.forEach(s => need.add(`sfx/${s.name}.mp3`));
  for (const url of need) {
    if (buffers[url] !== undefined) continue;
    try { buffers[url] = await actx.decodeAudioData(await (await fetch(url)).arrayBuffer()); }
    catch (e) { buffers[url] = null; console.warn(`Нет звука: ${url}`); }
  }
}
function place(buf, from, at, gain) {
  const end = at + buf.duration;
  if (end <= from) return;
  const src = actx.createBufferSource(), g = actx.createGain();
  g.gain.value = gain; src.buffer = buf; src.connect(g).connect(actx.destination);
  src.start(actx.currentTime + Math.max(0, at - from), Math.max(0, from - at));
  sources.push(src);
}
async function play() {
  if (playing) return;
  await loadBuffers();
  if (MM.t >= TOTAL - .05) MM.t = 0;
  const man = manifest(), from = MM.t;
  man.beats.forEach(b => buffers[`audio/${b.id}.mp3`] && place(buffers[`audio/${b.id}.mp3`], from, b.voice_at, 1));
  man.sfx.forEach(s => buffers[`sfx/${s.name}.mp3`] && place(buffers[`sfx/${s.name}.mp3`], from, s.t, .5 * s.vol));
  playing = true; ctxStart = actx.currentTime; tStart = from;
  const tick = () => {
    if (!playing) return;
    MM.seek(tStart + actx.currentTime - ctxStart);
    if (MM.t >= TOTAL) return pause();
    requestAnimationFrame(tick);
  };
  tick();
}
function pause() {
  playing = false;
  sources.forEach(s => { try { s.stop(); } catch (e) { /* уже остановлен */ } });
  sources = [];
  updateUi();
}

// ---------- запуск ----------
// start(биты): собрать эпизод и показать первый кадр
async function start(defs) {
  document.documentElement.style.background = '#000';
  document.body.style.cssText = 'margin:0;overflow:hidden;background:#000';
  svgEl = mk('svg', { id: 'mm-svg', viewBox: `0 0 ${W} ${H}` }, document.body);
  svgEl.style.position = 'absolute';
  mk('rect', { x: 0, y: 0, width: W, height: H, fill: DARK }, svgEl);
  addEventListener('resize', fit); fit();
  // шрифты должны загрузиться до замеров ширины текста
  await Promise.all((FONTS.preload || ['700 40px Oswald']).map(f => document.fonts.load(f, 'АБВабвGgЯя0123')));
  await document.fonts.ready;
  mannerDefs(svgEl);
  TOTAL = buildBeats(defs);
  if (!CLEAN) buildUi();
  let t = QUERY.has('t') ? parseFloat(QUERY.get('t')) : 0;
  if (QUERY.has('beat')) t += BEAT_LIST[parseInt(QUERY.get('beat'), 10)].start;
  MM.seek(t);
  MM.ready = true;
  if (QUERY.has('auto')) play();
}

"""Выбор стиля: какие стили есть, чем они отличаются и как выглядят.

`стили` печатает таблицу: имя, название, школа (персонаж и характер движения) и описание из комментария в начале файла стиля.
`превью` снимает витрину: по полосе кадров на каждый стиль (крупно, средний, общий, двое) и общий лист всех стилей, чтобы выбрать стиль глазами.
Стили лежат в styles/*.yaml; новый файл с комментарием в начале сам попадает в таблицу и витрину."""
import json
import shutil
import subprocess
import textwrap
from pathlib import Path

from . import build, config, serve

ПЕРСОНАЖ_ИМЕНА = {v: k for k, v in config.ПЕРСОНАЖИ.items()}
ХАРАКТЕР_ИМЕНА = {v: k for k, v in config.ХАРАКТЕРЫ.items()}


def список():
    """Готовые стили: [{имя, название, описание, персонаж, характер}], по алфавиту."""
    res = []
    for f in sorted((config.ROOT / 'styles').glob('*.yaml')):
        ст = config.стиль(f.stem)
        шапка = []
        for строка in f.read_text(encoding='utf-8').splitlines():
            if not строка.startswith('#'):
                break
            шапка.append(строка.lstrip('#').strip())
        rig, feel = ст.get('manner', {}).get('rig', 'bust'), ст.get('motion', {}).get('feel', 'smooth')
        res.append({'имя': f.stem, 'название': ст['name'], 'описание': ' '.join(x for x in шапка if x),
                    'персонаж': ПЕРСОНАЖ_ИМЕНА.get(rig, rig), 'характер': ХАРАКТЕР_ИМЕНА.get(feel, feel)})
    return res


def показать():
    print('Готовые стили (выбирайте по настроению истории; как они выглядят — docs/previews/styles.jpg, команда: mm.py стили --превью):\n')
    for с in список():
        print(f'  {с["имя"]:<14}{с["название"]:<18}{с["персонаж"]} / {с["характер"]}')
        for строка in textwrap.wrap(с['описание'], 104):
            print(f'      {строка}')
        print()
    print('Выбрать: mm.py новый reels/<имя> --стиль <имя>; сменить у готового эпизода: строка «стиль:» в episode.yaml или ключ --стиль у команд.')


# ---------- витрина ----------
СЦЕНЫ = """'use strict';
const BEATS = [
  ['a', 'Крупно', (m, D) => { const p = panel(), s = shot(p, 0, undefined, { bg: DARK }); room(s, 'комната');
    const k = closeUp(s, 'петя', [[0, 'neutral'], [.5, 'shock'], [1.2, 'grin']], 0, D);
    word(s, %s, ...k.text, .3, { size: k.size * .8, fill: MARK, stroke: DARK }); finish(p); caps(p, 'a'); }],
  ['b', 'Средний', (m, D) => { const p = panel(), s = shot(p, 0, undefined, { bg: DARK }); room(s, 'подвал');
    medium(s, 'вася', [[0, 'thinking'], [.6, 'cry'], [1.3, 'rage']], 0, D, { side: 'left' }); finish(p); caps(p, 'b'); }],
  ['c', 'Общий', (m, D) => { const p = panel(), s = shot(p, 0, undefined, { bg: DARK }); room(s, 'подвал');
    wide(s, 'вася', { x: 120, to: 760, t0: .1, t1: 1.9 });
    figure(s, 'зомби', -60, 1160, .44, { to: 540, t0: .1, t1: 1.9, phase: 1 }); figure(s, 'зомби', -170, 1120, .4, { to: 420, t0: .1, t1: 1.9, phase: 2.2 });
    finish(p); caps(p, 'c'); }],
  ['d', 'Двое', (m, D) => { const p = panel(), s = shot(p, 0, undefined, { bg: DARK }); office(s, { name: 'ВИТРИНА' });
    faceOff(s, 'петя', [[0, 'neutral'], [.8, 'grin']], 'вася', [[0, 'stern'], [.8, 'rage']], 0, D); finish(p); caps(p, 'd'); }],
];
start(BEATS);
"""
ЭПИЗОД = """название: Витрина
стиль: %s
скрипты: [scenes.js]
герои:
  петя: {очки: true}
  вася: {волосы: "#7c2d12", очки: false, толстовка: "#14532d", усы: 1}
  зомби: {кожа: "#9bb88a", волосы: "#3f3f46", очки: false, толстовка: "#52525b"}
"""
БИТЫ = ('a', 'b', 'c', 'd')
МОМЕНТЫ = {'a': 1.5, 'b': 1.4, 'c': 1.5, 'd': 1.5}


def _эпизод(папка, имя, название):
    папка.mkdir(parents=True, exist_ok=True)
    (папка / 'scenes.js').write_text(СЦЕНЫ % json.dumps(название.upper(), ensure_ascii=False), encoding='utf-8')
    (папка / 'episode.yaml').write_text(ЭПИЗОД % имя, encoding='utf-8')
    (папка / 'narration.yaml').write_text('биты:\n' + ''.join(f'  {б}: "[[a]]Слово один."\n' for б in БИТЫ), encoding='utf-8')
    (папка / 'audio').mkdir(exist_ok=True)
    тайминги = {}
    for б in БИТЫ:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', '2', '-codec:a', 'libmp3lame', str(папка / 'audio' / f'{б}.mp3')], check=True)
        тайминги[б] = {'dur': 2, 'marks': {'a': .1}, 'words': [[.1, 'слово'], [.7, 'слово'], [1.3, 'слово']]}
    (папка / 'audio' / 'timings.json').write_text(json.dumps(тайминги, ensure_ascii=False), encoding='utf-8')


def _кадры(сборка, куда):
    from playwright.sync_api import sync_playwright
    куда.mkdir(parents=True, exist_ok=True)
    srv, порт = serve.запустить(сборка)
    try:
        with sync_playwright() as p:
            br = p.chromium.launch()
            page = br.new_context(viewport={'width': 450, 'height': 800}, device_scale_factor=1).new_page()
            ошибки = []
            page.on('pageerror', lambda e: ошибки.append(str(e)))
            page.goto(f'http://127.0.0.1:{порт}/index.html?clean')
            try:
                page.wait_for_function('window.MM && window.MM.ready', timeout=60000)
            except Exception:
                raise RuntimeError('Страница витрины не загрузилась: ' + '; '.join(ошибки or ['(без ошибок)']))
            старт = {b['id']: b['start'] for b in page.evaluate('MM.manifest()')['beats']}
            файлы = []
            for б in БИТЫ:
                page.evaluate('t => MM.seek(t)', старт[б] + МОМЕНТЫ[б])
                f = куда / f'{б}.png'
                page.screenshot(path=str(f))
                файлы.append(f)
            br.close()
            return файлы
    finally:
        srv.shutdown()


def превью(куда, только=None):
    """Снять витрину в папку `куда`: <стиль>.jpg для каждого стиля и styles.jpg со всеми сразу. Возвращает пути полос стилей."""
    куда = Path(куда)
    куда.mkdir(parents=True, exist_ok=True)
    рабочая = config.ROOT / 'build' / 'витрина'
    if рабочая.exists():
        shutil.rmtree(рабочая)
    полосы = []
    for с in список():
        if только and с['имя'] not in только:
            continue
        эп = рабочая / с['имя'] / 'эпизод'
        _эпизод(эп, с['имя'], с['название'])
        сборка = build.собрать(эп, выход=рабочая / с['имя'] / 'сборка')
        кадры = _кадры(сборка, рабочая / с['имя'] / 'кадры')
        полоса = куда / f'{с["имя"]}.jpg'
        вход = [x for f in кадры for x in ('-i', str(f))]
        subprocess.run(['ffmpeg', '-v', 'error', '-y', *вход, '-filter_complex', '[0][1][2][3]hstack=inputs=4,scale=1080:-2', '-frames:v', '1', '-q:v', '5', str(полоса)], check=True)
        полосы.append(полоса)
    if полосы:
        вход = [x for f in полосы for x in ('-i', str(f))]
        subprocess.run(['ffmpeg', '-v', 'error', '-y', *вход, '-filter_complex', ''.join(f'[{i}]' for i in range(len(полосы))) + f'vstack=inputs={len(полосы)}', '-frames:v', '1', '-q:v', '6', str(куда / 'styles.jpg')], check=True) if len(полосы) > 1 else shutil.copy(полосы[0], куда / 'styles.jpg')
    return полосы

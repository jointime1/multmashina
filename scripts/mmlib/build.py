"""Сборка эпизода: папка examples/<имя> (+ движок, шрифты, стиль, озвучка) → автономная статическая папка build/<имя>.

В собранной папке всё лежит рядом (index.html, engine/, fonts/, audio/, sfx/): её можно открыть через любой статический сервер
и снять в видео. Сборка ничего не придумывает сама: нет озвучки или метки не совпали — она говорит об этом по-русски и останавливается.
"""
import json
import re
import shutil
from pathlib import Path

from . import config, gitignore

ДВИЖОК = ['core.js', 'icons.js', 'kit.js', 'captions.js', 'scenery.js', 'manner.js', 'characters.js', 'plans.js', 'player.js']   # порядок подключения
МЕТКА = re.compile(r'\[\[(\w+)\]\]')


def _слово(w):
    return re.sub(r'[^\w]', '', w.lower().replace('ё', 'е'))


def реплики(текст, слова, замены):
    """Строки субтитров: по одной на предложение, со временем его первого слова (слова считаются так же, как в озвучке)."""
    чистый = МЕТКА.sub('', текст).strip()
    res, i = [], 0
    for предл in re.split(r'(?<=[.!?…])\s+', чистый):
        n = len(re.findall(r"[\w'’-]+", предл))
        if n and i < len(слова):
            for k, v in замены.items():
                предл = re.sub(rf'(?i)\b{re.escape(k)}\b', v, предл)
            res.append([round(слова[i][0], 3), предл.strip()])
            i += n
    return res


def проверить_озвучку(биты, тайминги):
    """Каждый бит из сценария должен иметь озвучку, а каждая метка из текста — время."""
    for id_, текст in биты.items():
        if id_ not in тайминги:
            raise config.ОшибкаКонфига(f'Для бита «{id_}» нет озвучки в audio/timings.json. Запустите: python scripts/mm.py озвучить <эпизод>')
        нет = set(МЕТКА.findall(текст)) - set(тайминги[id_]['marks'])
        if нет:
            raise config.ОшибкаКонфига(f'Бит «{id_}»: метки {sorted(нет)} есть в тексте, но нет во временах озвучки; озвучьте бит заново')


def собрать(папка, выход=None, стиль_имя=None):
    папка = Path(папка).resolve()
    ep, биты = config.эпизод(папка)
    стиль = config.дополнить_стиль(config.стиль(стиль_имя or ep.get('стиль', 'dark-yard'), папка), ep)
    аудио = папка / 'audio'
    if not (аудио / 'timings.json').exists():
        raise config.ОшибкаКонфига(f'Нет {аудио}/timings.json: сначала озвучьте эпизод (python scripts/mm.py озвучить {папка.name})')
    тайминги = json.loads((аудио / 'timings.json').read_text(encoding='utf-8'))
    проверить_озвучку(биты, тайминги)

    вых = Path(выход) if выход else Path.cwd() / 'build' / (папка.name + (f'--{Path(стиль_имя).stem}' if стиль_имя else ''))
    if вых.exists():
        if not any(x.name == 'build' for x in вых.parents):
            raise config.ОшибкаКонфига(f'Не буду стирать {вых}: очищаются только папки внутри build/')
        shutil.rmtree(вых)
    (вых / 'engine').mkdir(parents=True)
    gitignore.скрыть_от_git(вых, '*')                   # папка пересоздаётся при каждой сборке, коммитить в ней нечего
    for f in ДВИЖОК:
        src = config.ROOT / 'engine' / f
        if not src.exists():
            raise config.ОшибкаКонфига(f'Нет файла движка {src}')
        shutil.copy(src, вых / 'engine' / f)
    shutil.copytree(config.ROOT / 'fonts', вых / 'fonts')
    (вых / 'episode').mkdir()
    скрипты = ep.get('скрипты', ['scenes.js'])
    for f in скрипты:
        shutil.copy(папка / f, вых / 'episode' / Path(f).name)
    shutil.copytree(аудио, вых / 'audio', ignore=shutil.ignore_patterns('timings.json', '*.wav', '.gitignore'))
    shutil.copy(config.ROOT / 'assets' / 'grain.png', вых / 'grain.png')
    (вых / 'sfx').mkdir()
    for f in (config.ROOT / 'assets' / 'sfx').glob('*.mp3'):
        shutil.copy(f, вых / 'sfx' / f.name)

    замены = {_слово(k): v for k, v in ep.get('субтитры', {}).get('замены', {}).items()}   # как слово звучит → как выглядит в субтитрах
    слова = {id_: [[round(t, 3), замены.get(_слово(w), w)] for t, w in тайминги[id_]['words']] for id_ in биты}
    данные = {id_: {'dur': тайминги[id_]['dur'], 'marks': тайминги[id_]['marks']} for id_ in биты}
    (вых / 'cues.json').write_text(json.dumps({id_: реплики(биты[id_], тайминги[id_]['words'], замены) for id_ in биты}, ensure_ascii=False), encoding='utf-8')
    (вых / 'style.js').write_text('window.STYLE = ' + config.в_js(стиль) + ';\n', encoding='utf-8')
    (вых / 'data.js').write_text('window.TIMINGS = ' + config.в_js(данные) + ';\nwindow.WORDS = ' + config.в_js(слова) + ';\n', encoding='utf-8')
    css = стиль.get('fonts', {}).get('files') or ['fonts/oswald.css']
    html = ['<!doctype html>', '<html lang="ru">', '<head>', '<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f'<title>{ep.get("название", папка.name)}</title>']
    html += [f'<link rel="stylesheet" href="{c}">' for c in css]
    html += ['</head>', '<body>', '<script src="style.js"></script>', '<script src="data.js"></script>']
    html += [f'<script src="engine/{f}"></script>' for f in ДВИЖОК]
    html += [f'<script src="episode/{Path(f).name}"></script>' for f in скрипты]
    html += ['</body>', '</html>']
    (вых / 'index.html').write_text('\n'.join(html) + '\n', encoding='utf-8')
    return вых

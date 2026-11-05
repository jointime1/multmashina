"""Конфиги: стили и эпизоды на YAML с русскими ключами → объект для движка.

Ключи по-русски, потому что инструмент для русскоязычного автора; внутри движка они английские. Перевод и проверка — здесь:
опечатка в ключе сразу даёт понятную ошибку, а не молча теряется.
"""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

# разделы стиля и их ключи: русский → английский
СТИЛЬ = {
    'сцена': ('stage', {'ширина': 'w', 'высота': 'h'}),
    'палитра': ('palette', {'тёмный': 'dark', 'светлый': 'light', 'красный': 'red', 'акцент': 'accent', 'приглушённый': 'muted',
                            'маркер': 'mark', 'зелёный': 'green', 'контур': 'ink', 'глубина': 'sea', 'сталь': 'steel'}),
    'шрифты': ('fonts', {'заголовки': 'display', 'запасные': 'fallback', 'моно': 'mono', 'подгрузить': 'preload', 'файлы': 'files'}),
    'субтитры': ('captions', {'y': 'y', 'размер': 'size', 'цвет': 'color', 'обводка': 'stroke', 'слов': 'words', 'знаков': 'chars',
                              'пауза': 'gap', 'ширина': 'max_width'}),
    'офис': ('office', {'стена': 'wall', 'низ_стены': 'wall2', 'потолок': 'ceiling', 'пол': 'floor', 'окно_верх': 'glass1', 'окно_низ': 'glass2', 'здания': 'bldg'}),
    'эффекты': ('effects', {'зерно': 'grain', 'виньетка': 'vignette', 'опережение': 'lead', 'пауза_после_бита': 'hold'}),
}
КОМНАТА = {'стена': 'wall', 'низ_стены': 'wall2', 'пол': 'floor', 'горизонт': 'hz', 'лампа_x': 'lampX', 'свет': 'glow', 'трубы': 'pipes',
           'узор': 'seed', 'вывеска': 'sign', 'цвет_вывески': 'signCol', 'вывеска_x': 'signX', 'вывеска_y': 'signY', 'размер_вывески': 'signSize'}
ГЕРОЙ = {'кожа': 'skin', 'волосы': 'hair', 'очки': 'glasses', 'толстовка': 'hoodCol', 'пиджак': 'suit', 'рубашка': 'shirt', 'галстук': 'tie',
         'лысый': 'bald', 'длинные_волосы': 'longHair', 'помада': 'lips', 'без_красного_носа': 'noNose', 'кепка': 'capCol', 'коробка': 'box',
         'доспех': 'armor', 'плащ': 'cloak', 'руки': 'arms', 'тату': 'tattoo', 'комплекция': 'build', 'усы': 'mustache', 'цвет_усов': 'mustCol',
         'щетина_на_голове': 'buzz', 'глаза': 'eyeCol', 'брови': 'browCol', 'надпись': 'emblem', 'цвет_надписи': 'emblemCol'}


class ОшибкаКонфига(Exception):
    pass


def _перевод(данные, словарь, где):
    res = {}
    for k, v in данные.items():
        if k not in словарь:
            raise ОшибкаКонфига(f'{где}: неизвестный ключ «{k}». Допустимые: {", ".join(словарь)}')
        res[словарь[k]] = v
    return res


def читать(path):
    """Прочитать YAML-файл; ошибки — по-русски и с именем файла."""
    path = Path(path)
    try:
        данные = yaml.safe_load(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise ОшибкаКонфига(f'Нет файла {path}')
    except yaml.YAMLError as e:
        raise ОшибкаКонфига(f'{path}: ошибка в YAML: {e}')
    return данные or {}


def стиль(имя_или_путь, папка_эпизода=None):
    """Загрузить стиль: имя (сначала styles/ рядом с эпизодом, потом styles/ инструмента) или путь к .yaml. Возвращает словарь для window.STYLE."""
    p = Path(имя_или_путь)
    if not p.suffix:
        свой = Path(папка_эпизода) / 'styles' / f'{имя_или_путь}.yaml' if папка_эпизода else None
        p = свой if свой and свой.exists() else ROOT / 'styles' / f'{имя_или_путь}.yaml'
    сырой = читать(p)
    res = {'name': сырой.pop('название', p.stem), 'rooms': {}, 'characters': {}}
    комнаты, герои = сырой.pop('комнаты', {}), сырой.pop('герои', {})
    for раздел, данные in сырой.items():
        if раздел not in СТИЛЬ:
            raise ОшибкаКонфига(f'{p.name}: неизвестный раздел «{раздел}». Допустимые: {", ".join(СТИЛЬ)}, комнаты, герои')
        имя, словарь = СТИЛЬ[раздел]
        res[имя] = _перевод(данные, словарь, f'{p.name} [{раздел}]')
    for k, v in комнаты.items():
        res['rooms'][k] = _перевод(v, КОМНАТА, f'{p.name} [комнаты.{k}]')
    for k, v in герои.items():
        res['characters'][k] = _перевод(v, ГЕРОЙ, f'{p.name} [герои.{k}]')
    ш = res.setdefault('fonts', {})
    ш['display_stack'] = ', '.join(f'"{x}"' if ' ' in x and not x.startswith('"') else x for x in [ш.get('display', 'Oswald'), *[s.strip() for s in ш.get('fallback', 'Arial Narrow, sans-serif').split(',')]])
    return res


def дополнить_стиль(стиль, ep):
    """Комнаты и герои из episode.yaml добавляются к стилю (и перекрывают одноимённые): кто герои — часть эпизода, а не стиля."""
    for ключ, словарь, имя in (('комнаты', КОМНАТА, 'rooms'), ('герои', ГЕРОЙ, 'characters')):
        for k, v in (ep.get(ключ) or {}).items():
            стиль[имя][k] = {**стиль[имя].get(k, {}), **_перевод(v, словарь, f'episode.yaml [{ключ}.{k}]')}
    return стиль


def _слить(база, сверху):
    """Словари сливаются по ключам вглубь, всё остальное (списки, числа, строки) заменяется значением эпизода."""
    res = dict(база)
    for k, v in сверху.items():
        res[k] = _слить(res[k], v) if isinstance(v, dict) and isinstance(res.get(k), dict) else v
    return res


def эпизод(папка):
    """Прочитать episode.yaml и narration.yaml папки эпизода.

    В episode.yaml можно указать `серия: ../серия.yaml`: общие герои, комнаты, голоса и настройки серии лежат там, а в эпизоде
    остаётся только своё (значения эпизода перекрывают общие). Бит в narration.yaml — строка (говорит голос по умолчанию) или список
    реплик разных голосов: `- олег: "Текст"`. Для остальных модулей бит остаётся строкой (реплики склеены), а список реплик с голосами
    лежит в ep['_реплики'][id_бита] как [(голос или None, текст), …].
    """
    папка = Path(папка)
    ep = читать(папка / 'episode.yaml')
    if ep.get('серия'):
        ep = _слить(читать(папка / ep['серия']), {k: v for k, v in ep.items() if k != 'серия'})
    нар = читать(папка / 'narration.yaml')
    if 'биты' not in нар or not нар['биты']:
        raise ОшибкаКонфига(f'{папка}/narration.yaml: нужен раздел [биты] с репликами')
    биты, реплики = {}, {}
    for id_, значение in нар['биты'].items():
        if isinstance(значение, str):
            сегменты = [(None, значение)]
        elif isinstance(значение, list) and значение and all(isinstance(x, dict) and len(x) == 1 for x in значение):
            сегменты = [(next(iter(x)), str(next(iter(x.values())))) for x in значение]
        else:
            raise ОшибкаКонфига(f'narration.yaml [биты.{id_}]: бит — это строка или список реплик вида «- голос: текст»')
        реплики[id_] = сегменты
        биты[id_] = ' '.join(t.strip() for _, t in сегменты)
    ep['_реплики'] = реплики
    return ep, биты


def в_js(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1)

"""Разговорный рот: герой говорит, пока звучит его голос, и молчит, пока говорит другой. Слова бита делятся между репликами по голосам."""
import json

import pytest
import yaml

from mmlib import build, config
from test_motion import _Браузер
from test_variety import _эпизод, в_пустой  # noqa: F401

# ---------- сборка: кто и когда говорит ----------

СЛОВА = [[.1, 'Раз'], [.6, 'два'], [1.1, 'Три'], [1.6, 'четыре'], [2.0, 'пять']]


def test_слова_бита_делятся_между_голосами_по_числу_слов():
    строки = [('рассказчик', 'Раз [[a]]два.'), ('петя', 'Три четыре пять.')]
    assert build.речь(строки, СЛОВА, 2.6, None) == [['рассказчик', .1, 1.1], ['петя', 1.1, 2.6]]


def test_пустой_голос_заменяется_голосом_по_умолчанию():
    assert build.речь([(None, 'Раз два три четыре пять.')], СЛОВА, 2.6, 'рассказчик') == [['рассказчик', .1, 2.6]]


def test_реплика_без_слов_пропускается():
    assert build.речь([('петя', '[[a]]'), ('вася', 'Раз два.')], СЛОВА, 2.6, None) == [['вася', .1, 2.6]]


def test_собранный_эпизод_хранит_реплики_по_голосам(мини, в_пустой):  # noqa: F811
    _эпизод(мини, {'один': "room(s, 'комната');"}, длит=2.6, слов=5)
    (мини / 'narration.yaml').write_text('биты:\n  один:\n    - рассказчик: "Раз два."\n    - петя: "Три четыре пять."\n', encoding='utf-8')
    тайминги = {'один': {'dur': 2.6, 'marks': {}, 'words': СЛОВА}}
    (мини / 'audio' / 'timings.json').write_text(json.dumps(тайминги, ensure_ascii=False), encoding='utf-8')
    вых = build.собрать(мини, выход=config.ROOT / 'build' / 'тест-речь')
    данные = json.loads((вых / 'data.js').read_text(encoding='utf-8').split('window.TIMINGS = ')[1].split(';\nwindow.WORDS')[0])
    assert данные['один']['lines'] == [['рассказчик', .1, 1.1], ['петя', 1.1, 2.6]]


# ---------- движок: рот открывается на своих словах ----------

ГОЛОВА = "room(s, 'комната'); hero(s, 'петя', CX, 900, 1.2, [[0, 'neutral']], 0, D%s);"


def _говорящий(мини, опции='', персонаж='вырезка'):
    """Эпизод из двух реплик: сначала рассказчик (до 1,1 с), потом петя."""
    _эпизод(мини, {'один': ГОЛОВА % опции}, длит=2.6, слов=5)
    (мини / 'narration.yaml').write_text('биты:\n  один:\n    - рассказчик: "Раз два."\n    - петя: "Три четыре пять."\n', encoding='utf-8')
    (мини / 'audio' / 'timings.json').write_text(json.dumps({'один': {'dur': 2.6, 'marks': {}, 'words': СЛОВА}}, ensure_ascii=False), encoding='utf-8')
    ep = yaml.safe_load((мини / 'episode.yaml').read_text(encoding='utf-8'))
    ep.pop('анимации', None)
    ep['манера'] = {'персонаж': персонаж}
    (мини / 'episode.yaml').write_text(yaml.safe_dump(ep, allow_unicode=True), encoding='utf-8')
    return build.собрать(мини, выход=config.ROOT / 'build' / 'тест-речь')


def _рты(б, моменты):
    res = []
    for t in моменты:
        б.page.evaluate('t => MM.seek(t)', t)
        рты = б.page.evaluate("() => [...document.querySelectorAll('[data-mouth]')].map(e => e.getAttribute('opacity') === null ? 1 : +e.getAttribute('opacity'))")
        res.append(рты.index(1))
    return res


МОМЕНТЫ = [i * .03 for i in range(1, 85)]


@pytest.mark.browser
def test_герой_открывает_рот_только_на_словах_своего_голоса(мини, в_пустой):  # noqa: F811
    with _Браузер(_говорящий(мини)) as б:
        рты = _рты(б, МОМЕНТЫ)
    пока_говорит_рассказчик = [r for t, r in zip(МОМЕНТЫ, рты) if t < 1.05]
    пока_говорит_петя = [r for t, r in zip(МОМЕНТЫ, рты) if 1.1 <= t < 2.4]
    assert set(пока_говорит_рассказчик) == {0}, 'пока говорит рассказчик, герой молчит'
    assert 3 in пока_говорит_петя and 0 in пока_говорит_петя, 'на своих словах рот хлопает: открывается и закрывается'


@pytest.mark.browser
def test_говорит_на_всех_словах_когда_так_сказано(мини, в_пустой):  # noqa: F811
    with _Браузер(_говорящий(мини, ', { talk: true }')) as б:
        рты = _рты(б, МОМЕНТЫ)
    assert 3 in [r for t, r in zip(МОМЕНТЫ, рты) if t < 1.05], 'talk: true — говорит и на репликах рассказчика'


@pytest.mark.browser
def test_молчит_когда_сказано_молчать(мини, в_пустой):  # noqa: F811
    with _Браузер(_говорящий(мини, ', { talk: false }')) as б:
        assert set(_рты(б, МОМЕНТЫ)) == {0}


@pytest.mark.browser
def test_свои_окна_речи(мини, в_пустой):  # noqa: F811
    with _Браузер(_говорящий(мини, ', { talk: [[.3, .8]] }')) as б:
        рты = _рты(б, МОМЕНТЫ)
    assert 3 in [r for t, r in zip(МОМЕНТЫ, рты) if .3 <= t < .8] and set(r for t, r in zip(МОМЕНТЫ, рты) if t > .9) == {0}


@pytest.mark.browser
def test_рисованный_рот_классики_раскрывается_на_слове(мини, в_пустой):  # noqa: F811
    """Не только дискретные куклы: у героя с рисованным ртом рот становится выше на словах героя и остаётся закрытым на чужих."""
    высота = "() => document.querySelector('[data-head] g[transform=\"translate(0 78)\"] > path').getBBox().height"
    with _Браузер(_говорящий(мини, персонаж='классика')) as б:
        молчит, говорит = [], []
        for t in МОМЕНТЫ:
            б.page.evaluate('t => MM.seek(t)', t)
            (молчит if t < 1.05 else говорит if 1.1 <= t < 2.4 else []).append(б.page.evaluate(высота))
    assert max(молчит) < 12, f'рот закрыт, пока говорит другой: {max(молчит)}'
    assert max(говорит) > 30 and min(говорит) < 12, f'рот хлопает на своих словах: {min(говорит)}..{max(говорит)}'


@pytest.mark.parametrize('слово', ['talk', 'lines', 'хлопает по слогу'])
def test_речь_описана_в_справочнике(слово):
    assert слово in (config.ROOT / 'docs' / 'scenes.md').read_text(encoding='utf-8')

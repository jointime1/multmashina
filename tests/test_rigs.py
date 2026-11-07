"""Школы анимации: из чего собран персонаж и как он двигается. Фильтр и цвет рисунка (манера) тут не при чём: проверяем устройство кадра и движение."""
import base64
import colorsys
import re

import pytest
import yaml

from mmlib import build, config
from test_motion import _Браузер
from test_variety import _проверить, _эпизод, в_пустой  # noqa: F401

ЭМОЦИИ = "room(s, 'комната'); hero(s, 'петя', CX, 900, 1.2, [[0, 'neutral'], [.5, 'shock'], [1.1, 'rage']], 0, D);"
ПОКОЙ = "room(s, 'комната'); hero(s, 'петя', CX, 900, 1.2, [[0, 'neutral']], 0, D);"
ХОДЬБА = "room(s, 'комната'); figure(s, 'петя', 200, 1100, .6, { to: 700, t0: 0, t1: D });"
ПЕРСОНАЖИ = {'каракуля': 'doodle', 'марионетка': 'puppet', 'желе': 'jelly', 'силуэт': 'shadow', 'шланг': 'hose', 'пиксель': 'pixel', 'вырезка': 'paper', 'классика': 'classic'}


def _школа(мини, сцена=ЭМОЦИИ, персонаж=None, характер=None):
    """Эпизод с героем и нужной школой: персонаж (манера) и характер (анимации)."""
    _эпизод(мини, {'один': сцена})
    ep = yaml.safe_load((мини / 'episode.yaml').read_text(encoding='utf-8'))
    ep.pop('манера', None), ep.pop('анимации', None)                # папка одна на весь тест: прошлая школа не должна остаться
    if персонаж:
        ep['манера'] = {'персонаж': персонаж}
    if характер:
        ep['анимации'] = {'характер': характер}
    (мини / 'episode.yaml').write_text(yaml.safe_dump(ep, allow_unicode=True), encoding='utf-8')
    return build.собрать(мини, выход=config.ROOT / 'build' / 'тест-школа')


def _стиль(tmp_path, **разделы):
    f = tmp_path / 'свой.yaml'
    f.write_text(yaml.safe_dump(разделы, allow_unicode=True), encoding='utf-8')
    return config.стиль(f)


def _знаки(значения, порог=1e-9):
    """Сколько раз ряд пересекает ноль (почти нулевые значения не считаем)."""
    знаки = [v > 0 for v in значения if abs(v) > порог]
    return sum(1 for a, b in zip(знаки, знаки[1:]) if a != b)


УГОЛ = "e => { const m = /rotate\\((-?[\\d.]+)/.exec(e.getAttribute('transform') || ''); return m ? +m[1] : 0; }"
МАСШТАБ = "e => { const m = /scale\\((-?[\\d.]+) (-?[\\d.]+)/.exec(e.getAttribute('transform') || ''); return m ? [+m[1], +m[2]] : [1, 1]; }"


# ---------- конфиг ----------

def test_персонаж_и_характер_переводятся(tmp_path):
    с = _стиль(tmp_path, манера={'персонаж': 'марионетка'}, анимации={'характер': 'пружина'})
    assert с['manner'] == {'rig': 'puppet'} and с['motion'] == {'feel': 'spring'}


@pytest.mark.parametrize('имя, ключ', ПЕРСОНАЖИ.items())
def test_каждый_персонаж_читается(tmp_path, имя, ключ):
    assert _стиль(tmp_path, манера={'персонаж': имя})['manner']['rig'] == ключ


def test_неизвестный_персонаж_называет_допустимые(tmp_path):
    with pytest.raises(config.ОшибкаКонфига, match='марионетка'):
        _стиль(tmp_path, манера={'персонаж': 'робот'})


def test_неизвестный_характер_называет_допустимые(tmp_path):
    with pytest.raises(config.ОшибкаКонфига, match='пружина'):
        _стиль(tmp_path, анимации={'характер': 'вялый'})


def test_эпизод_может_сменить_персонажа_стиля(tmp_path):
    с = config.дополнить_стиль(_стиль(tmp_path, манера={'персонаж': 'каракуля', 'линия': 2}), {'манера': {'персонаж': 'желе'}})
    assert с['manner'] == {'rig': 'jelly', 'line': 2}


# ---------- характер движения: кривые ----------

КРИВЫЕ = "() => { const q = Array.from({ length: 201 }, (_, i) => i / 200); return { out: q.map(out), io: q.map(io), soft: q.map(soft), back: q.map(back), out2: out(.2), io25: io(.25), soft25: soft(.25) }; }"


def _кривые(мини, характер):
    with _Браузер(_школа(мини, ПОКОЙ, характер=характер)) as б:
        return б.page.evaluate(КРИВЫЕ)


@pytest.mark.browser
def test_без_характера_плавности_прежние(мини, в_пустой):  # noqa: F811
    к = _кривые(мини, None)
    assert abs(к['out2'] - (1 - .8 ** 3)) < 1e-9 and _знаки([v - 1 for v in к['back'][:-1]]) == 1


@pytest.mark.browser
def test_механика_двигает_ровно_без_разгона_и_перелёта(мини, в_пустой):  # noqa: F811
    к = _кривые(мини, 'механика')
    assert к['out2'] == pytest.approx(.2) and к['io25'] == pytest.approx(.25) and к['soft25'] == pytest.approx(.25)
    assert max(к['back']) <= 1 + 1e-9


@pytest.mark.browser
def test_резкий_характер_долетает_почти_сразу(мини, в_пустой):  # noqa: F811
    к = _кривые(мини, 'резкий')
    assert к['out2'] > .7 and max(к['back']) <= 1.2


@pytest.mark.browser
def test_пружина_раскачивается_вокруг_цели(мини, в_пустой):  # noqa: F811
    к = _кривые(мини, 'пружина')
    assert max(к['back']) >= 1.2 and _знаки([v - 1 for v in к['back'][:-1]]) >= 3
    assert к['back'][0] == pytest.approx(0) and к['back'][-1] == pytest.approx(1)


@pytest.mark.browser
@pytest.mark.parametrize('характер', ['плавный', 'пружина', 'резкий', 'механика'])
def test_числа_и_линии_не_перелетают_цель_ни_в_каком_характере(мини, в_пустой, характер):  # noqa: F811
    """Счётчик считает по out, линия рисуется по out: перелёт дал бы 1 120 000 вместо 1 000 000."""
    к = _кривые(мини, характер)
    assert max(к['out']) <= 1 + 1e-9 and max(к['io']) <= 1 + 1e-9 and max(к['soft']) <= 1 + 1e-9


# ---------- устройство персонажей ----------

@pytest.mark.browser
@pytest.mark.parametrize('имя, ключ', ПЕРСОНАЖИ.items())
def test_у_героя_любого_персонажа_есть_метки_движка(мини, в_пустой, имя, ключ):  # noqa: F811
    with _Браузер(_школа(мини, персонаж=имя)) as б:
        б.page.evaluate('MM.seek(.7)')
        метки = б.page.evaluate("() => ['data-hero', 'data-head', 'data-body'].map(a => document.querySelectorAll('[' + a + ']').length)")
        assert метки == [1, 1, 1]
        assert б.page.evaluate("document.querySelector('[data-hero]').getAttribute('data-rig')") == ключ


ФОРМА = """() => { const skip = new Set(['transform', 'opacity', 'display']);
  return [...document.querySelectorAll('[data-hero] *')].map(e => [e.tagName, ...[...e.attributes].filter(a => !skip.has(a.name)).map(a => a.name + '=' + a.value)].join('|')); }"""
ПОЗА = "() => [...document.querySelectorAll('[data-hero] *')].map(e => (e.getAttribute('transform') || '') + '/' + (e.getAttribute('opacity') || ''))"


def _формы_и_позы(б, моменты):
    формы, позы = [], []
    for t in моменты:
        б.page.evaluate('t => MM.seek(t)', t)
        формы.append(б.page.evaluate(ФОРМА))
        позы.append(б.page.evaluate(ПОЗА))
    return формы, позы


@pytest.mark.browser
def test_у_марионетки_детали_жёсткие_а_у_обычного_героя_лицо_гнётся(мини, в_пустой):  # noqa: F811
    """Бумажные детали только едут и поворачиваются; смена выражения — это смена готовых деталей, а не изгиб контура."""
    моменты = (.1, .7, 1.3)
    for имя in ('марионетка', 'вырезка'):
        with _Браузер(_школа(мини, персонаж=имя)) as б:
            формы, позы = _формы_и_позы(б, моменты)
        assert формы[0] == формы[1] == формы[2], f'у {имя} сменилась форма детали'
        assert позы[0] != позы[1] and позы[1] != позы[2], f'{имя} не двигается'
    with _Браузер(_школа(мини)) as б:
        формы, _ = _формы_и_позы(б, моменты)
    assert формы[0] != формы[1], 'контрольный героя без персонажа должен гнуть лицо'


@pytest.mark.browser
@pytest.mark.parametrize('имя', ['марионетка', 'вырезка', 'пиксель'])
def test_рот_всегда_одна_готовая_деталь_без_плавных_переходов(мини, в_пустой, имя):  # noqa: F811
    with _Браузер(_школа(мини, персонаж=имя)) as б:
        видимые = set()
        for i in range(31):
            б.page.evaluate('t => MM.seek(t)', i * .05)
            рты = б.page.evaluate("() => [...document.querySelectorAll('[data-mouth]')].map(e => { const o = e.getAttribute('opacity'); return o === null ? 1 : +o; })")
            assert len(рты) >= 5, 'нужен набор готовых ртов'
            assert sorted(рты)[-1] == 1 and sum(1 for o in рты if o > 0) == 1, (i * .05, рты)
            видимые.add(рты.index(1))
        assert len(видимые) >= 3, 'рот не меняется вслед за эмоцией'


@pytest.mark.browser
def test_глаза_марионетки_дробятся_на_ступени(мини, в_пустой):  # noqa: F811
    """Веко сидит в одном из нескольких положений: между ними нет плавного перехода."""
    with _Браузер(_школа(мини, персонаж='марионетка')) as б:
        положения = set()
        for i in range(61):
            б.page.evaluate('t => MM.seek(t)', i * .025)
            положения.add(tuple(б.page.evaluate("() => [...document.querySelectorAll('[data-lid]')].map(e => e.getAttribute('transform'))")))
        assert 2 <= len(положения) <= 8, len(положения)


@pytest.mark.browser
@pytest.mark.parametrize('имя', ['каракуля', 'силуэт', 'шланг'])
def test_руки_играют_эмоцию_а_у_обычного_героя_рук_нет(мини, в_пустой, имя):  # noqa: F811
    углы = {}
    with _Браузер(_школа(мини, персонаж=имя)) as б:
        for t in (.2, .8):
            б.page.evaluate('t => MM.seek(t)', t)
            углы[t] = б.page.evaluate(f"() => [...document.querySelectorAll('[data-arm]')].map({УГОЛ})")
    assert len(углы[.2]) == 2 and len(углы[.8]) == 2
    assert all(abs(углы[.8][i] - углы[.2][i]) > 40 for i in (0, 1)), f'руки не отреагировали на шок: {углы}'
    assert углы[.8][0] * углы[.8][1] < 0, 'руки вскидываются в разные стороны от тела'


@pytest.mark.browser
def test_у_обычного_героя_рук_нет(мини, в_пустой):  # noqa: F811
    with _Браузер(_школа(мини)) as б:
        assert б.page.evaluate("document.querySelectorAll('[data-arm]').length") == 0


@pytest.mark.browser
def test_каракуля_закрывает_лицо_руками_когда_плачет(мини, в_пустой):  # noqa: F811
    with _Браузер(_школа(мини, "room(s, 'комната'); hero(s, 'петя', CX, 900, 1.2, [[0, 'neutral'], [.5, 'cry']], 0, D);", персонаж='каракуля')) as б:
        for t in (.2, .9):
            б.page.evaluate('t => MM.seek(t)', t)
        руки = б.page.evaluate("() => [...document.querySelectorAll('[data-arm]')].map(e => { const h = e.getBoundingClientRect(), f = document.querySelector('[data-head]').getBoundingClientRect(); return h.right > f.left && h.left < f.right && h.top < f.bottom && h.bottom > f.top; })")
    assert руки == [True, True], 'руки должны подняться к лицу'


@pytest.mark.browser
def test_желе_пружинит_после_смены_эмоции(мини, в_пустой):  # noqa: F811
    """После реакции тело сжимается и вытягивается несколько раз, затухая; у обычного героя одно вздрагивание."""
    моменты = [.5 + i * .02 for i in range(23)]

    def отклонения(б):
        res = []
        for t in моменты:
            б.page.evaluate('t => MM.seek(t)', t)
            res.append(б.page.evaluate(f"() => ({МАСШТАБ})(document.querySelector('[data-body]'))")[1] - 1)
        return res

    with _Браузер(_школа(мини, персонаж='желе')) as б:
        желе = отклонения(б)
    with _Браузер(_школа(мини)) as б:
        обычный = отклонения(б)
    assert _знаки(желе, 1e-3) >= 2, f'желе не раскачалось: {желе}'
    assert max(map(abs, желе[-5:])) < max(map(abs, желе[:10])) * .6, 'качание не затухает'
    assert _знаки(обычный, 1e-3) <= 1


@pytest.mark.browser
def test_желе_колышется_и_в_покое(мини, в_пустой):  # noqa: F811
    def размах(б):
        ys = []
        for i in range(21):
            б.page.evaluate('t => MM.seek(t)', .3 + i * .05)
            ys.append(б.page.evaluate(f"() => ({МАСШТАБ})(document.querySelector('[data-body]'))")[1])
        return max(ys) - min(ys)

    with _Браузер(_школа(мини, ПОКОЙ, персонаж='желе')) as б:
        assert размах(б) >= .05
    with _Браузер(_школа(мини, ПОКОЙ)) as б:
        assert размах(б) < .03


@pytest.mark.browser
@pytest.mark.parametrize('имя', ['марионетка', 'желе'])
def test_зрачок_лежит_поверх_белка_глаза(мини, в_пустой, имя):  # noqa: F811
    """Белок, нарисованный после зрачка, закрыл бы его: глаза были бы пустыми белыми дисками."""
    with _Браузер(_школа(мини, ПОКОЙ, персонаж=имя)) as б:
        б.page.evaluate('MM.seek(.7)')
        верно = б.page.evaluate("() => { const белки = [...document.querySelectorAll('[data-hero] ellipse')].filter(e => e.getAttribute('fill') === '#fff' && !e.hasAttribute('opacity')); return белки.length === 2 && белки.every(e => e.nextElementSibling && e.nextElementSibling.querySelector('circle') && e.nextElementSibling.querySelector('circle').getAttribute('fill') !== '#fff'); }")
        assert верно, 'зрачок должен идти в дереве после белка'
        центр = б.page.evaluate("() => { const e = document.querySelector('[data-hero] ellipse[fill=\"#fff\"]:not([opacity])'), r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }")
        assert центр


# ---------- полный цвет ----------

СТИЛИ_ВСЕ = sorted(f.stem for f in (config.ROOT / 'styles').glob('*.yaml'))
ПАЛИТРА_ПО_УМОЛЧАНИЮ = {'dark': '#0b1220', 'light': '#f1f5f9', 'red': '#ff3b3b', 'accent': '#38bdf8', 'muted': '#94a3b8', 'mark': '#ffd23f', 'green': '#22c55e', 'ink': '#12141c', 'sea': '#0c4a6e', 'steel': '#94a3b8'}


def _hsl(цвет):
    r, g, b = (int(цвет[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s, l


@pytest.mark.parametrize('имя', СТИЛИ_ВСЕ)
def test_готовый_стиль_полноцветный(имя):
    """Тона сводят кадр к двум-четырём краскам: это одноцветная картинка. Готовые стили её не используют (ключ `тона` остаётся для своих)."""
    с = config.стиль(имя)
    assert not с.get('manner', {}).get('tones'), f'{имя}: кадр сведён к тонам, а нужен полный цвет'
    палитра = {**ПАЛИТРА_ПО_УМОЛЧАНИЮ, **с.get('palette', {})}
    яркие = [_hsl(c) for c in палитра.values() if _hsl(c)[1] >= .35 and .15 <= _hsl(c)[2] <= .85]
    assert len(яркие) >= 4 and len({int(h // 60) for h, _, _ in яркие}) >= 3, f'{имя}: в палитре мало разных насыщенных цветов: {палитра}'


# ---------- силуэт ----------

@pytest.mark.browser
def test_силуэт_залит_глубоким_цветом_героя_с_яркой_каймой(мини, в_пустой):  # noqa: F811
    """Сплошная фигура не чёрная: глубокий насыщенный цвет героя, по краю цветной контровой свет, черты светятся тем же цветом."""
    with _Браузер(_школа(мини, персонаж='силуэт')) as б:
        б.page.evaluate('MM.seek(.7)')
        р = б.page.evaluate("""() => {
          const тёмные = [...document.querySelectorAll('[data-hero] *')].filter(e => !e.closest('[data-light]') && e.getAttribute('fill') && e.getAttribute('fill') !== 'none');
          const края = [...document.querySelectorAll('[data-hero] *')].filter(e => !e.closest('[data-light]') && e.getAttribute('stroke') && e.getAttribute('stroke') !== 'none');
          return { заливки: [...new Set(тёмные.map(e => e.getAttribute('fill')))], края: [...new Set(края.map(e => e.getAttribute('stroke')))], черты: document.querySelectorAll('[data-light]').length };
        }""")
    assert len(р['заливки']) == 1 and р['черты'] >= 4, р
    h, s_, l = _hsl(р['заливки'][0])
    assert s_ >= .35 and l <= .3, f'фигура должна быть глубокого цвета, а не чёрной: {р["заливки"]}'
    каймы = [c for c in р['края'] if c != р['заливки'][0]]
    assert len(каймы) == 1, f'нужна одна цветная кайма: {р["края"]}'
    assert _hsl(каймы[0])[1] >= .6 and _hsl(каймы[0])[2] >= .5, f'кайма должна быть яркой: {каймы}'
    assert abs(_hsl(каймы[0])[0] - h) < 3, 'кайма того же оттенка, что фигура'


@pytest.mark.browser
def test_силуэты_разных_героев_разного_цвета(мини, в_пустой):  # noqa: F811
    сцена = ("room(s, 'комната'); hero(s, 'петя', 250, 900, 1, [[0, 'neutral']], 0, D, { hoodCol: '#14532d' });"
             "hero(s, 'петя', 650, 900, 1, [[0, 'neutral']], 0, D, { hoodCol: '#7c1d1d' });")
    with _Браузер(_школа(мини, сцена, персонаж='силуэт')) as б:
        б.page.evaluate('MM.seek(.7)')
        цвета = б.page.evaluate("() => [...document.querySelectorAll('[data-hero]')].map(h => h.querySelector('circle').getAttribute('fill'))")
    h1, h2 = _hsl(цвета[0])[0], _hsl(цвета[1])[0]
    assert min(abs(h1 - h2), 360 - abs(h1 - h2)) > 60, f'зелёный и красный герои должны отличаться цветом силуэта: {цвета}'


@pytest.mark.browser
def test_глаза_силуэта_косеют_от_злости(мини, в_пустой):  # noqa: F811
    сцена = "room(s, 'комната'); hero(s, 'петя', CX, 900, 1.2, [[0, 'neutral'], [.5, 'rage']], 0, D);"
    углы = {}
    with _Браузер(_школа(мини, сцена, персонаж='силуэт')) as б:
        for t in (.2, 1.0):
            б.page.evaluate('t => MM.seek(t)', t)
            углы[t] = б.page.evaluate(f"() => [...document.querySelectorAll('[data-eye]')].map({УГОЛ})")
    assert len(углы[.2]) == 2 and all(abs(a) < 3 for a in углы[.2])
    assert all(abs(a) > 10 for a in углы[1.0]) and углы[1.0][0] * углы[1.0][1] < 0, 'злые глаза скошены к переносице'


@pytest.mark.browser
@pytest.mark.parametrize('имя', ['силуэт', 'шланг'])
def test_персонаж_не_замирает_и_в_покое(мини, в_пустой, имя):  # noqa: F811
    with _Браузер(_школа(мини, ПОКОЙ, персонаж=имя)) as б:
        позы = set()
        for i in range(8):
            б.page.evaluate('t => MM.seek(t)', .3 + i * .1)
            позы.add(б.page.evaluate("document.querySelector('[data-body]').getAttribute('transform')"))
    assert len(позы) >= 6, 'тело стоит как вкопанное'


# ---------- шланг ----------

ВЕРШИНЫ = "() => ({ y: +/translate\\(\\S+ (-?[\\d.]+)/.exec(document.querySelector('[data-body]').getAttribute('transform'))[1] })"


def _пики(ряд):
    return sum(1 for a, b, c in zip(ряд, ряд[1:], ряд[2:]) if b < a and b < c)


@pytest.mark.browser
def test_шланг_подпрыгивает_в_такт_и_макароны_рук_пляшут(мини, в_пустой):  # noqa: F811
    высоты, макароны = [], set()
    with _Браузер(_школа(мини, ПОКОЙ, персонаж='шланг')) as б:
        for i in range(25):
            б.page.evaluate('t => MM.seek(t)', .3 + i * .05)
            высоты.append(б.page.evaluate(ВЕРШИНЫ)['y'])
            макароны.add(б.page.evaluate("[...document.querySelectorAll('[data-arm] path[data-noodle]')].map(e => e.getAttribute('d')).join('|')"))
    assert _пики(высоты) >= 2, f'нет отскоков в такт: {высоты}'
    assert len(макароны) >= 6, 'руки-макароны не колышутся'
    обычный = []
    with _Браузер(_школа(мини, ПОКОЙ)) as б:
        for i in range(25):
            б.page.evaluate('t => MM.seek(t)', .3 + i * .05)
            обычный.append(б.page.evaluate(ВЕРШИНЫ)['y'])
    assert _пики(обычный) <= 1, 'контрольный обычный герой не должен прыгать'


@pytest.mark.browser
def test_глаза_шланга_с_вырезом_следят_за_взглядом(мини, в_пустой):  # noqa: F811
    сцена = "room(s, 'комната'); hero(s, 'петя', CX, 900, 1.2, [[0, 'neutral', { px: .9 }], [.5, 'neutral', { px: -.9 }]], 0, D);"
    with _Браузер(_школа(мини, сцена, персонаж='шланг')) as б:
        повороты = []
        for t in (.2, .9):
            б.page.evaluate('t => MM.seek(t)', t)
            повороты.append(б.page.evaluate("() => [...document.querySelectorAll('[data-pie]')].map(e => e.getAttribute('transform'))"))
    assert len(повороты[0]) == 2 and повороты[0] != повороты[1], 'вырез зрачка должен поворачиваться за взглядом'


# ---------- пиксель ----------

СЕТКА = 20
ГЕОМЕТРИЯ = """() => [...document.querySelectorAll('[data-hero] *')].map(e => ({
  тег: e.tagName, x: +(e.getAttribute('x') || 0), y: +(e.getAttribute('y') || 0), w: +(e.getAttribute('width') || 0), h: +(e.getAttribute('height') || 0),
  tr: e.getAttribute('transform') || '' }))"""


def _на_сетке(элементы):
    плохие = []
    for e in элементы:
        if e['тег'] not in ('g', 'rect'):
            плохие.append(f"{e['тег']} вместо квадратов")
        for k in ('x', 'y', 'w', 'h'):
            if e[k] % СЕТКА:
                плохие.append(f"{e['тег']} {k}={e[k]}")
        if 'rotate' in e['tr'] or 'scale' in e['tr']:
            плохие.append(f"поворот или масштаб: {e['tr']}")
        for m in re.finditer(r'translate\(\s*(-?[\d.]+)[ ,]+(-?[\d.]+)', e['tr']):
            if float(m.group(1)) % СЕТКА or float(m.group(2)) % СЕТКА:
                плохие.append(f"сдвиг мимо сетки: {e['tr']}")
    return плохие


@pytest.mark.browser
def test_пиксельный_герой_весь_из_квадратов_сетки(мини, в_пустой):  # noqa: F811
    with _Браузер(_школа(мини, персонаж='пиксель')) as б:
        for t in (.1, .7, 1.3):
            б.page.evaluate('t => MM.seek(t)', t)
            плохие = _на_сетке(б.page.evaluate(ГЕОМЕТРИЯ))
            assert not плохие, (t, плохие[:6])


@pytest.mark.browser
def test_пиксельные_руки_это_готовые_позы_спрайтами(мини, в_пустой):  # noqa: F811
    позы = {}
    with _Браузер(_школа(мини, персонаж='пиксель')) as б:
        for i in range(31):
            б.page.evaluate('t => MM.seek(t)', i * .05)
            видимые = б.page.evaluate("() => [...document.querySelectorAll('[data-arm]')].map(a => [...a.querySelectorAll('[data-pose]')].map(p => p.getAttribute('opacity') === null ? 1 : +p.getAttribute('opacity')))")
            assert len(видимые) == 2 and all(len(v) >= 3 and sum(v) == 1 and max(v) == 1 for v in видимые), (i * .05, видимые)
            позы[i] = tuple(v.index(1) for v in видимые)
    assert позы[4] != позы[16], 'поза рук не меняется от шока'


@pytest.mark.browser
def test_человечек_пикселя_шагает_сменой_спрайтов(мини, в_пустой):  # noqa: F811
    with _Браузер(_школа(мини, ХОДЬБА, персонаж='пиксель')) as б:
        кадры = []
        for t in (.3, .5, .7):
            б.page.evaluate('t => MM.seek(t)', t)
            кадры.append(tuple(б.page.evaluate("() => [...document.querySelectorAll('[data-leg]')].map(e => e.getAttribute('opacity') === null ? 1 : +e.getAttribute('opacity'))")))
            assert not _на_сетке(б.page.evaluate(ГЕОМЕТРИЯ)), кадры
        assert len(set(кадры)) >= 2 and all(sum(k) == 1 for k in кадры), кадры


ЯЧЕЙКИ = """async ([ссылка, ячейка]) => {
  const картинка = new Image(); картинка.src = ссылка; await картинка.decode();
  const c = document.createElement('canvas'); c.width = картинка.width; c.height = картинка.height;
  const x = c.getContext('2d'); x.drawImage(картинка, 0, 0);
  const д = x.getImageData(0, 0, c.width, c.height).data;
  let разные = 0, всего = 0;
  for (let y = 3; y < c.height * .7; y += 5) for (let px = 0; px + 1 < c.width; px++) {     // ниже лежат субтитры: они вне фильтра и остаются чёткими
    if ((px + 1) % ячейка === 0) continue;                       // граница ячейки: тут перепад законен
    const i = (y * c.width + px) * 4, j = i + 4;
    всего++; if (Math.abs(д[i] - д[j]) + Math.abs(д[i + 1] - д[j + 1]) + Math.abs(д[i + 2] - д[j + 2]) > 30) разные++;
  }
  return разные / всего;
}"""


def _доля_перепадов_внутри_ячейки(б, ячейка_px):
    б.page.evaluate('MM.seek(.7)')
    ссылка = 'data:image/png;base64,' + base64.b64encode(б.page.screenshot(type='png')).decode()
    return б.page.evaluate(ЯЧЕЙКИ, [ссылка, ячейка_px])


def _без_зерна(мини, манера=None, сцена=ПОКОЙ):
    """Эпизод без зерна и виньетки: шум плёнки лежит поверх фильтра и мешает мерить склейку."""
    _эпизод(мини, {'один': сцена})
    ep = yaml.safe_load((мини / 'episode.yaml').read_text(encoding='utf-8'))
    ep.pop('анимации', None), ep.pop('манера', None)
    ep['эффекты'] = {'зерно': False, 'виньетка': 0}
    if манера:
        ep['манера'] = манера
    (мини / 'episode.yaml').write_text(yaml.safe_dump(ep, allow_unicode=True), encoding='utf-8')
    return build.собрать(мини, выход=config.ROOT / 'build' / 'тест-школа')


@pytest.mark.browser
def test_пиксели_манеры_склеивают_кадр_в_крупные_точки(мини, в_пустой):  # noqa: F811
    """Ячейка 10 единиц сцены = 5 точек на экране 450 px (целое число: дробная ячейка даёт швы): внутри ячейки цвет не меняется, перепады только на её границах."""
    with _Браузер(_без_зерна(мини)) as б:
        обычный = _доля_перепадов_внутри_ячейки(б, 5)
    with _Браузер(_без_зерна(мини, {'пиксели': 10})) as б:
        крупно = _доля_перепадов_внутри_ячейки(б, 5)
    assert обычный > .01, f'контрольный кадр без пикселей должен иметь перепады: {обычный}'
    assert крупно < обычный / 5 and крупно < .004, f'внутри ячейки цвет меняется: {крупно} против {обычный}'


# ---------- фактура краски ----------

РАЗБРОС = """async ссылка => {
  const картинка = new Image(); картинка.src = ссылка; await картинка.decode();
  const c = document.createElement('canvas'); c.width = картинка.width; c.height = картинка.height;
  const x = c.getContext('2d'); x.drawImage(картинка, 0, 0);
  const w = c.width, д = x.getImageData(0, 0, w, Math.floor(c.height * .22)).data, h = д.length / 4 / w, разницы = [];
  const я = (px, py) => .2126 * д[(py * w + px) * 4] + .7152 * д[(py * w + px) * 4 + 1] + .0722 * д[(py * w + px) * 4 + 2];
  for (let py = 1; py < h - 1; py += 2) for (let px = 1; px < w - 1; px += 2) разницы.push(Math.abs(я(px, py) - я(px + 1, py)) + Math.abs(я(px, py) - я(px, py + 1)));
  разницы.sort((a, b) => a - b);
  return разницы[Math.floor(разницы.length / 2)];                 // медиана перепада между соседними точками: гладкая заливка даёт ноль, зерно краски — больше
}"""


def _зерно_стены(б):
    б.page.evaluate('MM.seek(.7)')
    ссылка = 'data:image/png;base64,' + base64.b64encode(б.page.screenshot(type='png')).decode()
    return б.page.evaluate(РАЗБРОС, ссылка)


def test_фактура_переводится_и_проверяется(tmp_path):
    assert _стиль(tmp_path, манера={'фактура': 'гуашь', 'сила_фактуры': .4})['manner'] == {'texture': 'gouache', 'textureAmt': .4}
    with pytest.raises(config.ОшибкаКонфига, match='гуашь'):
        _стиль(tmp_path, манера={'фактура': 'масло'})


@pytest.mark.browser
@pytest.mark.parametrize('фактура', ['гуашь', 'бумага'])
def test_фактура_делает_гладкую_стену_живой_краской(мини, в_пустой, фактура):  # noqa: F811
    """Гладкий градиент стены не имеет зерна (медиана перепада между соседними точками около нуля); гуашь и бумага дают его, и оно стоит на месте."""
    чистый = "rect(s, -20, -20, W + 40, H + 40, { fill: '#f3e6c4' }); hero(s, 'петя', CX, 900, 1.2, [[0, 'neutral']], 0, D);"   # светлый плоский фон: на тёмном умножение почти не видно
    with _Браузер(_без_зерна(мини, None, чистый)) as б:
        гладкая = _зерно_стены(б)
    with _Браузер(_без_зерна(мини, {'фактура': фактура}, чистый)) as б:
        живая, первый = _зерно_стены(б), б.кадр(.7)
        б.кадр(.2)
        assert б.кадр(.7) == первый, 'фактура должна быть одинаковой в каждом кадре'
    assert гладкая < .6 and живая > гладкая + 1, f'{фактура}: зерно {живая} против {гладкая}'


# ---------- вырезка и классика ----------

@pytest.mark.browser
def test_глаза_вырезки_стоят_вплотную_а_у_марионетки_с_зазором(мини, в_пустой):  # noqa: F811
    """Бумажные куклы в духе «Южного парка»: два белых овала касаются друг друга."""
    зазор = "() => { const r = [...document.querySelectorAll('[data-eye]')].map(e => e.getBoundingClientRect()); return r.length === 2 ? r[1].left - r[0].right : null; }"
    with _Браузер(_школа(мини, персонаж='вырезка')) as б:
        б.page.evaluate('MM.seek(.7)')
        assert б.page.evaluate(зазор) is not None and б.page.evaluate(зазор) <= 3, 'глаза вырезки должны касаться друг друга'
    with _Браузер(_школа(мини, персонаж='марионетка')) as б:
        б.page.evaluate('MM.seek(.7)')
        assert б.page.evaluate(зазор) is None or б.page.evaluate(зазор) > 3


@pytest.mark.browser
def test_классика_лепит_градиентами_и_красит_линию_цветом(мини, в_пустой):  # noqa: F811
    """Свет и тень градиентами, контур тёмным оттенком самой краски, а не чёрной тушью."""
    with _Браузер(_школа(мини, персонаж='классика')) as б:
        б.page.evaluate('MM.seek(.7)')
        р = б.page.evaluate("""() => { const э = [...document.querySelectorAll('[data-hero] *')];
          return { градиенты: э.filter(e => (e.getAttribute('fill') || '').startsWith('url(#')).length,
                   контуры: [...new Set(э.map(e => e.getAttribute('stroke')).filter(c => c && c !== 'none'))], тушь: INK }; }""")
    assert р['градиенты'] >= 3, р
    assert р['тушь'] not in р['контуры'], 'контур классики не чёрная тушь, а тёмный оттенок краски'


@pytest.mark.browser
def test_у_классики_в_каждом_глазу_два_блика(мини, в_пустой):  # noqa: F811
    with _Браузер(_школа(мини, персонаж='классика')) as б:
        б.page.evaluate('MM.seek(.7)')
        блики = б.page.evaluate("() => [...document.querySelectorAll('[data-eye]')].map(e => [...e.querySelectorAll('circle')].filter(c => c.getAttribute('fill') === '#ffffff' && +c.getAttribute('r') < 12).length)")
    assert блики == [2, 2], блики


@pytest.mark.browser
def test_классика_приседает_перед_реакцией_и_пружинит_после(мини, в_пустой):  # noqa: F811
    """Подготовка (присед перед скачком реакции) и инерция после неё: два главных приёма классической анимации."""
    сцена = "room(s, 'комната'); hero(s, 'петя', CX, 900, 1.2, [[0, 'neutral'], [.7, 'shock']], 0, D);"
    with _Браузер(_школа(мини, сцена, персонаж='классика')) as б:
        def sy(t):
            б.page.evaluate('t => MM.seek(t)', t)
            return б.page.evaluate(f"() => ({МАСШТАБ})(document.querySelector('[data-body]'))")[1] - 1
        покой, подготовка = sy(.15), sy(.64)
        после = [sy(.7 + i * .03) for i in range(15)]
    assert подготовка < покой - .02, f'перед реакцией тело должно присесть: {покой} → {подготовка}'
    assert _знаки(после, 1e-3) >= 2, f'после реакции тело должно пружинить: {после}'


@pytest.mark.browser
def test_обычному_герою_руки_включаются_ключом_и_играют_эмоцию(мини, в_пустой):  # noqa: F811
    """Руки обычного героя выключены по умолчанию (старые стили не меняются); `руки: да` даёт те же играющие руки, что у каракули."""
    def рисовать(**манера):
        _эпизод(мини, {'один': ЭМОЦИИ})
        ep = yaml.safe_load((мини / 'episode.yaml').read_text(encoding='utf-8'))
        ep.pop('анимации', None), ep.pop('манера', None)
        if манера:
            ep['манера'] = манера
        (мини / 'episode.yaml').write_text(yaml.safe_dump(ep, allow_unicode=True), encoding='utf-8')
        return build.собрать(мини, выход=config.ROOT / 'build' / 'тест-школа')
    with _Браузер(рисовать(руки=True)) as б:
        углы = {}
        for t in (.2, .8):
            б.page.evaluate('t => MM.seek(t)', t)
            углы[t] = б.page.evaluate(f"() => [...document.querySelectorAll('[data-arm]')].map({УГОЛ})")
    assert len(углы[.2]) == 2 and all(abs(углы[.8][i] - углы[.2][i]) > 40 for i in (0, 1)), углы
    with _Браузер(рисовать()) as б:
        assert б.page.evaluate("document.querySelectorAll('[data-arm]').length") == 0


@pytest.mark.browser
def test_у_классики_вырез_кожей_только_у_пиджака_а_у_толстовки_воротник_капюшона(мини, в_пустой):  # noqa: F811
    """Толстовка не открывает грудь до пупка: кожа в вырезе есть у пиджака, у толстовки — воротник капюшона."""
    сцена = "room(s, 'комната'); hero(s, 'петя', 250, 900, 1, [[0, 'neutral']], 0, D, { skin: '#f2c29b' }); hero(s, 'петя', 650, 900, 1, [[0, 'neutral']], 0, D, { skin: '#f2c29b', suit: '#1f2937', tie: '#b91c1c' });"
    with _Браузер(_школа(мини, сцена, персонаж='классика')) as б:
        б.page.evaluate('MM.seek(.7)')
        вырезы = б.page.evaluate("() => [...document.querySelectorAll('[data-hero]')].map(h => [...h.querySelectorAll('[data-body] path')].filter(e => e.getAttribute('fill') === '#f2c29b').length)")
    assert вырезы[0] == 0 and вырезы[1] >= 1, вырезы


# ---------- человечки на общем плане ----------

ЧЕЛОВЕЧЕК = "[...document.querySelectorAll('[data-hero] %s')]"


@pytest.mark.browser
def test_человечек_каракули_нарисован_линиями_без_плашек(мини, в_пустой):  # noqa: F811
    with _Браузер(_школа(мини, ХОДЬБА, персонаж='каракуля')) as б:
        б.page.evaluate('MM.seek(.4)')
        assert б.page.evaluate(f"{ЧЕЛОВЕЧЕК % 'rect'}.length") == 0
        assert б.page.evaluate(f"{ЧЕЛОВЕЧЕК % 'path[stroke-linecap=round]'}.length") >= 5


@pytest.mark.browser
def test_человечек_марионетки_качается_а_ноги_не_гнутся(мини, в_пустой):  # noqa: F811
    def ноги_и_тело(б, t):
        б.page.evaluate('t => MM.seek(t)', t)
        return б.page.evaluate("() => [[...document.querySelectorAll('[data-leg]')].map(e => e.getAttribute('transform')), document.querySelector('[data-body]').getAttribute('transform')]")

    with _Браузер(_школа(мини, ХОДЬБА, персонаж='марионетка')) as б:
        (ноги1, тело1), (ноги2, тело2) = ноги_и_тело(б, .3), ноги_и_тело(б, .4)
    assert len(ноги1) == 2 and ноги1 == ноги2, 'ноги бумажной куклы не сгибаются'
    assert тело1 != тело2, 'кукла должна раскачиваться при ходьбе'
    with _Браузер(_школа(мини, ХОДЬБА)) as б:
        (ноги1, _), (ноги2, _) = ноги_и_тело(б, .3), ноги_и_тело(б, .4)
    assert len(ноги1) == 2 and ноги1 != ноги2, 'у обычного человечка ноги шагают'


@pytest.mark.browser
def test_человечек_желе_пружинит_при_ходьбе(мини, в_пустой):  # noqa: F811
    with _Браузер(_школа(мини, ХОДЬБА, персонаж='желе')) as б:
        масштабы = []
        for i in range(12):
            б.page.evaluate('t => MM.seek(t)', .2 + i * .06)
            масштабы.append(б.page.evaluate(f"() => ({МАСШТАБ})(document.querySelector('[data-body]'))")[1])
        assert max(масштабы) - min(масштабы) >= .08


# ---------- проверка раскладки и справочник ----------

@pytest.mark.browser
@pytest.mark.parametrize('имя', ПЕРСОНАЖИ)
def test_проверка_раскладки_работает_с_любым_персонажем(мини, в_пустой, capsys, имя):  # noqa: F811
    сцена = "room(s, 'комната'); const k = closeUp(s, 'петя', [[0, 'neutral'], [.8, 'shock']], 0, D); word(s, 'КРУПНО', ...k.text, .3, { size: k.size, fill: MARK });"
    _школа(мини, сцена, персонаж=имя)
    код, вывод = _проверить(мини, capsys, строго=True)
    assert 'крупно' in вывод and код == 0, вывод


@pytest.mark.browser
@pytest.mark.parametrize('имя', ПЕРСОНАЖИ)
def test_герой_с_вычурным_обликом_остаётся_узнаваемым(мини, в_пустой, имя):  # noqa: F811
    """Доспех, длинные волосы, усы, коробка: любой облик из стиля рисуется, ничего не падает."""
    сцена = ("room(s, 'комната'); hero(s, 'петя', 250, 900, 1, [[0, 'rage']], 0, D, { armor: '#475569', cloak: '#1e3a8a', longHair: true, arms: true, tattoo: '#0b1220', eyeCol: '#38bdf8', build: 1.5 });"
             "hero(s, 'петя', 650, 900, 1, [[0, 'thinking'], [.6, 'epiphany']], 0, D, { mustache: 1, bald: true, suit: '#1f2937', tie: '#b91c1c', box: true });")
    with _Браузер(_школа(мини, сцена, персонаж=имя)) as б:
        for t in (.1, .8):
            б.page.evaluate('t => MM.seek(t)', t)
        assert б.page.evaluate("document.querySelectorAll('[data-hero]').length") == 2


@pytest.mark.parametrize('слово', ['персонаж', 'каракуля', 'марионетка', 'желе', 'силуэт', 'шланг', 'пиксель', 'пиксели', 'вырезка', 'классика', 'фактура', 'сила_фактуры', 'руки', 'характер', 'пружина', 'резкий', 'механика'])
def test_школа_описана_в_справочнике(слово):
    assert слово in (config.ROOT / 'docs' / 'styles.md').read_text(encoding='utf-8')


@pytest.mark.parametrize('файл', ['notebook', 'cutout', 'jelly', 'shadow', 'hose', 'pixel', 'classic', 'soyuz'])
def test_стиль_школы_задаёт_персонажа_и_характер(файл):
    с = config.стиль(файл)
    assert с['manner'].get('rig') and с['motion'].get('feel')

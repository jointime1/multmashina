"""Манера рисунка: толщина и дрожь линии, анимация рывками, тона, растр, глаза и пропорции. Старые стили при этом не меняются."""
import base64
import json

import pytest
import yaml

from mmlib import build, config, render
from test_motion import _Браузер
from test_variety import _проверить, _эпизод, в_пустой  # noqa: F401

ГЕРОЙ = "room(s, 'комната'); hero(s, 'петя', CX, 900, 1.5, [[0, 'neutral']], 0, D);"


def _манера(мини, сцена=ГЕРОЙ, **манера):
    _эпизод(мини, {'один': сцена})
    ep = yaml.safe_load((мини / 'episode.yaml').read_text(encoding='utf-8'))
    ep['манера'] = манера
    (мини / 'episode.yaml').write_text(yaml.safe_dump(ep, allow_unicode=True), encoding='utf-8')
    return build.собрать(мини, выход=config.ROOT / 'build' / 'тест-манера')


# ---------- конфиг ----------

def _стиль(tmp_path, манера):
    f = tmp_path / 'свой.yaml'
    f.write_text(yaml.safe_dump({'манера': манера}, allow_unicode=True), encoding='utf-8')
    return config.стиль(f)


def test_манера_переводится_из_стиля(tmp_path):
    с = _стиль(tmp_path, {'линия': 1.5, 'дрожь': 3, 'рывки': 12, 'тона': ['#000000', '#ffffff'], 'глаза': 'точки'})
    assert с['manner'] == {'line': 1.5, 'wobble': 3, 'step': 12, 'tones': ['#000000', '#ffffff'], 'eyes': 'dots'}


def test_опечатка_в_манере_называет_допустимые_ключи(tmp_path):
    with pytest.raises(config.ОшибкаКонфига, match='линия'):
        _стиль(tmp_path, {'линиия': 2})


def test_неизвестные_глаза_называют_допустимые(tmp_path):
    with pytest.raises(config.ОшибкаКонфига, match='точки'):
        _стиль(tmp_path, {'глаза': 'квадратные'})


@pytest.mark.parametrize('тона', [['#000000'], ['чёрный', '#ffffff'], '#000000'])
def test_тона_это_список_из_двух_и_больше_цветов(tmp_path, тона):
    with pytest.raises(config.ОшибкаКонфига, match='тона'):
        _стиль(tmp_path, {'тона': тона})


def test_эпизод_перекрывает_манеру_стиля_по_ключам(tmp_path):
    с = config.дополнить_стиль(_стиль(tmp_path, {'линия': 2, 'рывки': 12}), {'манера': {'рывки': 8}})
    assert с['manner'] == {'line': 2, 'step': 8}


# ---------- старые стили не меняются ----------

@pytest.mark.browser
def test_без_манеры_кадр_прежний(мини, в_пустой):  # noqa: F811
    _эпизод(мини, {'один': ГЕРОЙ})
    with _Браузер(build.собрать(мини, выход=config.ROOT / 'build' / 'тест-манера')) as б:
        assert б.page.evaluate("document.querySelectorAll('[filter]').length") == 0
        assert б.page.evaluate('MM.manifest().step') == 0
        assert б.page.evaluate("() => { MM.seek(.31); const a = document.querySelector('[data-hero] g').getAttribute('transform'); MM.seek(.32); return a !== document.querySelector('[data-hero] g').getAttribute('transform'); }")


# ---------- линия ----------

ТОЛЩИНЫ = "() => [...document.querySelectorAll('[data-hero] [stroke]')].filter(e => e.getAttribute('stroke') === INK).map(e => +e.getAttribute('stroke-width'))"


@pytest.mark.browser
@pytest.mark.parametrize('линия, ждём', [(2, 12), (.5, 3), (0, 0)])
def test_обводка_героя_следует_за_манерой(мини, в_пустой, линия, ждём):  # noqa: F811
    with _Браузер(_манера(мини, линия=линия)) as б:
        assert ждём in б.page.evaluate(ТОЛЩИНЫ)
        assert 6 not in б.page.evaluate(ТОЛЩИНЫ)


@pytest.mark.browser
def test_брови_не_становятся_толще_обводки(мини, в_пустой):  # noqa: F811
    """Брови и лямки нарисованы штрихом, но это форма, а не обводка."""
    with _Браузер(_манера(мини, линия=2)) as б:
        assert б.page.evaluate("() => [...document.querySelectorAll('[data-hero] path')].some(e => e.getAttribute('stroke-width') === '15')")


@pytest.mark.browser
def test_обводка_рук_человечка_следует_за_манерой(мини, в_пустой):  # noqa: F811
    """Рука — два штриха один на другом, без обводки тёмный штрих совпадает со светлым."""
    сцена = "room(s, 'комната'); figure(s, 'петя', CX, 1100, .6);"
    with _Браузер(_манера(мини, сцена, линия=0)) as б:
        штрихи = б.page.evaluate("() => [...document.querySelectorAll('[data-hero] path[stroke-linecap]')].map(e => +e.getAttribute('stroke-width'))")
        assert 40 in штрихи and 52 not in штрихи


# ---------- рывки ----------

СДВИГ = "room(s, 'комната'); const e = G(s, { x: 0, y: 500 }); e.setAttribute('id', 'цель'); rect(e, 0, 0, 80, 80, { fill: RED }); tw(e, { x: 800 }, 0, 1.4, lin);"
ГДЕ = "t => { MM.seek(t); return document.getElementById('цель').getAttribute('transform'); }"


@pytest.mark.browser
def test_рывки_держат_кадр_и_сдвигают_его_на_следующей_ступени(мини, в_пустой):  # noqa: F811
    with _Браузер(_манера(мини, СДВИГ, рывки=8)) as б:
        assert б.page.evaluate('MM.manifest().step') == 8
        assert б.page.evaluate(ГДЕ, .26) == б.page.evaluate(ГДЕ, .36)
        assert б.page.evaluate(ГДЕ, .36) != б.page.evaluate(ГДЕ, .38)


@pytest.mark.parametrize('a, b, fps, шаг, снимков', [(0, 30, 30, 12, 12), (0, 30, 30, 8, 8), (0, 30, 30, 0, 30), (7, 37, 30, 12, 13)])
def test_повторы_кадров_не_снимаются(a, b, fps, шаг, снимков):
    план = render.план_съёмки(a, b, fps, шаг)
    assert len(план) == b - a and план[0][1] is True
    assert sum(1 for _, снимать in план if снимать) == снимков


@pytest.mark.browser
def test_кадры_плана_совпадают_с_кадрами_движка(мини, в_пустой):  # noqa: F811
    """Кадр, который рендер считает повтором, в движке действительно тот же: иначе ролик поедет."""
    with _Браузер(_манера(мини, СДВИГ, рывки=12)) as б:
        for i, снимать in render.план_съёмки(0, 30, 30, 12):
            if not снимать:
                assert б.page.evaluate(ГДЕ, i / 30) == б.page.evaluate(ГДЕ, (i - 1) / 30), i


# ---------- дрожь и тона ----------

ЗЕРНО = "t => { MM.seek(t); return document.querySelector('#mm-manner feTurbulence').getAttribute('seed'); }"


@pytest.mark.browser
def test_дрожь_меняется_по_кругу_из_четырёх_рисунков(мини, в_пустой):  # noqa: F811
    with _Браузер(_манера(мини, дрожь=3, смена_дрожи=8)) as б:
        assert б.page.evaluate(ЗЕРНО, .05) == б.page.evaluate(ЗЕРНО, .1)
        assert б.page.evaluate(ЗЕРНО, .05) != б.page.evaluate(ЗЕРНО, .2)
        assert б.page.evaluate(ЗЕРНО, .05) == б.page.evaluate(ЗЕРНО, .55)


@pytest.mark.browser
def test_субтитры_лежат_вне_фильтра_а_камера_под_ним(мини, в_пустой):  # noqa: F811
    """Текст субтитров остаётся чётким, а шум не едет вместе с камерой."""
    сцена = ГЕРОЙ + "caps(s, 'один');"
    with _Браузер(_манера(мини, сцена, дрожь=3)) as б:
        б.page.evaluate('MM.seek(.5)')
        рисунок = б.page.evaluate("() => { const b = BEAT_LIST[0]; return [b.world.parentNode.getAttribute('filter'), b.world.getAttribute('filter'), b.fixed.parentNode.getAttribute('filter')]; }")
        assert рисунок == ['url(#mm-manner)', None, None]


def _снимок(б, t):
    б.page.evaluate('t => MM.seek(t)', t)
    return б.page.screenshot(type='png')


РАЗОБРАТЬ = """async ссылка => {
  const картинка = new Image(); картинка.src = ссылка; await картинка.decode();
  const c = document.createElement('canvas'); c.width = картинка.width; c.height = картинка.height;
  const x = c.getContext('2d'); x.drawImage(картинка, 0, 0);
  return [...x.getImageData(0, 0, c.width, c.height).data];
}"""


def _пиксели(б, t):
    """Точки кадра как список (r, g, b): Pillow проекту не нужен, поэтому снимок разбирает сам браузер."""
    ссылка = 'data:image/png;base64,' + base64.b64encode(_снимок(б, t)).decode()
    д = б.page.evaluate(РАЗОБРАТЬ, ссылка)
    return [(д[i], д[i + 1], д[i + 2]) for i in range(0, len(д), 4 * 37)]


@pytest.mark.browser
def test_кадр_с_дрожью_повторяется_точно(мини, в_пустой):  # noqa: F811
    with _Браузер(_манера(мини, дрожь=3)) as б:
        первый = _снимок(б, .7)
        _снимок(б, .2)
        assert _снимок(б, .7) == первый


@pytest.mark.browser
def test_тона_оставляют_в_кадре_только_заданные_цвета(мини, в_пустой):  # noqa: F811
    тона = [(16, 16, 24), (214, 40, 40), (244, 236, 216)]
    with _Браузер(_манера(мини, ГЕРОЙ, тона=['#%02x%02x%02x' % c for c in тона])) as б:
        точки = _пиксели(б, .7)
        рядом = sum(1 for p in точки if min(max(abs(a - b) for a, b in zip(p, c)) for c in тона) <= 6)
        assert рядом / len(точки) > .97
        видно = {min(range(3), key=lambda i: max(abs(a - b) for a, b in zip(p, тона[i]))) for p in точки}
        assert len(видно) == 3


@pytest.mark.browser
def test_растр_даёт_точки_на_однотонной_заливке(мини, в_пустой):  # noqa: F811
    сцена = "rect(s, -20, -20, W + 40, H + 40, { fill: '#808080' });"
    with _Браузер(_манера(мини, сцена, тона=['#000000', '#ffffff'], растр=16)) as б:
        точки = _пиксели(б, .7)
        чёрных, белых = sum(1 for p in точки if p[0] < 40), sum(1 for p in точки if p[0] > 216)
        assert чёрных > .2 * len(точки) and белых > .2 * len(точки)


# ---------- глаза и пропорции ----------

@pytest.mark.browser
def test_глаза_точки_без_белков(мини, в_пустой):  # noqa: F811
    with _Браузер(_манера(мини, глаза='точки')) as б:
        assert б.page.evaluate("() => [...document.querySelectorAll('[data-hero] ellipse')].every(e => e.getAttribute('fill') !== '#fff')")


@pytest.mark.browser
def test_пропорции_меняют_голову_и_тело(мини, в_пустой):  # noqa: F811
    размеры = "() => { MM.seek(.7); const r = document.querySelector('[data-head]'), b = document.querySelector('[data-body]'); return [r.getBoundingClientRect().width, r.getBoundingClientRect().height, b.getBoundingClientRect().width]; }"
    with _Браузер(_манера(мини, )) as б:
        ш0, в0, т0 = б.page.evaluate(размеры)
    with _Браузер(_манера(мини, ширина_головы=.8, высота_головы=1.2, тело=.7)) as б:
        ш, в, т = б.page.evaluate(размеры)
    assert ш < ш0 * .85 and в > в0 * 1.1 and т < т0 * .8


@pytest.mark.browser
def test_длинная_шея_опускает_тело(мини, в_пустой):  # noqa: F811
    верх = "() => { MM.seek(.7); return document.querySelector('[data-body]').getBoundingClientRect().top; }"
    with _Браузер(_манера(мини, )) as б:
        обычная = б.page.evaluate(верх)
    with _Браузер(_манера(мини, шея=1.5)) as б:
        assert б.page.evaluate(верх) > обычная + 10


@pytest.mark.browser
def test_голова_человечка_следует_за_манерой(мини, в_пустой):  # noqa: F811
    сцена = "room(s, 'комната'); figure(s, 'петя', CX, 1100, .6);"
    with _Браузер(_манера(мини, сцена, ширина_головы=.8, высота_головы=1.2)) as б:
        assert 'scale(0.8' in б.page.evaluate("document.querySelector('[data-head]').getAttribute('transform')")


# ---------- бумага и плоский цвет ----------

def test_неизвестная_бумага_называет_допустимые(tmp_path):
    with pytest.raises(config.ОшибкаКонфига, match='клетка'):
        _стиль(tmp_path, {'бумага': 'картон'})


def test_низ_пола_задаётся_стилем():
    assert config.КОМНАТА['низ_пола'] == 'floor2' and config.СТИЛЬ['офис'][1]['низ_пола'] == 'floor2'


@pytest.mark.browser
def test_пол_комнаты_темнеет_к_цвету_из_стиля(мини, в_пустой):  # noqa: F811
    _эпизод(мини, {'один': "room(s, 'комната', { floor2: '#abcdef' });"})
    with _Браузер(build.собрать(мини, выход=config.ROOT / 'build' / 'тест-манера')) as б:
        assert б.page.evaluate("[...document.querySelectorAll('stop')].some(e => e.getAttribute('stop-color') === '#abcdef')")


@pytest.mark.browser
def test_плоский_цвет_убирает_градиенты_у_декораций(мини, в_пустой):  # noqa: F811
    with _Браузер(_манера(мини, "room(s, 'комната'); office(s);", плоско=True)) as б:
        assert б.page.evaluate("document.querySelectorAll('[fill^=\"url(#mmlg\"]').length") == 0
        assert б.page.evaluate("document.querySelectorAll('[fill^=\"url(#mmrg\"]').length") == 0


@pytest.mark.browser
@pytest.mark.parametrize('бумага', ['клетка', 'линейка'])
def test_бумага_лежит_поверх_рисунка_и_стоит_на_месте(мини, в_пустой, бумага):  # noqa: F811
    with _Браузер(_манера(мини, бумага=бумага)) as б:
        assert б.page.evaluate("() => { const b = BEAT_LIST[0], last = b.world.parentNode.lastElementChild; return last !== b.world && last.getAttribute('fill') === 'url(#mm-paper)'; }")


@pytest.mark.browser
def test_шторки_сверхкрупного_плана_берут_цвет_фона(мини, в_пустой):  # noqa: F811
    """В светлой манере чёрная шторка съедает тёмную надпись: у шторки цвет фона кадра."""
    with _Браузер(_манера(мини, "eyes(s, 'петя', [[0, 'neutral']], 0, D);")) as б:
        assert б.page.evaluate("[...document.querySelectorAll('[data-plan] rect')].some(e => e.getAttribute('fill') === DARK)")


МЕСТА = {'street': 'улица', 'kitchen': 'кухня', 'metro': 'метро', 'meeting': 'переговорка', 'stairs': 'лестница'}


@pytest.mark.browser
@pytest.mark.parametrize('функция, имя', МЕСТА.items(), ids=МЕСТА)
def test_готовая_локация_считается_своим_фоном(мини, в_пустой, capsys, функция, имя):  # noqa: F811
    _эпизод(мини, {'один': f"{функция}(s); hero(s, 'петя', CX, 900, 1.2, [[0, 'neutral'], [.6, 'shock']], 0, D);"})
    _, вывод = _проверить(мини, capsys)
    assert f'Фоны: {имя} 100%' in вывод and 'Ошибка' not in вывод, вывод


@pytest.mark.browser
@pytest.mark.parametrize('функция', МЕСТА)
def test_локация_закрывает_весь_кадр(мини, в_пустой, функция):  # noqa: F811
    сцена = f"rect(s, -20, -20, W + 40, H + 40, {{ fill: '#ff00ff' }}); {функция}(s);"
    _эпизод(мини, {'один': сцена})
    with _Браузер(build.собрать(мини, выход=config.ROOT / 'build' / 'тест-манера')) as б:
        assert not [p for p in _пиксели(б, .5) if p == (255, 0, 255)]


@pytest.mark.browser
def test_полоса_панелей_цвета_обводки_субтитров(мини, в_пустой):  # noqa: F811
    with _Браузер(_манера(мини, "panels(s, 2);")) as б:
        assert б.page.evaluate("[...document.querySelectorAll('rect')].some(e => e.getAttribute('fill') === CAP.stroke)")


# ---------- чужие цвета в светлой манере ----------

def test_комнаты_эпизода_берут_цвета_стиля_когда_он_просит(tmp_path):
    """Серия с тёмными комнатами в светлой манере превращается в сплошную заливку: цвета берутся у стиля, раскладка остаётся своя."""
    с = _стиль(tmp_path, {'комнаты_стиля': True})
    с['rooms']['комната'] = {'wall': '#111111', 'wall2': '#222222', 'floor': '#333333', 'lampX': 760}
    ep = {'комнаты': {'лестница': {'стена': '#abcdef', 'низ_стены': '#abcdef', 'пол': '#abcdef', 'лампа_x': 100}}}
    assert config.дополнить_стиль(с, ep)['rooms']['лестница'] == {'wall': '#111111', 'wall2': '#222222', 'floor': '#333333', 'lampX': 100}


def test_обычный_стиль_оставляет_комнаты_эпизода_как_есть():
    с = config.дополнить_стиль(config.стиль('dark-yard'), {'комнаты': {'лестница': {'стена': '#abcdef'}}})
    assert с['rooms']['лестница']['wall'] == '#abcdef'


@pytest.mark.browser
def test_вывеска_под_тонами_без_свечения(мини, в_пустой):  # noqa: F811
    """Свечение после порога тонов превращается в кляксу и съедает буквы."""
    сцена = "office(s, { name: 'Контора' });"
    свет = "[...document.querySelectorAll('text')].filter(e => e.style.filter).length"
    with _Браузер(_манера(мини, сцена, тона=['#000000', '#ffffff'])) as б:
        assert б.page.evaluate(свет) == 0
    with _Браузер(_манера(мини, сцена)) as б:
        assert б.page.evaluate(свет) == 1


@pytest.mark.browser
def test_экран_чата_цвета_фона(мини, в_пустой):  # noqa: F811
    with _Браузер(_манера(мини, "chat(s, 'Чат', [[0, 'Привет', .2]]);")) as б:
        assert б.page.evaluate("[...document.querySelectorAll('[data-decor]')].some(e => e.getAttribute('fill') === DARK)")


# ---------- справочник и готовые стили ----------

@pytest.mark.parametrize('файл', sorted(p.stem for p in (config.ROOT / 'styles').glob('*.yaml')))
def test_готовый_стиль_читается_и_описан_в_справочнике(файл):
    assert config.стиль(файл)['name']
    assert f'`{файл}`' in (config.ROOT / 'docs' / 'styles.md').read_text(encoding='utf-8')


@pytest.mark.parametrize('ключ', config.СТИЛЬ['манера'][1])
def test_ключ_манеры_описан_в_справочнике(ключ):
    assert f'`{ключ}`' in (config.ROOT / 'docs' / 'styles.md').read_text(encoding='utf-8')


@pytest.mark.parametrize('функция', МЕСТА)
def test_локация_описана_в_справочнике(функция):
    assert f'`{функция}(g)`' in (config.ROOT / 'docs' / 'scenes.md').read_text(encoding='utf-8')


def test_красный_плаката_попадает_в_красный_тон():
    """При трёх тонах порог идёт по яркости: настоящий красный темнее трети и уходит в чёрное, штампы пропадают на тёмном."""
    с = config.стиль('poster')
    яркость = lambda c: sum(k * int(c[i:i + 2], 16) / 255 for k, i in zip((.2126, .7152, .0722), (1, 3, 5)))
    for цвет in ('red', 'accent', 'sea'):
        assert 1 / 3 < яркость(с['palette'][цвет]) < 2 / 3, цвет


@pytest.mark.browser
def test_при_рывках_субтитры_не_накладываются(мини, в_пустой):  # noqa: F811
    """Обычно старый субтитр гаснет за две сотых секунды. При рывках такой кадр держится всю ступень, и две надписи видны поверх друг друга."""
    _манера(мини, рывки=8)                                            # субтитры добавляет оболочка бита
    слова = [[.1, 'Привет'], [.2, 'новый'], [.3, 'мир'], [.74, 'как'], [.8, 'твои'], [.9, 'дела']]
    (мини / 'audio' / 'timings.json').write_text(json.dumps({'один': {'dur': 1.5, 'marks': {'a': .1}, 'words': слова}}, ensure_ascii=False), encoding='utf-8')
    with _Браузер(build.собрать(мини, выход=config.ROOT / 'build' / 'тест-манера')) as б:
        видно = "t => { MM.seek(t); return [...BEAT_LIST[0].fixed.children].filter(e => parseFloat(e.getAttribute('opacity') ?? 1) > .01).length; }"
        groups = б.page.evaluate('BEAT_LIST[0].fixed.children.length')
        assert groups == 2
        assert max(б.page.evaluate(видно, i / 64) for i in range(100)) <= 1

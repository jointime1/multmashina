"""Школы анимации: из чего собран персонаж и как он двигается. Фильтр и цвет рисунка (манера) тут не при чём: проверяем устройство кадра и движение."""
import pytest
import yaml

from mmlib import build, config
from test_motion import _Браузер
from test_variety import _проверить, _эпизод, в_пустой  # noqa: F401

ЭМОЦИИ = "room(s, 'комната'); hero(s, 'петя', CX, 900, 1.2, [[0, 'neutral'], [.5, 'shock'], [1.1, 'rage']], 0, D);"
ПОКОЙ = "room(s, 'комната'); hero(s, 'петя', CX, 900, 1.2, [[0, 'neutral']], 0, D);"
ХОДЬБА = "room(s, 'комната'); figure(s, 'петя', 200, 1100, .6, { to: 700, t0: 0, t1: D });"
ПЕРСОНАЖИ = {'каракуля': 'doodle', 'марионетка': 'puppet', 'желе': 'jelly'}


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
    with _Браузер(_школа(мини, персонаж='марионетка')) as б:
        формы, позы = _формы_и_позы(б, моменты)
    assert формы[0] == формы[1] == формы[2], 'у марионетки сменилась форма детали'
    assert позы[0] != позы[1] and позы[1] != позы[2], 'марионетка не двигается'
    with _Браузер(_школа(мини)) as б:
        формы, _ = _формы_и_позы(б, моменты)
    assert формы[0] != формы[1], 'контрольный героя без персонажа должен гнуть лицо'


@pytest.mark.browser
def test_рот_марионетки_всегда_одна_готовая_деталь_без_плавных_переходов(мини, в_пустой):  # noqa: F811
    with _Браузер(_школа(мини, персонаж='марионетка')) as б:
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
def test_каракуля_играет_эмоцию_руками_а_у_обычного_героя_рук_нет(мини, в_пустой):  # noqa: F811
    углы = {}
    with _Браузер(_школа(мини, персонаж='каракуля')) as б:
        for t in (.2, .8):
            б.page.evaluate('t => MM.seek(t)', t)
            углы[t] = б.page.evaluate(f"() => [...document.querySelectorAll('[data-arm]')].map({УГОЛ})")
    assert len(углы[.2]) == 2 and len(углы[.8]) == 2
    assert all(abs(углы[.8][i] - углы[.2][i]) > 40 for i in (0, 1)), f'руки не отреагировали на шок: {углы}'
    assert углы[.8][0] * углы[.8][1] < 0, 'руки вскидываются в разные стороны от тела'
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


@pytest.mark.parametrize('слово', ['персонаж', 'каракуля', 'марионетка', 'желе', 'характер', 'пружина', 'резкий', 'механика'])
def test_школа_описана_в_справочнике(слово):
    assert слово in (config.ROOT / 'docs' / 'styles.md').read_text(encoding='utf-8')


@pytest.mark.parametrize('файл', ['notebook', 'cutout', 'jelly'])
def test_стиль_школы_задаёт_персонажа_и_характер(файл):
    с = config.стиль(файл)
    assert с['manner'].get('rig') and с['motion'].get('feel')

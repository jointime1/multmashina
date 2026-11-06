"""Готовые планы: каждый даёт свой кадр, а надпись по подсказке плана лежит в безопасной зоне. Все тесты браузерные."""
import pytest

from mmlib import build, config
from test_motion import _Браузер
from test_variety import _проверить, _эпизод, в_пустой  # noqa: F401

ЛИЦО = "[[0, 'neutral'], [.6, 'shock']]"

ПЛАНЫ = {
    'closeUp': (f"const k = closeUp(s, 'петя', {ЛИЦО}, 0, D);", 'крупно, по центру 100%'),
    'eyes': (f"const k = eyes(s, 'петя', {ЛИЦО}, 0, D);", 'сверхкрупно 100%'),
    'medium-слева': (f"const k = medium(s, 'петя', {ЛИЦО}, 0, D);", 'средний, слева 100%'),
    'medium-справа': (f"const k = medium(s, 'петя', {ЛИЦО}, 0, D, {{ side: 'right' }});", 'средний, справа 100%'),
    'wide': ("const k = wide(s, 'петя');", 'общий, по центру 100%'),
    'faceOff': (f"const k = faceOff(s, 'петя', {ЛИЦО}, 'петя', {ЛИЦО}, 0, D);", 'лицом к лицу 100%'),
    'overShoulder': (f"const k = overShoulder(s, 'петя', 'петя', {ЛИЦО}, 0, D);", 'через плечо 100%'),
    'topView': ("const k = topView(s, ['петя', 'петя', 'петя']);", 'сверху 100%'),
    'chat': ("const k = chat(s, 'Чат', [[0, 'Привет', .2], [1, 'Пока', .8]]);", 'экран 100%'),
    'item': ("const k = item(s, c => ico(c, 'gavel', 0, 0, 420, LIGHT));", 'предмет 100%'),
}


@pytest.mark.browser
@pytest.mark.parametrize('сцена, ожидается', ПЛАНЫ.values(), ids=ПЛАНЫ)
def test_план_даёт_свой_кадр_и_место_под_надпись(мини, в_пустой, capsys, сцена, ожидается):  # noqa: F811
    _эпизод(мини, {'один': сцена + "word(s, 'СЛОВО', ...k.text, .3, { size: k.size, fill: LIGHT });"})
    _, вывод = _проверить(мини, capsys)
    assert ожидается in вывод and 'безопасную зону' not in вывод and 'Ошибка' not in вывод, вывод


@pytest.mark.browser
def test_панели_комикса_берут_обычные_координаты_кадра(мини, в_пустой, capsys):  # noqa: F811
    сцена = f"""const [a, b] = panels(s, 2);
        room(a, 'комната'); hero(a, 'петя', CX, 850, 1, {ЛИЦО}, 0, D);
        room(b, 'подвал'); hero(b, 'петя', CX, 850, 1, {ЛИЦО}, 0, D);"""
    _эпизод(мини, {'один': сцена})
    _, вывод = _проверить(мини, capsys)
    assert 'комикс 100%' in вывод and 'Ошибка' not in вывод, вывод


@pytest.mark.browser
@pytest.mark.parametrize('рядов', [2, 3])
def test_панели_не_заходят_на_субтитры(мини, в_пустой, рядов):  # noqa: F811
    """Субтитры лежат на y≈1200: лица в панелях не должны оказаться под ними."""
    имена = ', '.join(f'p{i}' for i in range(рядов))
    _эпизод(мини, {'один': f"const [{имена}] = panels(s, {рядов});"})
    with _Браузер(build.собрать(мини, выход=config.ROOT / 'build' / f'тест-панели-{рядов}')) as б:
        б.page.evaluate('MM.seek(.3)')
        assert б.page.evaluate("() => [...document.querySelectorAll('clipPath rect')].every(r => +r.getAttribute('y') + +r.getAttribute('height') <= 1160)")


@pytest.mark.browser
def test_панель_появляется_в_свой_момент(мини, в_пустой):  # noqa: F811
    _эпизод(мини, {'один': "const [a, b] = panels(s, 2, { at: [0, .8] }); room(a, 'комната'); room(b, 'подвал');"})
    with _Браузер(build.собрать(мини, выход=config.ROOT / 'build' / 'тест-панели')) as б:
        видна = "i => { const e = document.querySelectorAll('[data-panel]')[i]; return parseFloat(e.getAttribute('opacity') ?? 1); }"
        б.page.evaluate('MM.seek(.3)')
        assert б.page.evaluate(видна, 0) == 1 and б.page.evaluate(видна, 1) == 0
        б.page.evaluate('MM.seek(1.2)')
        assert б.page.evaluate(видна, 1) == 1


@pytest.mark.browser
def test_человечек_идёт_через_кадр(мини, в_пустой, capsys):  # noqa: F811
    _эпизод(мини, {'один': "wide(s, 'петя', { x: 150, to: 750, t0: .1, t1: 4.8 });"}, длит=5)
    _, вывод = _проверить(мини, capsys)
    assert 'общий, слева' in вывод and 'общий, справа' in вывод and 'ничего не меняется' not in вывод, вывод


@pytest.mark.browser
def test_сообщения_чата_приходят_по_очереди(мини, в_пустой):  # noqa: F811
    _эпизод(мини, {'один': "chat(s, 'Чат', [[0, 'Первое', .2], [1, 'Второе', 1]]);"})
    with _Браузер(build.собрать(мини, выход=config.ROOT / 'build' / 'тест-чат')) as б:
        есть = """слово => [...document.querySelectorAll('#mm-svg text')].some(e => {
            if (e.textContent !== слово) return false;
            for (let n = e; n && n.id !== 'mm-svg'; n = n.parentNode) if (n.getAttribute && parseFloat(n.getAttribute('opacity') ?? 1) < .5) return false;
            return true; })"""
        б.page.evaluate('MM.seek(.6)')
        assert б.page.evaluate(есть, 'Первое') and not б.page.evaluate(есть, 'Второе')
        б.page.evaluate('MM.seek(1.4)')
        assert б.page.evaluate(есть, 'Второе')


@pytest.mark.browser
def test_длинное_сообщение_переносится_внутри_зоны(мини, в_пустой, capsys):  # noqa: F811
    длинное = 'очень длинное сообщение ' * 8
    _эпизод(мини, {'один': f"chat(s, 'Чат', [[0, '{длинное}', .2], [1, '{длинное}', .4]]);"})
    _, вывод = _проверить(мини, capsys)
    assert 'безопасную зону' not in вывод, вывод


@pytest.mark.browser
def test_переполненный_чат_уезжает_вверх(мини, в_пустой, capsys):  # noqa: F811
    сообщения = ', '.join(f"[{i % 2}, 'Сообщение номер {i}', {.1 + i * .1:.1f}]" for i in range(14))
    _эпизод(мини, {'один': f"chat(s, 'Чат', [{сообщения}]);"}, длит=3)
    _, вывод = _проверить(мини, capsys)
    assert 'безопасную зону' not in вывод, вывод


@pytest.mark.browser
def test_головы_сверху_можно_двигать(мини, в_пустой, capsys):  # noqa: F811
    _эпизод(мини, {'один': "const v = topView(s, ['петя', 'петя']); tw(v.heads[0], { x: 100 }, .2, .6);"})
    _, вывод = _проверить(мини, capsys)
    assert 'сверху 100%' in вывод and 'Ошибка' not in вывод, вывод


@pytest.mark.browser
def test_реакция_в_кружке_не_меняет_план(мини, в_пустой, capsys):  # noqa: F811
    _эпизод(мини, {'один': f"chat(s, 'Чат', [[0, 'Привет', .2]]); inset(s, 'петя', {ЛИЦО}, 0, D);"})
    _, вывод = _проверить(мини, capsys)
    assert 'экран 100%' in вывод and 'Ошибка' not in вывод, вывод


@pytest.mark.browser
def test_кадр_плана_не_зависит_от_времени_снятия(мини, в_пустой):  # noqa: F811
    """Покадровый рендер идёт в любом порядке: человечек и панели — чистые функции от времени."""
    _эпизод(мини, {'один': "wide(s, 'петя', { x: 150, to: 750, t0: .1, t1: 1.4, run: true });"})
    with _Браузер(build.собрать(мини, выход=config.ROOT / 'build' / 'тест-детерминизм')) as б:
        снимок = "() => document.querySelector('[data-hero]').outerHTML"
        б.page.evaluate('MM.seek(.9)')
        первый = б.page.evaluate(снимок)
        б.page.evaluate('MM.seek(.2)')
        б.page.evaluate('MM.seek(.9)')
        assert б.page.evaluate(снимок) == первый


@pytest.mark.browser
def test_человечек_сохраняет_комплекцию_героя(мини, в_пустой):  # noqa: F811
    """Качок остаётся качком и на общем плане, иначе героя не узнать."""
    (мини / 'episode.yaml').write_text('название: Т\nстиль: dark-yard\nскрипты: [scenes.js]\nгерои:\n  петя: {очки: true}\n  качок: {комплекция: 1.5}\n', encoding='utf-8')
    _эпизод(мини, {'один': "wide(s, 'петя', { x: 200 }); wide(s, 'качок', { x: 650 });"})
    with _Браузер(build.собрать(мини, выход=config.ROOT / 'build' / 'тест-качок')) as б:
        ширины = б.page.evaluate("() => [...document.querySelectorAll('[data-hero] rect')].map(r => +r.getAttribute('width')).filter(w => w > 100)")
        assert len(ширины) == 2 and ширины[1] == pytest.approx(ширины[0] * 1.5), ширины

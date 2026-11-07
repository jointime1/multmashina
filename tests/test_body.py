"""Тело героя: жесты рук по имени, ноги и стойка во весь рост, качание головы на слогах."""
import pytest
import yaml

from mmlib import build, config
from test_motion import _Браузер
from test_variety import _эпизод, в_пустой  # noqa: F401

УГОЛ = "e => { const m = /rotate\\((-?[\\d.]+)/.exec(e.getAttribute('transform') || ''); return m ? +m[1] : 0; }"


def _герой(мини, ключи, персонаж, сцена_до=''):
    """Эпизод с одним героем, его ключи эмоций и жестов, нужный персонаж."""
    _эпизод(мини, {'один': f"room(s, 'комната'); hero(s, 'петя', CX, 900, 1.2, {ключи}, 0, D);"})
    ep = yaml.safe_load((мини / 'episode.yaml').read_text(encoding='utf-8'))
    ep.pop('анимации', None)
    ep['манера'] = {'персонаж': персонаж}
    (мини / 'episode.yaml').write_text(yaml.safe_dump(ep, allow_unicode=True), encoding='utf-8')
    return build.собрать(мини, выход=config.ROOT / 'build' / 'тест-тело')


def _углы(б, t):
    б.page.evaluate('t => MM.seek(t)', t)
    return б.page.evaluate(f"() => [...document.querySelectorAll('[data-arm]')].map({УГОЛ})")


# ---------- жесты: у кого руки вращаются вокруг плеча ----------
ВРАЩАЮЩИЕ = ['каракуля', 'силуэт', 'шланг', 'вырезка', 'классика']


@pytest.mark.browser
@pytest.mark.parametrize('персонаж', ВРАЩАЮЩИЕ)
def test_жест_point_поднимает_только_правую_руку(мини, в_пустой, персонаж):  # noqa: F811
    with _Браузер(_герой(мини, "[[0, 'neutral'], [.4, 'neutral', { gest: 'point' }]]", персонаж)) as б:
        до, после = _углы(б, .1), _углы(б, .9)
    assert abs(после[1]) > 80 and abs(до[1]) < 30, f'правая рука должна подняться: {до} → {после}'
    assert abs(после[0]) < 30, f'левая остаётся внизу: {после}'


@pytest.mark.browser
@pytest.mark.parametrize('персонаж', ВРАЩАЮЩИЕ)
def test_жест_wave_машет_рукой(мини, в_пустой, персонаж):  # noqa: F811
    with _Браузер(_герой(мини, "[[0, 'neutral'], [.3, 'neutral', { gest: 'wave' }]]", персонаж)) as б:
        ряд = [_углы(б, .8 + i * .05)[1] for i in range(8)]
    assert min(map(abs, ряд)) > 90, f'рука поднята: {ряд}'
    assert max(ряд) - min(ряд) > 12, f'рука машет, а не стоит: {ряд}'


@pytest.mark.browser
@pytest.mark.parametrize('жест, ожидание', [
    ('shrug', lambda л, п: 30 < л < 70 and -70 < п < -30),                  # обе руки в стороны ладонями вверх
    ('facepalm', lambda л, п: abs(л) < 30 and п > 90),                      # правая к лицу
    ('handsup', lambda л, п: л > 120 and п < -120),                         # обе вверх
])
def test_жесты_по_имени_ставят_руки(мини, в_пустой, жест, ожидание):  # noqa: F811
    with _Браузер(_герой(мини, f"[[0, 'neutral'], [.3, 'neutral', {{ gest: '{жест}' }}]]", 'классика')) as б:
        л, п = _углы(б, .9)
    assert ожидание(л, п), f'{жест}: левая {л}, правая {п}'


@pytest.mark.browser
def test_жест_плавно_приходит_и_снимается_следующим_ключом(мини, в_пустой):  # noqa: F811
    with _Браузер(_герой(мини, "[[0, 'neutral'], [.5, 'neutral', { gest: 'point' }], [1.3, 'neutral']]", 'классика')) as б:
        до, на_пути, держит, потом = _углы(б, .1)[1], _углы(б, .42)[1], _углы(б, .9)[1], _углы(б, 1.8)[1]
    assert abs(до) < 30 and abs(держит) > 80 and abs(потом) < 30, (до, держит, потом)
    assert abs(до) < abs(на_пути) < abs(держит), f'жест должен приходить плавно: {до} → {на_пути} → {держит}'


@pytest.mark.parametrize('слово', ['gest', 'point', 'wave', 'shrug', 'facepalm', 'handsup', 'hips', 'cross'])
def test_жесты_описаны_в_справочнике(слово):
    assert слово in (config.ROOT / 'docs' / 'scenes.md').read_text(encoding='utf-8')

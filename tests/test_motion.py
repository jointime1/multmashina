"""Вариативность анимаций: входы элементов, переходы между сценами, камера, реакция героев. Выключено по умолчанию, включается разделом «анимации» стиля."""
import json
import subprocess

import pytest

from mmlib import build, config, serve

playwright = pytest.importorskip('playwright.sync_api')


# ---------- конфиг (без браузера) ----------

def test_анимации_переводятся_с_русского(tmp_path):
    (tmp_path / 's.yaml').write_text('анимации:\n  входы: [падение, слева]\n  переходы: [рывок, вспышка]\n  камера: [наезд, стоп]\n  реакция: 0.07\n', encoding='utf-8')
    m = config.стиль(str(tmp_path / 's.yaml'))['motion']
    assert m == {'enters': ['drop', 'left'], 'trans': ['whip', 'flash'], 'cam': ['in', 'none'], 'punch': 0.07}


def test_опечатка_в_анимациях_называет_допустимое(tmp_path):
    (tmp_path / 's.yaml').write_text('анимации:\n  входы: [падение, взлёт]\n', encoding='utf-8')
    with pytest.raises(config.ОшибкаКонфига, match='взлёт.*Допустимые.*падение'):
        config.стиль(str(tmp_path / 's.yaml'))
    (tmp_path / 's2.yaml').write_text('анимации:\n  входы: падение\n', encoding='utf-8')
    with pytest.raises(config.ОшибкаКонфига, match='список'):
        config.стиль(str(tmp_path / 's2.yaml'))
    (tmp_path / 's3.yaml').write_text('анимации:\n  вход: [падение]\n', encoding='utf-8')
    with pytest.raises(config.ОшибкаКонфига, match='неизвестный ключ'):
        config.стиль(str(tmp_path / 's3.yaml'))


def test_эпизод_или_серия_перекрывают_анимации_и_паузу(мини):
    ep, _ = config.эпизод(мини)
    ep['анимации'] = {'камера': ['наезд'], 'реакция': 0}
    ep['эффекты'] = {'пауза_после_бита': 0.2}
    стиль = config.дополнить_стиль(config.стиль('dark-yard'), ep)
    assert стиль['motion']['cam'] == ['in'] and стиль['motion']['punch'] == 0
    assert стиль['motion']['enters'], 'остальное из стиля сохраняется'
    assert стиль['effects']['hold'] == 0.2


# ---------- браузер ----------

СЦЕНЫ = """'use strict';
const BEATS = [
  ['один', 'Один', (m, D) => {
    const p = panel(0), s = shot(p, 0, undefined, { bg: '#123' });
    word(s, 'ПЕРВЫЙ', CX, 600, 0.5, { size: 150, fill: LIGHT, enter: 'drop' });
    word(s, 'ВТОРОЙ', CX, 800, 0.5, { size: 150, fill: LIGHT, enter: 'left' });
    hero(s, 'петя', CX, 1000, 1, [[0, 'neutral'], [0.8, 'grin']], 0, D);
    finish(p); caps(p, 'один');
  }],
  ['два', 'Два', (m, D) => {
    const p = panel(0), s = shot(p, 0, undefined, { bg: '#321' });
    word(s, 'ТРЕТИЙ', CX, 600, 0.5, { size: 150, fill: LIGHT });
    label(s, 'ЧЕТВЁРТЫЙ', CX, 800, 0.5, { size: 60 });
    finish(p); caps(p, 'два');
  }, { trans: TRANS }],
];
start(BEATS);
"""


def _эпизод_из_двух(мини, trans='whip', анимации=''):
    (мини / 'scenes.js').write_text(СЦЕНЫ.replace('TRANS', f"'{trans}'"), encoding='utf-8')
    (мини / 'episode.yaml').write_text(f"""название: Движение
стиль: dark-yard
скрипты: [scenes.js]
герои:
  петя: {{очки: true}}
{анимации}""", encoding='utf-8')
    (мини / 'narration.yaml').write_text('биты:\n  один: "[[hi]]Привет, [[w]]мир."\n  два: "[[hi]]Привет, [[w]]мир."\n', encoding='utf-8')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', '1.4', '-codec:a', 'libmp3lame', str(мини / 'audio' / 'два.mp3')], check=True)
    тм = json.loads((мини / 'audio' / 'timings.json').read_text(encoding='utf-8'))
    тм['два'] = тм['один']
    (мини / 'audio' / 'timings.json').write_text(json.dumps(тм, ensure_ascii=False), encoding='utf-8')


def _страница(мини, имя):
    вых = build.собрать(мини, выход=config.ROOT / 'build' / имя)
    return вых


class _Браузер:
    def __init__(self, вых):
        self.srv, self.порт = serve.запустить(вых)
        self.ошибки = []

    def __enter__(self):
        self.pw = playwright.sync_playwright().start()
        try:
            br = self.pw.chromium.launch()
        except Exception as e:
            self.pw.stop()
            self.srv.shutdown()
            pytest.skip(f'нет Chromium: {e}')
        self.br = br
        self.page = br.new_page(viewport={'width': 450, 'height': 800})
        self.page.on('pageerror', lambda e: self.ошибки.append(str(e)))
        self.page.on('console', lambda m: self.ошибки.append(m.text) if m.type == 'error' else None)
        self.page.goto(f'http://127.0.0.1:{self.порт}/index.html?clean')
        self.page.wait_for_function('window.MM && window.MM.ready', timeout=60000)
        return self

    def __exit__(self, *a):
        self.br.close()
        self.pw.stop()
        self.srv.shutdown()
        assert not self.ошибки, self.ошибки

    def кадр(self, t):
        self.page.evaluate('t => MM.seek(t)', t)
        return self.page.screenshot()


@pytest.mark.browser
def test_входы_отличаются_друг_от_друга(мини):
    _эпизод_из_двух(мини, trans='cut')
    with _Браузер(_страница(мини, 'тест-входы')) as b:
        # у слова с drop в начале входа смещение вверх, у left — влево; в конце оба на месте
        pos = lambda t, i: b.page.evaluate(f"(t => {{ MM.seek(t); const e = [...document.querySelectorAll('#mm-svg text')].filter(x => x.textContent === ['ПЕРВЫЙ','ВТОРОЙ'][{i}])[0]; const r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }})({t})")
        a0, a1 = pos(0.55, 0), pos(1.2, 0)
        b0, b1 = pos(0.55, 1), pos(1.2, 1)
        assert a0[1] < a1[1] - 20 and abs(a0[0] - a1[0]) < 5, f'drop должен падать сверху: {a0} → {a1}'
        assert b0[0] < b1[0] - 20 and abs(b0[1] - b1[1]) < 5, f'left должен влетать слева: {b0} → {b1}'


@pytest.mark.browser
def test_переход_показывает_обе_сцены_а_потом_одну(мини):
    _эпизод_из_двух(мини, trans='whip')
    with _Браузер(_страница(мини, 'тест-переход')) as b:
        граница = b.page.evaluate('MM.manifest().beats[1].start')
        видимые = lambda t: (b.page.evaluate('t => MM.seek(t)', t), b.page.evaluate("[...document.querySelectorAll('#mm-svg > g')].filter(g => g.getAttribute('display') === 'inline').length"))[1]
        assert видимые(граница - .05) == 1
        assert видимые(граница + .06) == 2, 'в начале перехода под новой сценой видна уходящая'
        assert видимые(граница + .5) == 1, 'после перехода остаётся одна сцена'
        # детерминизм: тот же момент даёт тот же кадр, даже после перемотки назад
        k1 = b.кадр(граница + .08)
        b.кадр(граница + 1)
        assert b.кадр(граница + .08) == k1


@pytest.mark.browser
def test_камера_двигает_сцену_но_не_субтитры(мини):
    _эпизод_из_двух(мини, trans='cut', анимации='анимации:\n  камера: [наезд]\n  входы: []\n')
    with _Браузер(_страница(мини, 'тест-камера')) as b:
        сост = lambda t: (b.page.evaluate('t => MM.seek(t)', t), b.page.evaluate("[BEAT_LIST[0].world.getAttribute('transform'), BEAT_LIST[0].fixed.getAttribute('transform')]"))[1]
        начало, конец = сост(.05), сост(1.3)
        assert начало[0] != конец[0] and конец[0] and 'scale' in конец[0], f'камера должна менять слой сцены: {начало} → {конец}'
        assert начало[1] is None and конец[1] is None, 'слой субтитров стоит на месте'


@pytest.mark.browser
def test_реакция_героя_на_смену_эмоции(мини):
    _эпизод_из_двух(мини, trans='cut', анимации='анимации:\n  реакция: 0.08\n  входы: []\n')
    with _Браузер(_страница(мини, 'тест-реакция')) as b:
        # тело героя — единственный слой с масштабом по двум осям; в покое он «дышит» в пределах 1,5 %, при смене эмоции вытягивается заметно сильнее
        вытяжка = lambda t: (b.page.evaluate('t => MM.seek(t)', t), b.page.evaluate("Math.max(...[...document.querySelectorAll('#mm-svg g')].map(g => (/scale\\(([\\d.]+) ([\\d.]+)\\)/.exec(g.getAttribute('transform') || '') || [0, 0, 0])[2]).map(Number))"))[1]
        assert вытяжка(0.87) > 1.05, 'в момент смены эмоции тело вытягивается (вздрагивание)'
        assert вытяжка(0.3) < 1.02, 'без смены эмоции героя ничего не дёргает'

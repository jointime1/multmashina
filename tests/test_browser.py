"""Дымовой тест движка в настоящем браузере: страница собирается, кадр зависит от времени, ошибок в консоли нет."""
import pytest

from mmlib import build, config, serve

playwright = pytest.importorskip('playwright.sync_api')


@pytest.mark.browser
def test_страница_рисует_кадры(мини):
    вых = build.собрать(мини, выход=config.ROOT / 'build' / 'тест-мини')
    srv, порт = serve.запустить(вых)
    ошибки = []
    try:
        with playwright.sync_playwright() as p:
            try:
                br = p.chromium.launch()
            except Exception as e:
                pytest.skip(f'нет Chromium: {e}')
            page = br.new_page(viewport={'width': 450, 'height': 800})
            page.on('pageerror', lambda e: ошибки.append(str(e)))
            page.on('console', lambda m: ошибки.append(m.text) if m.type == 'error' else None)
            page.goto(f'http://127.0.0.1:{порт}/index.html?clean')
            page.wait_for_function('window.MM && window.MM.ready', timeout=60000)
            man = page.evaluate('MM.manifest()')
            assert man['w'] == 900 and man['h'] == 1600
            assert man['beats'][0]['id'] == 'один' and man['duration'] > 1.4
            кадры = []
            for t in (0.05, 1.3):
                page.evaluate('t => MM.seek(t)', t)
                кадры.append(page.screenshot())
            assert кадры[0] != кадры[1], 'кадр не зависит от времени: анимации не работают'
            page.evaluate('t => MM.seek(t)', 1.3)
            assert page.screenshot() == кадры[1], 'один и тот же момент даёт разные кадры: рендер недетерминирован'
            br.close()
    finally:
        srv.shutdown()
    assert not ошибки, ошибки


@pytest.mark.browser
def test_нерисованная_линия_не_оставляет_точку(мини, tmp_path):
    """У линии нулевой длины круглые кончики рисуют точку: до начала рисования (и вообще пока d=0) линия должна быть скрыта."""
    (мини / 'scenes.js').write_text("""'use strict';
const BEATS = [['один', 'Тест', (m, D) => {
  const p = panel(0), s = shot(p, 0, undefined, { bg: DARK });
  strike(s, 100, 300, 700, 300, 1.0);
  finish(p); caps(p, 'один');
}]];
start(BEATS);
""", encoding='utf-8')
    вых = build.собрать(мини, выход=config.ROOT / 'build' / 'тест-линия')
    srv, порт = serve.запустить(вых)
    try:
        with playwright.sync_playwright() as p:
            try:
                br = p.chromium.launch()
            except Exception as e:
                pytest.skip(f'нет Chromium: {e}')
            page = br.new_page(viewport={'width': 450, 'height': 800})
            page.goto(f'http://127.0.0.1:{порт}/index.html?clean')
            page.wait_for_function('window.MM && window.MM.ready', timeout=60000)
            видимость = lambda t: (page.evaluate('t => MM.seek(t)', t), page.evaluate("[...document.querySelectorAll('#mm-svg path[stroke-dasharray]')].map(e => e.getAttribute('visibility'))"))[1]
            assert видимость(.2) == ['hidden'], 'линия до начала рисования должна быть скрыта'
            assert видимость(1.3) == [None], 'нарисованная линия должна быть видна'
            br.close()
    finally:
        srv.shutdown()


@pytest.mark.browser
def test_облики_героев_и_tick_не_растягивает_бит(мини, tmp_path):
    """Герои с доспехом, татуировками, комплекцией, усами и ледяными глазами рисуются без ошибок; tick (вечное качание) не удлиняет бит."""
    (мини / 'episode.yaml').write_text("""название: Облики
стиль: dark-yard
скрипты: [scenes.js]
герои:
  олег: {доспех: "#475569", плащ: "#1e3a8a", тату: "#0b1220", руки: true, глаза: "#38bdf8", длинные_волосы: true, брови: "#8b93a3"}
  камиль: {усы: 1, очки: true, надпись: "Py", цвет_надписи: "#facc15"}
  серёга: {лысый: true, щетина_на_голове: true, руки: true, комплекция: 1.5, надпись: "CODEX"}
""", encoding='utf-8')
    (мини / 'scenes.js').write_text("""'use strict';
const BEATS = [['один', 'Тест', (m, D) => {
  const p = panel(0), s = shot(p, 0, undefined, { bg: DARK });
  const g = G(s, {}); tick(t => g.setAttribute('transform', `translate(${Math.sin(t) * 5} 0)`));
  hero(s, 'олег', 150, 800, .8, [[0, 'stern']], 0, D);
  hero(s, 'камиль', 450, 900, .8, [[0, 'smug']], 0, D);
  hero(s, 'серёга', 750, 800, .8, [[0, 'rage']], 0, D);
  finish(p); caps(p, 'один');
}]];
start(BEATS);
""", encoding='utf-8')
    вых = build.собрать(мини, выход=config.ROOT / 'build' / 'тест-облики')
    srv, порт = serve.запустить(вых)
    ошибки = []
    try:
        with playwright.sync_playwright() as p:
            try:
                br = p.chromium.launch()
            except Exception as e:
                pytest.skip(f'нет Chromium: {e}')
            page = br.new_page(viewport={'width': 450, 'height': 800})
            page.on('pageerror', lambda e: ошибки.append(str(e)))
            page.on('console', lambda m: ошибки.append(m.text) if m.type == 'error' else None)
            page.goto(f'http://127.0.0.1:{порт}/index.html?clean')
            page.wait_for_function('window.MM && window.MM.ready', timeout=60000)
            man = page.evaluate('MM.manifest()')
            assert man['duration'] < 5, f'tick растянул бит до {man["duration"]} с'
            page.evaluate('t => MM.seek(t)', 1.0)
            assert len(page.screenshot()) > 5000
            br.close()
    finally:
        srv.shutdown()
    assert not ошибки, ошибки


@pytest.mark.browser
def test_пауза_между_сценами_это_только_удержание(мини):
    """Субтитры, искры и покачивание, чей конец далеко за битом, не растягивают его: длина бита = голос + пауза_после_бита."""
    (мини / 'scenes.js').write_text("""'use strict';
const BEATS = [['один', 'Тест', (m, D) => {
  const p = panel(0), s = shot(p, 0, undefined, { bg: DARK });
  const w = word(s, 'мир', CX, 600, m('w'), { size: 160, fill: LIGHT });
  sparks(s, 450, 800, 0, 99); bob(w, 600, 8, 1, 0, 99);
  hero(s, 'петя', CX, 1000, 1, [[0, 'neutral'], [m('w'), 'grin']], 0, D);
  finish(p); caps(p, 'один');
}]];
start(BEATS);
""", encoding='utf-8')
    вых = build.собрать(мини, выход=config.ROOT / 'build' / 'тест-пауза')
    srv, порт = serve.запустить(вых)
    ошибки = []
    try:
        with playwright.sync_playwright() as p:
            try:
                br = p.chromium.launch()
            except Exception as e:
                pytest.skip(f'нет Chromium: {e}')
            page = br.new_page(viewport={'width': 450, 'height': 800})
            page.on('pageerror', lambda e: ошибки.append(str(e)))
            page.goto(f'http://127.0.0.1:{порт}/index.html?clean')
            page.wait_for_function('window.MM && window.MM.ready', timeout=60000)
            man, hold = page.evaluate('[MM.manifest(), FX.hold]')
            assert hold <= .35, f'пауза_после_бита по умолчанию слишком длинная: {hold} с'
            assert abs(man['duration'] - (1.4 + hold)) < .01, f'бит растянулся до {man["duration"]} с вместо {1.4 + hold}'
            br.close()
    finally:
        srv.shutdown()
    assert not ошибки, ошибки

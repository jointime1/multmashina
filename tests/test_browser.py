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

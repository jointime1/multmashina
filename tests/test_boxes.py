"""Плашки и штампы: буквы стоят в рамке по центру, поля сверху и снизу равны, слева и справа тоже. Браузерные тесты помечены browser."""
import pytest

from mmlib import build, config, serve

playwright = pytest.importorskip('playwright.sync_api')

СЦЕНА = """'use strict';
const BEATS = [['один', 'Тест', (m, D) => {
  const p = panel(0), s = shot(p, 0, undefined, { bg: DARK });
  room(s, 'комната');
  %s
  finish(p); caps(p, 'один');
}]];
start(BEATS);
"""

# поля: расстояние от букв (по метрикам шрифта) до внутреннего края рамки или блока, в долях кегля
JS_ПОЛЯ = """() => {
  const cv = document.createElement('canvas').getContext('2d'), out = [];
  for (const g of document.querySelectorAll('#mm-svg g')) {
    const r = [...g.children].find(c => c.tagName === 'rect' && c.getAttribute('rx')), t = [...g.children].find(c => c.tagName === 'text');
    if (!r || !t) continue;
    const size = parseFloat(t.getAttribute('font-size')), fam = t.getAttribute('font-family'), s = t.textContent;
    cv.font = `${t.getAttribute('font-weight')} ${size}px ${fam}`;
    const m = cv.measureText(s), an = t.getAttribute('text-anchor');
    const mt = t.transform.baseVal.numberOfItems ? t.transform.baseVal.consolidate().matrix : { e: 0, f: 0 }, tx = mt.e, ty = mt.f;   // x и y текста движок кладёт в transform
    const x0 = an === 'middle' ? tx - m.width / 2 : tx;
    const inkL = x0 - m.actualBoundingBoxLeft, inkR = x0 + m.actualBoundingBoxRight, inkT = ty - m.actualBoundingBoxAscent, inkB = ty + m.actualBoundingBoxDescent;
    const sw = r.getAttribute('fill') === 'none' ? parseFloat(r.getAttribute('stroke-width') || 0) / 2 : 0;   // у штампа рамка — штрих, считаем от его внутренней кромки
    const rx = parseFloat(r.getAttribute('x')), ry = parseFloat(r.getAttribute('y')), rw = parseFloat(r.getAttribute('width')), rh = parseFloat(r.getAttribute('height'));
    out.push({ text: s, size, top: (inkT - ry - sw) / size, bottom: (ry + rh - sw - inkB) / size, left: (inkL - rx - sw) / size, right: (rx + rw - sw - inkR) / size });
  }
  return out;
}"""


def _поля(мини, строка, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (мини / 'scenes.js').write_text(СЦЕНА % строка, encoding='utf-8')
    сборка = build.собрать(мини)
    srv, порт = serve.запустить(сборка)
    try:
        with playwright.sync_playwright() as p:
            try:
                br = p.chromium.launch()
            except Exception as e:
                pytest.skip(f'нет Chromium: {e}')
            page = br.new_context(viewport={'width': 900, 'height': 1600}).new_page()
            page.goto(f'http://127.0.0.1:{порт}/index.html?clean')
            page.wait_for_function('window.MM && window.MM.ready', timeout=60000)
            page.evaluate('document.fonts.ready')
            page.evaluate('MM.seek(0.9)')
            res = page.evaluate(JS_ПОЛЯ)
            br.close()
            return res
    finally:
        srv.shutdown()


@pytest.mark.browser
@pytest.mark.parametrize('размер', [50, 80, 120])
def test_штамп_держит_буквы_по_центру_рамки(мини, tmp_path, monkeypatch, размер):
    (поле,) = [x for x in _поля(мини, f"stamp(s, 'ОТВЕТЫ ЗАБЫТЫ', 450, 700, 0, {{ size: {размер}, r: 0 }});", tmp_path, monkeypatch) if x['text'] == 'ОТВЕТЫ ЗАБЫТЫ']
    assert abs(поле['top'] - поле['bottom']) < .06, f'буквы сползли вверх или вниз: {поле}'
    assert поле['top'] > .2 and поле['bottom'] > .2, f'буквы упираются в рамку: {поле}'
    assert abs(поле['left'] - поле['right']) < .06 and поле['left'] > .2, f'поля по бокам неровные: {поле}'


@pytest.mark.browser
@pytest.mark.parametrize('размер', [40, 56, 80])
def test_ярлык_держит_буквы_по_центру_блока(мини, tmp_path, monkeypatch, размер):
    (поле,) = [x for x in _поля(мини, f"label(s, 'ОТВЕТЫ ЗАБЫТЫ', 450, 700, 0, {{ size: {размер} }});", tmp_path, monkeypatch) if x['text'] == 'ОТВЕТЫ ЗАБЫТЫ']
    assert abs(поле['top'] - поле['bottom']) < .06, f'буквы сползли вверх или вниз: {поле}'
    assert поле['top'] > .15 and поле['bottom'] > .15, f'буквы упираются в край блока: {поле}'
    assert abs(поле['left'] - поле['right']) < .06, f'поля по бокам неровные: {поле}'

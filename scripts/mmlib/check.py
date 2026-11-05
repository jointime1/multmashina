"""Проверка эпизода: то, что агент (или человек) иначе заметил бы только на готовом видео.

  • ошибки в сценах (опечатка в метке, неизвестный герой, сломанный вызов) — с именем бита, где это случилось;
  • слова вне безопасной зоны кадра (x 50–810, y 130–1290) дольше полусекунды: платформы закрывают остальное кнопками и шапкой;
  • бит дольше своего голоса из-за затянувшейся анимации;
  • темп речи: слишком быстро (> 3,4 слова в секунду) или вяло (< 1,2).
Слова, помеченные как украшение (data-decor), не проверяются.
"""
import json
from pathlib import Path

from . import build, config, serve

ЗОНА = (50, 130, 810, 1290)      # x0, y0, x1, y1
ДОПУСК = 6                       # обводка букв выходит за границу текста на несколько пикселей
JS_ТЕКСТЫ = """() => {
  // реальные границы букв (а не коробка строки): по метрикам шрифта, с учётом сдвигов, поворотов и масштабов всех родителей
  const cv = window.__mmcv || (window.__mmcv = document.createElement('canvas').getContext('2d'));
  const out = [];
  for (const el of document.querySelectorAll('#mm-svg text')) {
    let o = 1, n = el, decor = false;
    while (n && n.id !== 'mm-svg') {
      if (n.getAttribute) {
        const a = n.getAttribute('opacity'); if (a !== null) o *= parseFloat(a);
        if (n.getAttribute('display') === 'none') o = 0;
        if (n.getAttribute('data-decor')) decor = true;
      }
      n = n.parentNode;
    }
    if (o < 0.2 || decor) continue;
    const t = el.textContent, ctm = el.getScreenCTM();
    if (!t || !ctm) continue;
    cv.font = `${el.getAttribute('font-weight') || 400} ${parseFloat(el.getAttribute('font-size')) || 16}px ${el.getAttribute('font-family') || 'sans-serif'}`;
    const m = cv.measureText(t);
    if (m.width < 1) continue;
    const an = el.getAttribute('text-anchor') || 'start', x0 = an === 'middle' ? -m.width / 2 : an === 'end' ? -m.width : 0;
    const pts = [[x0, -m.actualBoundingBoxAscent], [x0 + m.width, -m.actualBoundingBoxAscent], [x0, m.actualBoundingBoxDescent], [x0 + m.width, m.actualBoundingBoxDescent]]
      .map(([x, y]) => [ctm.a * x + ctm.c * y + ctm.e, ctm.b * x + ctm.d * y + ctm.f]);
    const xs = pts.map(q => q[0]), ys = pts.map(q => q[1]);
    out.push([t.slice(0, 40), Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]);
  }
  return out;
}"""


def проверить(папка, стиль_имя=None, строго=False):
    from playwright.sync_api import sync_playwright
    папка = Path(папка)
    сборка = build.собрать(папка, стиль_имя=стиль_имя)
    ep, биты = config.эпизод(папка)
    тайминги = json.loads((папка / 'audio' / 'timings.json').read_text(encoding='utf-8'))
    srv, порт = serve.запустить(сборка)
    ошибки, замечания = [], []
    try:
        with sync_playwright() as p:
            br = p.chromium.launch()
            page = br.new_context(viewport={'width': 900, 'height': 1600}, device_scale_factor=1).new_page()
            page.on('pageerror', lambda e: ошибки.append(f'в сценах: {e}'))
            page.on('console', lambda m: ошибки.append(f'в консоли: {m.text}') if m.type == 'error' else None)
            page.goto(f'http://127.0.0.1:{порт}/index.html?clean')
            try:
                page.wait_for_function('window.MM && window.MM.ready', timeout=60000)
            except Exception:
                br.close()
                return _итог(ошибки or ['страница не загрузилась, ошибок в консоли нет'], [], 0, строго)
            man = page.evaluate('MM.manifest()')
            hold = config.стиль(ep.get('стиль', 'dark-yard'), папка).get('effects', {}).get('hold', .6)
            вне = {}
            for b in man['beats']:
                t = 0.0
                while t <= b['len']:
                    page.evaluate('t => MM.seek(t)', b['start'] + min(t, b['len'] - .001))
                    for текст, x0, y0, x1, y1 in page.evaluate(JS_ТЕКСТЫ):
                        if x1 < 0 or x0 > 900 or y1 < 0 or y0 > 1600:
                            continue                                  # целиком за кадром: не видно, не считается
                        сдвиг = max(ЗОНА[0] - x0, x1 - ЗОНА[2], ЗОНА[1] - y0, y1 - ЗОНА[3])
                        if сдвиг > ДОПУСК:
                            k = (b['id'], текст)
                            был = вне.get(k, [0, 0, None, 0])
                            вне[k] = [max(был[0], round(сдвиг)), t if сдвиг >= был[0] else был[1], [round(x0), round(y0), round(x1), round(y1)] if сдвиг >= был[0] else был[2], был[3] + 1]
                    t += .25
                лишнее = b['len'] - (b['voice_at'] - b['start'] + b['voice_dur']) - hold
                if лишнее > 1.0:
                    замечания.append(f'бит «{b["id"]}» дольше голоса на {лишнее:.1f} с: какая-то анимация заканчивается позже слов (укоротите её или оставьте так намеренно)')
            br.close()
        for (бит, текст), (сдвиг, t, рамка, раз) in sorted(вне.items()):
            if раз < 2:
                continue                                              # въезд или вылет за долю секунды — это движение, а не ошибка раскладки
            замечания.append(f'бит «{бит}»: «{текст}» вылезает за безопасную зону на {сдвиг} px (в момент {t} с, рамка {рамка}); зона x {ЗОНА[0]}–{ЗОНА[2]}, y {ЗОНА[1]}–{ЗОНА[3]}')
        for id_ in биты:
            слов = len(тайминги[id_]['words']); длит = тайминги[id_]['dur']
            темп = слов / длит if длит else 0
            if слов >= 4 and темп > 3.4:
                замечания.append(f'бит «{id_}»: речь очень быстрая, {темп:.1f} слова/с (комфортно до ~3): сократите текст или снизьте темп озвучки')
            if слов >= 4 and темп < 1.2:
                замечания.append(f'бит «{id_}»: речь вялая, {темп:.1f} слова/с: добавьте текста или поднимите темп озвучки')
        return _итог(ошибки, замечания, man['duration'], строго)
    finally:
        srv.shutdown()


def _итог(ошибки, замечания, длительность, строго):
    for e in ошибки:
        print(f'✗ Ошибка {e}')
    for z in замечания:
        print(f'! Замечание: {z}')
    if длительность:
        совет = '' if 15 <= длительность <= 90 else ' (для рилса обычно 15–60 секунд)'
        print(f'Эпизод {длительность:.1f} с{совет}.')
    if not ошибки and not замечания:
        print('✓ Ошибок и замечаний нет.')
    return 1 if ошибки or (строго and замечания) else 0

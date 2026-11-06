"""Контактные листы: кадры эпизода в нужные моменты, чтобы увидеть собственную работу глазами (картинки можно открыть и разобрать).

По умолчанию на каждый бит — три кадра: начало (0,3 с), середина и конец. Свои моменты: «бит:секунды», «бит:mid», «бит:end»,
например  --моменты hook:0.3,offer:end. Результат: <куда>/лист-1.png … и <куда>/список.txt — какой кадр в листе чем является
(листы читаются слева направо, сверху вниз, по пять кадров в ряд).
"""
import subprocess
from pathlib import Path

from . import build, gitignore, serve


def _моменты(man, строка):
    биты = {b['id']: b for b in man['beats']}
    res = []
    if not строка:
        for b in man['beats']:
            for подпись, t in (('начало', min(.3, b['len'] * .3)), ('середина', b['len'] * .5), ('конец', b['len'] - .15)):
                res.append((b['id'], подпись, b['start'] + t, t))
        return res
    for часть in строка.split(','):
        id_, _, t = часть.strip().partition(':')
        if id_ not in биты:
            raise SystemExit(f'Нет бита «{id_}». Есть: {", ".join(биты)}')
        b = биты[id_]
        сек = b['len'] * .5 if t == 'mid' else b['len'] - .15 if t == 'end' else float(t or 0)
        res.append((id_, t or 'начало', b['start'] + сек, сек))
    return res


def снять(папка, куда=None, моменты=None, стиль_имя=None, ширина=540):
    from playwright.sync_api import sync_playwright
    папка = Path(папка)
    сборка = build.собрать(папка, стиль_имя=стиль_имя)
    куда = Path(куда) if куда else Path.cwd() / 'review' / папка.resolve().name
    куда.mkdir(parents=True, exist_ok=True)
    gitignore.скрыть_от_git(куда, '*.png', '*.txt')
    for старый in куда.glob('*'):
        if старый.suffix in ('.png', '.txt'):
            старый.unlink()
    srv, порт = serve.запустить(сборка)
    try:
        with sync_playwright() as p:
            br = p.chromium.launch()
            высота = int(ширина * 16 / 9)
            page = br.new_context(viewport={'width': ширина, 'height': высота}, device_scale_factor=1).new_page()
            ошибки = []
            page.on('pageerror', lambda e: ошибки.append(str(e)))
            page.goto(f'http://127.0.0.1:{порт}/index.html?clean')
            try:
                page.wait_for_function('window.MM && window.MM.ready', timeout=60000)
            except Exception:
                raise SystemExit('Страница не загрузилась. Ошибки:\n  ' + '\n  '.join(ошибки or ['(пусто)']))
            man = page.evaluate('MM.manifest()')
            точки = _моменты(man, моменты)
            листы, строки = [], []
            for i, (бит, подпись, t, локальное) in enumerate(точки):
                лист, номер = divmod(i, 10)
                d = куда / f'.л{лист}'
                d.mkdir(exist_ok=True)
                page.evaluate('t => MM.seek(t)', t)
                page.screenshot(path=str(d / f'f{номер:02d}.png'))
                строки.append(f'лист-{лист + 1}, позиция {номер + 1}: бит «{бит}», {подпись} ({локальное:.2f} с от начала бита, {t:.2f} с от начала эпизода)')
                if d not in листы:
                    листы.append(d)
            br.close()
        for k, d in enumerate(листы, 1):
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '1', '-i', str(d / 'f%02d.png'), '-vf', 'scale=360:640,tile=5x2:padding=6:color=0x202020',
                            '-frames:v', '1', str(куда / f'лист-{k}.png')], check=True)
            for f in d.glob('*.png'):
                f.unlink()
            d.rmdir()
        (куда / 'список.txt').write_text('\n'.join(строки) + '\n', encoding='utf-8')
        print(f'Кадров: {len(точки)}, листов: {len(листы)}. Откройте {куда}/лист-1.png; расшифровка кадров — {куда}/список.txt')
        for e in ошибки:
            print(f'! Ошибка в сценах: {e}')
    finally:
        srv.shutdown()

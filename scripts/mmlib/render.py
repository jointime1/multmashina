"""Рендер эпизода в MP4: кадры снимает настоящий браузер (Playwright), звук собирается в numpy, видео кодирует ffmpeg.

Кадр берётся не «записью экрана», а перемоткой: страница умеет нарисовать любое мгновение (MM.seek(t)), поэтому видео получается
точным и одинаковым при каждом запуске, а кадры можно снимать параллельно в нескольких браузерах.
"""
import json
import math
import re
import shutil
import subprocess
import tempfile
import wave
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from . import serve

SR = 44100
ГРОМКОСТЬ_ЭФФЕКТОВ = .25     # эффекты тише голоса; множитель на «громкость» из sfx(...)


def _снять_кадры(порт, диапазон, ширина, высота, fps, папка):
    from playwright.sync_api import sync_playwright
    a, b = диапазон
    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_context(viewport={'width': ширина, 'height': высота}, device_scale_factor=1).new_page()
        page.goto(f'http://127.0.0.1:{порт}/index.html?clean')
        page.wait_for_function('window.MM && window.MM.ready', timeout=120000)
        for i in range(a, b):
            page.evaluate('t => MM.seek(t)', i / fps)
            page.screenshot(path=str(папка / f'{i:06d}.jpg'), type='jpeg', quality=93)
        br.close()
    return b - a


def _манифест(порт):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.goto(f'http://127.0.0.1:{порт}/index.html?clean')
        try:
            page.wait_for_function('window.MM && window.MM.ready', timeout=120000)
        except Exception:
            raise SystemExit('Страница эпизода не загрузилась. Ошибки в консоли браузера:\n  ' + '\n  '.join(errors or ['(пусто)']))
        man = page.evaluate('MM.manifest()')
        br.close()
    if errors:
        raise SystemExit('В сценах есть ошибки:\n  ' + '\n  '.join(errors))
    return man


def _декодировать(файл):
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(файл), '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.float32)


def _звук(сборка, man, куда):
    """Голос и эффекты → одна дорожка (wav)."""
    длина = int(math.ceil(man['duration'] * SR)) + SR
    дорожка = np.zeros(длина, np.float32)

    def положить(x, t, g):
        i = int(t * SR)
        if i < длина:
            n = min(len(x), длина - i)
            дорожка[i:i + n] += x[:n] * g
    for b in man['beats']:
        f = сборка / 'audio' / f'{b["id"]}.mp3'
        if f.exists():
            положить(_декодировать(f), b['voice_at'], 1.0)
    кэш = {}
    for s in man['sfx']:
        f = сборка / 'sfx' / f'{s["name"]}.mp3'
        if not f.exists():
            raise SystemExit(f'В сцене вызван эффект «{s["name"]}», а файла sfx/{s["name"]}.mp3 нет. Сгенерируйте: python scripts/mm.py ассеты')
        x = кэш.setdefault(s['name'], _декодировать(f))
        положить(x, s['t'], ГРОМКОСТЬ_ЭФФЕКТОВ * s['vol'])
    дорожка = np.clip(дорожка, -1, 1)
    with wave.open(str(куда), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((дорожка * 32767).astype('<i2').tobytes())


def _srt(сборка, man):
    реплики = json.loads((сборка / 'cues.json').read_text(encoding='utf-8'))
    старт = {b['id']: b['voice_at'] for b in man['beats']}
    конец = {b['id']: b['voice_at'] + b['voice_dur'] for b in man['beats']}
    строки, n = [], 0
    ts = lambda s: f'{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d},{int(round(s % 1 * 1000)):03d}'.replace(',1000', ',999')
    for id_, cues in реплики.items():
        for i, (t, текст) in enumerate(cues):
            a = старт[id_] + t
            b = старт[id_] + cues[i + 1][0] if i + 1 < len(cues) else конец[id_]
            n += 1
            строки += [str(n), f'{ts(a)} --> {ts(max(b, a + .3))}', текст, '']
    return '\n'.join(строки)


def снять(сборка, mp4, fps=30, высота=1920, потоков=4, lufs=-14, кодек='libx264'):
    сборка, mp4 = Path(сборка).resolve(), Path(mp4).resolve()
    srv, порт = serve.запустить(сборка)
    try:
        man = _манифест(порт)
        ширина = int(round(высота * man['w'] / man['h'] / 2) * 2)
        n = int(math.ceil(man['duration'] * fps))
        print(f'Эпизод: {man["duration"]:.1f} с, {n} кадров, {ширина}×{высота}, потоков {потоков}')
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            шаг = int(math.ceil(n / потоков))
            части = [(i, min(i + шаг, n)) for i in range(0, n, шаг)]
            with ProcessPoolExecutor(max_workers=потоков) as ex:
                готово = sum(ex.map(_снять_кадры, [порт] * len(части), части, [ширина] * len(части), [высота] * len(части), [fps] * len(части), [td] * len(части)))
            print(f'Снято кадров: {готово}')
            _звук(сборка, man, td / 'audio.wav')
            mp4.parent.mkdir(parents=True, exist_ok=True)
            tmp = mp4.with_suffix('.tmp.mp4')
            подкл = ['-c:v', 'h264_videotoolbox', '-b:v', '12M'] if кодек == 'videotoolbox' else ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium']
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(fps), '-i', str(td / '%06d.jpg'), '-i', str(td / 'audio.wav'),
                            *подкл, '-pix_fmt', 'yuv420p', '-af', f'loudnorm=I={lufs}:TP=-1.5:LRA=11', '-c:a', 'aac', '-b:a', '192k',
                            '-t', f'{man["duration"]:.3f}', '-movflags', '+faststart', str(tmp)], check=True)
            tmp.replace(mp4)
        mp4.with_suffix('.srt').write_text(_srt(сборка, man), encoding='utf-8')
        print(f'Готово: {mp4} ({mp4.stat().st_size / 1e6:.1f} МБ) и {mp4.with_suffix(".srt").name}')
    finally:
        srv.shutdown()

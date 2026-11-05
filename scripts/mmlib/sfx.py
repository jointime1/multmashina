"""Звуковые эффекты синтезом (numpy): свист, хлопок, тик, глухой удар. Файлы без внешних зависимостей, лицензия — как у репозитория.

Результат кладётся в assets/sfx/*.mp3 и копируется в каждую сборку; свои эффекты можно положить туда же под любым именем
и вызывать в сценах как sfx(BEAT_ID, t, 'имя', громкость).
"""
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

SR = 44100


def _нормировать(x, пик=.9):
    return x / max(np.abs(x).max(), 1e-9) * пик


def _низкие(шум, a):
    """Простой фильтр низких частот: a — «открытость» от 0 до 1 на каждый отсчёт."""
    y = np.zeros_like(шум)
    for i in range(1, len(шум)):
        y[i] = y[i - 1] + a[i] * (шум[i] - y[i - 1])
    return y


def свист():
    n = int(SR * .45); t = np.linspace(0, 1, n)
    rng = np.random.default_rng(1)
    a = .02 + .5 * np.sin(np.pi * t) ** 2                     # фильтр открывается и закрывается — получается «ш-ш-ш-ух»
    return _нормировать(_низкие(rng.standard_normal(n), a) * np.sin(np.pi * t) ** 1.5)


def хлопок():
    n = int(SR * .6); t = np.arange(n) / SR
    rng = np.random.default_rng(2)
    удар = rng.standard_normal(n) * np.exp(-t * 38)
    бас = np.sin(2 * np.pi * (140 * np.exp(-t * 9) + 45) * t) * np.exp(-t * 7)
    return _нормировать(.7 * удар + 1.1 * бас)


def тик():
    n = int(SR * .05); t = np.arange(n) / SR
    return _нормировать(np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 110), .6)


def удар():
    n = int(SR * .45); t = np.arange(n) / SR
    rng = np.random.default_rng(3)
    return _нормировать(np.sin(2 * np.pi * (95 * np.exp(-t * 6) + 40) * t) * np.exp(-t * 8) + .15 * rng.standard_normal(n) * np.exp(-t * 40))


ЭФФЕКТЫ = {'whoosh': свист, 'bang': хлопок, 'tick': тик, 'thud': удар}   # имена латиницей: их пишут в коде сцен


def сгенерировать(папка):
    папка = Path(папка); папка.mkdir(parents=True, exist_ok=True)
    for имя, f in ЭФФЕКТЫ.items():
        pcm = (np.clip(f(), -1, 1) * 32767).astype('<i2')
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / 'x.wav'
            with wave.open(str(wav), 'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wav), '-codec:a', 'libmp3lame', '-b:a', '128k', str(папка / f'{имя}.mp3')], check=True)
        print(f'эффект {имя}: {папка / (имя + ".mp3")}')

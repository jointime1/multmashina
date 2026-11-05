"""Образцы голоса по описанию (Qwen3-TTS VoiceDesign): несколько вариантов, чтобы выбрать тембр и записать его эталоном для клона.

Каждый вариант — свой seed: одно и то же описание с разными seed даёт разные голоса в заданном характере. Рядом печатаются длительность
и средняя высота тона (для проверки «этот ниже того»); тембр и характер оценивает только слух.
"""
from pathlib import Path

import numpy as np

from .backends import QwenДизайн, ОшибкаОзвучки


def высота(samples, sr):
    """Средняя высота тона по звонким кадрам (автокорреляция), Гц; None, если речи не нашлось."""
    n = int(sr * .04)
    res = []
    for i in range(0, len(samples) - n, n // 2):
        f = samples[i:i + n] - samples[i:i + n].mean()
        if np.sqrt(np.mean(f ** 2)) < .02:
            continue
        ac = np.correlate(f, f, 'full')[n - 1:]
        lo, hi = int(sr / 400), int(sr / 70)
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > .35 * ac[0]:
            res.append(sr / k)
    return round(float(np.median(res)), 1) if res else None


def сделать(база, описание, текст, seeds):
    import soundfile as sf
    база = Path(база)
    база.parent.mkdir(parents=True, exist_ok=True)
    try:
        движок = QwenДизайн({'описание': описание}, Path('.'))
    except ОшибкаОзвучки as e:
        raise SystemExit(f'Ошибка озвучки: {e}')
    for seed in seeds:
        движок.н['seed'] = seed
        wav = база.with_name(f'{база.name}.seed{seed}.wav')
        движок.синтез(текст, wav)
        x, sr = sf.read(str(wav), dtype='float32')
        print(f'{wav}: {len(x) / sr:.1f} с, тон ≈ {высота(x.reshape(-1), sr)} Гц', flush=True)
    print('Послушайте варианты, лучший скопируйте как эталон (voice/….wav) и впишите в episode.yaml → озвучка → голоса дословный текст:')
    print(f'  {текст}')

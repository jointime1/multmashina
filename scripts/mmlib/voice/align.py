"""Времена слов: локальный Whisper слышит запись, слова сценария сопоставляются с услышанными по порядку. Отсюда времена меток и субтитров."""
import re
import subprocess
from difflib import SequenceMatcher

import numpy as np

МЕТКА = re.compile(r'\[\[(\w+)\]\]')
СЛОВО = re.compile(r"[\w'’-]+")


def разобрать_метки(сырой):
    """Чистый текст и {метка: позиция в чистом тексте}."""
    метки, куски, поз = {}, [], 0
    for i, часть in enumerate(МЕТКА.split(сырой)):
        if i % 2:
            if часть in метки:
                raise ValueError(f'метка «{часть}» повторяется в одном бите')
            метки[часть] = поз
        else:
            куски.append(часть); поз += len(часть)
    return ''.join(куски), метки


def время_меток(чистый, метки, слова):
    """Для каждой метки — время начала первого слова на позиции метки или после неё."""
    курсор, найденные = 0, []
    for t, w in слова:
        i = чистый.find(w, курсор)
        if i >= 0:
            найденные.append((i, t)); курсор = i + len(w)
    res = {}
    for имя, поз in метки.items():
        t = next((t for i, t in найденные if i >= поз), None)
        if t is None:
            raise ValueError(f'метка «{имя}» не совпала ни с одним произнесённым словом')
        res[имя] = round(float(t), 3)
    return res


def _норма(w):
    return re.sub(r'[^\w]', '', w.lower().replace('ё', 'е'))


def _похожи(x, y):
    return x == y or (len(x) >= 4 and len(y) >= 4 and x[:4] == y[:4]) or SequenceMatcher(None, x, y).ratio() >= .62


class Выравнивание:
    def __init__(self, модель='small'):
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise SystemExit('Не хватает пакета faster-whisper (нужен для времён слов). Запускайте через uv с --extra voice')
        self.модель = WhisperModel(модель, device='cpu', compute_type='int8')

    def слова(self, mp3, чистый, длительность):
        pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp3), '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
        сегменты, _ = self.модель.transcribe(np.frombuffer(pcm, np.float32), word_timestamps=True, language='ru')
        услышано = [(_норма(w.word), w.start) for s in сегменты for w in s.words if _норма(w.word)]
        токены, времена, j = СЛОВО.findall(чистый), [], 0
        for tok in токены:
            n = _норма(tok)
            k = next((k for k in range(j, min(j + 6, len(услышано))) if _похожи(n, услышано[k][0])), None)
            времена.append(None if k is None else услышано[k][1])
            if k is not None:
                j = k + 1
        for i, v in enumerate(времена):          # слова, которые Whisper склеил или написал иначе: посередине между соседями
            if v is None:
                до = next((времена[q] for q in range(i - 1, -1, -1) if времена[q] is not None), 0.0)
                после = next((времена[q] for q in range(i + 1, len(времена)) if времена[q] is not None), длительность)
                времена[i] = до + (после - до) * .5
        for i in range(1, len(времена)):         # времена не убывают
            времена[i] = max(времена[i], времена[i - 1])
        слова = [[round(float(t), 3), w] for t, w in zip(времена, токены)]
        if слова:
            слова[0][0] = min(слова[0][0], .1)
        return слова, len(услышано)

"""Бэкенды озвучки: каждый превращает текст в сырую запись (wav). Тяжёлые зависимости подключаются только при выборе бэкенда.

  qwen-клон    Qwen3-TTS (mlx-audio, Apple Silicon): голос клонируется с эталонной записи — один тембр на весь эпизод
  qwen-дизайн  Qwen3-TTS VoiceDesign: голос «заказывается» текстовым описанием; каждая реплика сэмплирует голос заново,
               поэтому годится для подбора тембра (его записывают как эталон для клона), а не для целого эпизода
  chatterbox   Chatterbox multilingual (PyTorch, mps/cpu): голос по умолчанию или клон с эталона
  edge         Edge TTS (онлайн, бесплатно): готовые голоса Microsoft, например ru-RU-SvetlanaNeural
"""
import asyncio
import subprocess
from pathlib import Path

import numpy as np


class ОшибкаОзвучки(Exception):
    pass


def _нужен(пакет, как):
    raise ОшибкаОзвучки(f'Не хватает пакета «{пакет}». Запустите команду так:\n  {как}')


def _записать(wav, samples, sr):
    import soundfile as sf
    sf.write(str(wav), samples, sr)


class QwenКлон:
    РЕПО = 'mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16'

    def __init__(self, настройки, папка):
        self.н, self.папка = настройки, Path(папка)
        эталон = self.папка / настройки.get('эталон', 'voice/ref.wav')
        if not эталон.exists():
            raise ОшибкаОзвучки(f'Нет эталонной записи {эталон}. Сделайте её бэкендом qwen-дизайн или положите свою (10–15 секунд чистой речи)')
        if not настройки.get('текст_эталона'):
            raise ОшибкаОзвучки('Для клона нужен текст_эталона: дословный текст того, что сказано в эталонной записи')
        try:
            import mlx.core as mx
            from mlx_audio.tts.utils import load_model
        except ImportError:
            _нужен('mlx-audio', 'uv run --extra voice --extra qwen python scripts/mm.py озвучить ' + self.папка.as_posix())
        self.mx, self.эталон = mx, эталон
        self.модель = load_model(self.РЕПО)

    def синтез(self, текст, wav):
        self.mx.random.seed(int(self.н.get('seed', 11)))
        res = list(self.модель.generate(text=текст, ref_audio=str(self.эталон), ref_text=self.н['текст_эталона'], lang_code='russian'))
        samples = np.concatenate([np.array(r.audio).reshape(-1) for r in res])
        _записать(wav, samples, res[0].sample_rate)


class QwenДизайн(QwenКлон):
    РЕПО = 'mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16'

    def __init__(self, настройки, папка):
        self.н, self.папка = настройки, Path(папка)
        if not настройки.get('описание'):
            raise ОшибкаОзвучки('Для qwen-дизайн нужно «описание» голоса (лучше по-английски: возраст, тембр, манера речи)')
        try:
            import mlx.core as mx
            from mlx_audio.tts.utils import load_model
        except ImportError:
            _нужен('mlx-audio', 'uv run --extra voice --extra qwen python scripts/mm.py озвучить ' + self.папка.as_posix() + ' --голос qwen-дизайн')
        self.mx = mx
        self.модель = load_model(self.РЕПО)

    def синтез(self, текст, wav):
        self.mx.random.seed(int(self.н.get('seed', 11)))
        res = list(self.модель.generate_voice_design(text=текст, instruct=self.н['описание'], language='russian'))
        _записать(wav, np.concatenate([np.array(r.audio).reshape(-1) for r in res]), res[0].sample_rate)


class Chatterbox:
    def __init__(self, настройки, папка):
        self.н, self.папка = настройки, Path(папка)
        try:
            import os
            os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
            import torch
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        except ImportError:
            _нужен('chatterbox-tts', 'uv run --extra voice --extra chatterbox python scripts/mm.py озвучить ' + self.папка.as_posix() + ' --голос chatterbox')
        self.torch = torch
        dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.модель = ChatterboxMultilingualTTS.from_pretrained(device=dev)   # устройство строкой: иначе веса с CUDA не переедут на CPU

    def синтез(self, текст, wav):
        self.torch.manual_seed(int(self.н.get('seed', 11)))
        эталон = self.н.get('эталон')
        wavt = self.модель.generate(текст, language_id='ru', audio_prompt_path=str(self.папка / эталон) if эталон else None,
                                    exaggeration=float(self.н.get('выразительность', .75)), cfg_weight=float(self.н.get('cfg', .3)))
        _записать(wav, wavt.cpu().numpy().reshape(-1), self.модель.sr)


class Edge:
    def __init__(self, настройки, папка):
        self.н = настройки
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            _нужен('edge-tts', 'uv run --extra voice --extra edge python scripts/mm.py озвучить ' + Path(папка).as_posix() + ' --голос edge')

    def синтез(self, текст, wav):
        import edge_tts
        mp3 = Path(wav).with_suffix('.edge.mp3')
        async def go():
            await edge_tts.Communicate(текст, self.н.get('голос', 'ru-RU-SvetlanaNeural'), rate=self.н.get('скорость', '+0%')).save(str(mp3))
        for попытка in range(5):          # Edge иногда отвечает пустым звуком, помогает повтор
            try:
                asyncio.run(go()); break
            except Exception as e:
                if попытка == 4:
                    raise ОшибкаОзвучки(f'Edge TTS не ответил: {e}')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mp3), '-ac', '1', '-ar', '24000', str(wav)], check=True)
        mp3.unlink()


БЭКЕНДЫ = {'qwen-клон': QwenКлон, 'qwen-дизайн': QwenДизайн, 'chatterbox': Chatterbox, 'edge': Edge}

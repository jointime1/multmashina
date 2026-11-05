"""Что есть на машине: ffmpeg, Chromium, платформа, голосовые бэкенды. Агент запускает это первым, чтобы выбрать озвучку и не гадать."""
import importlib.util
import platform
import shutil
import sys


def _импорт(имя):
    return importlib.util.find_spec(имя) is not None


def проверить():
    крит = []
    mac_arm = sys.platform == 'darwin' and platform.machine() == 'arm64'
    print(f'Python {platform.python_version()} на {platform.system()} {platform.machine()}')
    for утилита in ('ffmpeg', 'ffprobe', 'uv'):
        есть = shutil.which(утилита)
        print(f'  {"✓" if есть else "✗"} {утилита}' + ('' if есть else '   — установите (macOS: brew install ffmpeg uv)'))
        if not есть and утилита != 'uv':
            крит.append(утилита)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        print('  ✓ Chromium для Playwright')
    except ImportError:
        print('  ✗ playwright не установлен — запускайте через «uv run python scripts/mm.py …» из папки репозитория')
        крит.append('playwright')
    except Exception:
        print('  ✗ Chromium не скачан — выполните: uv run python -m playwright install chromium')
        крит.append('chromium')
    print('Озвучка:')
    for имя, пакет, как, ок in (
        ('edge', 'edge_tts', 'uv run --extra voice --extra edge python scripts/mm.py …', True),
        ('qwen-клон / qwen-дизайн', 'mlx_audio', 'uv run --extra voice --extra qwen python scripts/mm.py …', mac_arm),
        ('chatterbox', 'chatterbox', 'uv run --extra voice --extra chatterbox python scripts/mm.py …', True),
    ):
        работает = _импорт(пакет)
        причина = '' if ок else ' (нужен Mac на Apple Silicon)'
        print(f'  {"✓ готов" if работает else ("· можно включить" if ок else "✗ недоступен")}: {имя}{причина}' + ('' if работает or not ок else f'   → {как}'))
    print(f'  {"✓" if _импорт("faster_whisper") else "·"} выравнивание слов (faster-whisper): нужно любой озвучке, включается экстрой --extra voice')
    if mac_arm:
        print('Рекомендация: qwen-клон (один тембр на весь эпизод, лучший вариант для «характерных» голосов); без моделей — edge.')
    else:
        print('Рекомендация: edge (бесплатно, нужен интернет) или chatterbox.')
    return 1 if крит else 0

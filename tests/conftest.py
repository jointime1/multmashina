"""Общие заготовки тестов: минимальный эпизод с «озвучкой» из тишины (настоящие модели в тестах не нужны)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

КОРЕНЬ = Path(__file__).resolve().parents[1]


@pytest.fixture
def мини(tmp_path):
    """Копия tests/fixtures/mini с тишиной вместо голоса и ручными временами слов."""
    if not shutil.which('ffmpeg'):
        pytest.skip('нужен ffmpeg')
    папка = tmp_path / 'mini'
    shutil.copytree(КОРЕНЬ / 'tests' / 'fixtures' / 'mini', папка)
    (папка / 'audio').mkdir()
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', '1.4', '-codec:a', 'libmp3lame',
                    str(папка / 'audio' / 'один.mp3')], check=True)
    (папка / 'audio' / 'timings.json').write_text(json.dumps({'один': {'dur': 1.4, 'marks': {'hi': 0.1, 'w': 0.7}, 'words': [[0.1, 'Привет'], [0.7, 'мир']]}}, ensure_ascii=False))
    return папка

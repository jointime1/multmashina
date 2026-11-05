"""Новый эпизод из шаблона templates/episode: три бита, герой, комната, субтитры. Дальше его правят: текст, герои, сцены."""
import shutil
from pathlib import Path

from . import config


def создать(папка, стиль='dark-yard', название=None):
    папка = Path(папка)
    if папка.exists() and any(папка.iterdir()):
        raise config.ОшибкаКонфига(f'Папка {папка} не пустая: выберите другое имя или удалите её')
    config.стиль(стиль)                                  # сразу проверим, что стиль существует и читается
    shutil.copytree(config.ROOT / 'templates' / 'episode', папка, dirs_exist_ok=True)
    значения = {'{{название}}': название or папка.name, '{{стиль}}': стиль}
    for f in папка.rglob('*'):
        if f.is_file():
            t = f.read_text(encoding='utf-8')
            for k, v in значения.items():
                t = t.replace(k, v)
            f.write_text(t, encoding='utf-8')
    print(f'Эпизод создан: {папка}')
    print('Дальше: поправьте narration.yaml и scenes.js, затем озвучьте (uv run --extra voice --extra edge python scripts/mm.py озвучить ' + str(папка) + '; '
          'вместо edge можно qwen или chatterbox, см. «окружение»), проверьте (проверить), посмотрите кадры (кадры) и снимите (снять).')

"""Команды для ИИ-агента: окружение, новый, проверить, кадры. Браузерные тесты помечены browser и пропускаются без Chromium."""
import json
import shutil
import subprocess

import pytest

from mmlib import config, env, new

playwright = pytest.importorskip('playwright.sync_api')

СЦЕНА = """'use strict';
const BEATS = [['один', 'Тест', (m, D) => {
  const p = panel(0), s = shot(p, 0, undefined, { bg: DARK });
  room(s, 'комната');
  %s
  hero(s, 'петя', CX, 1000, 1, [[0, 'neutral'], [m('w'), 'grin']], 0, D);
  finish(p); caps(p, 'один');
}]];
start(BEATS);
"""


def _сцена(папка, строка):
    (папка / 'scenes.js').write_text(СЦЕНА % строка, encoding='utf-8')


def _озвучить_тишиной(папка, слов=3, длит=1.5):
    """Тишина вместо голоса для всех битов эпизода: достаточно, чтобы собрать страницу и проверить сцены."""
    _, биты = config.эпизод(папка)
    (папка / 'audio').mkdir(exist_ok=True)
    тайминги = {}
    for id_, текст in биты.items():
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', str(длит), '-codec:a', 'libmp3lame',
                        str(папка / 'audio' / f'{id_}.mp3')], check=True)
        метки = [s.split(']]')[0] for s in текст.split('[[')[1:]]
        тайминги[id_] = {'dur': длит, 'marks': {м: .1 + .3 * i for i, м in enumerate(метки)}, 'words': [[.1 + .3 * i, f'слово{i}'] for i in range(слов)]}
    (папка / 'audio' / 'timings.json').write_text(json.dumps(тайминги, ensure_ascii=False), encoding='utf-8')


@pytest.fixture
def в_пустой(tmp_path, monkeypatch):
    """build/ и review/ создаются в текущей папке: в тестах это временная."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------- окружение ----------

def test_окружение_печатает_всё_нужное(capsys):
    код = env.проверить()
    вывод = capsys.readouterr().out
    for слово in ('ffmpeg', 'Озвучка', 'edge', 'qwen', 'chatterbox', 'Рекомендация'):
        assert слово in вывод, слово
    assert код in (0, 1)


# ---------- новый ----------

def test_новый_создаёт_рабочий_эпизод(tmp_path):
    папка = tmp_path / 'ролик'
    new.создать(папка, 'light-cartoon', 'Мой ролик')
    for f in ('episode.yaml', 'narration.yaml', 'scenes.js'):
        assert (папка / f).exists(), f
    ep, биты = config.эпизод(папка)
    assert ep['название'] == 'Мой ролик' and ep['стиль'] == 'light-cartoon'
    assert list(биты) == ['hook', 'middle', 'outro']
    assert not any('{{' in f.read_text(encoding='utf-8') for f in папка.rglob('*') if f.is_file()), 'остались неподставленные поля шаблона'


def test_новый_не_затирает_чужое(tmp_path):
    (tmp_path / 'занято').mkdir()
    (tmp_path / 'занято' / 'важное.txt').write_text('важно')
    with pytest.raises(config.ОшибкаКонфига, match='не пустая'):
        new.создать(tmp_path / 'занято')
    assert (tmp_path / 'занято' / 'важное.txt').exists()


def test_новый_неизвестный_стиль(tmp_path):
    with pytest.raises(config.ОшибкаКонфига):
        new.создать(tmp_path / 'ролик', 'нет-такого-стиля')
    assert not (tmp_path / 'ролик').exists()


# ---------- проверить ----------

@pytest.mark.browser
def test_проверить_чистый_шаблон(tmp_path, в_пустой, capsys):
    from mmlib import check
    if not shutil.which('ffmpeg'):
        pytest.skip('нужен ffmpeg')
    папка = tmp_path / 'ролик'
    new.создать(папка)
    _озвучить_тишиной(папка)
    try:
        код = check.проверить(папка)
    except Exception as e:
        if 'Executable' in str(e):
            pytest.skip(f'нет Chromium: {e}')
        raise
    вывод = capsys.readouterr().out
    assert код == 0, вывод
    assert 'Ошибок и замечаний нет' in вывод or 'Замечание' in вывод


@pytest.mark.browser
def test_проверить_ловит_ошибку_в_сцене(мини, в_пустой, capsys):
    from mmlib import check
    _сцена(мини, "hero(s, 'нет-такого', CX, 1000, 1, [[0, 'neutral']], 0, D);")
    try:
        код = check.проверить(мини)
    except Exception as e:
        if 'Executable' in str(e):
            pytest.skip(f'нет Chromium: {e}')
        raise
    вывод = capsys.readouterr().out
    assert код == 1 and 'Ошибка' in вывод and 'нет-такого' in вывод


@pytest.mark.browser
def test_проверить_замечает_слово_вне_зоны(мини, в_пустой, capsys):
    from mmlib import check
    # слово у самого правого края кадра виден дольше полусекунды всё время бита
    _сцена(мини, "word(s, 'КРАЙ', 880, 600, 0, { size: 160, fill: LIGHT });")
    try:
        код = check.проверить(мини)
    except Exception as e:
        if 'Executable' in str(e):
            pytest.skip(f'нет Chromium: {e}')
        raise
    вывод = capsys.readouterr().out
    assert 'безопасн' in вывод and 'КРАЙ' in вывод, вывод
    assert код == 0                                                  # замечание, а не ошибка
    assert check.проверить(мини, строго=True) == 1                   # со строгим режимом замечание валит проверку


@pytest.mark.browser
def test_проверить_замечает_долгую_паузу_между_сценами(мини, в_пустой, capsys):
    from mmlib import check
    # анимация кончается через 5 секунд при голосе 1,4 с: после реплики на видео повисла бы тишина в несколько секунд
    _сцена(мини, "prog(() => {}, 0, 5);")
    try:
        check.проверить(мини)
    except Exception as e:
        if 'Executable' in str(e):
            pytest.skip(f'нет Chromium: {e}')
        raise
    вывод = capsys.readouterr().out
    assert 'тишины' in вывод and 'бит «один»' in вывод, вывод


# ---------- кадры ----------

@pytest.mark.browser
def test_кадры_делают_листы_и_список(мини, в_пустой, tmp_path):
    from mmlib import frames
    куда = tmp_path / 'review'
    try:
        frames.снять(мини, куда)
    except Exception as e:
        if 'Executable' in str(e):
            pytest.skip(f'нет Chromium: {e}')
        raise
    assert (куда / 'лист-1.png').stat().st_size > 1000
    строки = (куда / 'список.txt').read_text(encoding='utf-8').strip().splitlines()
    assert len(строки) == 3 and 'начало' in строки[0] and 'конец' in строки[2]       # три кадра на бит
    frames.снять(мини, куда, моменты='один:mid')
    assert len((куда / 'список.txt').read_text(encoding='utf-8').strip().splitlines()) == 1


@pytest.mark.browser
def test_кадры_неизвестный_бит(мини, в_пустой, tmp_path):
    from mmlib import frames
    try:
        with pytest.raises(SystemExit, match='Нет бита'):
            frames.снять(мини, tmp_path / 'review', моменты='нет-такого:1')
    except Exception as e:
        if 'Executable' in str(e):
            pytest.skip(f'нет Chromium: {e}')
        raise


@pytest.mark.browser
def test_проверить_сверяет_ролик_с_источником(мини, в_пустой, capsys):
    from mmlib import check
    (мини / 'источник.md').write_text('Кто-то написал про погоду на выходных: дождь, ветер, зонт, плед, чай и долгие разговоры за столом '
                                     'о том, как хорошо дома, когда за окном такое; остальные согласились и добавили про варенье.', encoding='utf-8')
    try:
        код = check.проверить(мини)
    except Exception as e:
        if 'Executable' in str(e):
            pytest.skip(f'нет Chromium: {e}')
        raise
    вывод = capsys.readouterr().out
    assert 'источник' in вывод and 'Привет' in вывод, вывод           # «Привет» в ролике есть, в источнике нет
    assert код == 0                                                  # замечание, а не ошибка

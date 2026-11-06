"""Снятое и собранное не попадает в коммит проекта: движок сам кладёт .gitignore там, где git иначе показал бы готовые файлы."""
import subprocess

import pytest

from mmlib import build, gitignore


def _репо(папка):
    папка.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', 'init', '-q', str(папка)], check=True)
    return папка


def _видно(репо):
    """Что git покажет в `git add -A`: пути всех неотслеживаемых файлов."""
    r = subprocess.run(['git', '-C', str(репо), '-c', 'core.quotePath=false', 'status', '--porcelain', '-uall'], capture_output=True, text=True, check=True)
    return [строка[3:] for строка in r.stdout.splitlines()]


def _готовые(папка):
    папка.mkdir(parents=True, exist_ok=True)
    for имя in ('ролик.mp4', 'ролик.srt', 'заметки.txt'):
        (папка / имя).write_bytes(b'x')
    return папка


def test_видео_и_субтитры_не_видны_git(tmp_path):
    out = _готовые(_репо(tmp_path / 'проект') / 'out')
    assert gitignore.скрыть_от_git(out, '*.mp4', '*.srt') == ['*.mp4', '*.srt']
    видно = _видно(tmp_path / 'проект')
    assert 'out/ролик.mp4' not in видно and 'out/ролик.srt' not in видно
    assert 'out/заметки.txt' in видно, 'чужое не прячем'
    assert 'out/.gitignore' in видно, 'сам .gitignore можно закоммитить: он защитит и остальных'


def test_подпапки_тоже_покрыты(tmp_path):
    out = _репо(tmp_path / 'проект') / 'out'
    _готовые(out / 'до-правки')
    gitignore.скрыть_от_git(out, '*.mp4')
    assert 'out/до-правки/ролик.mp4' not in _видно(tmp_path / 'проект')


def test_повторный_вызов_ничего_не_дописывает(tmp_path):
    out = _готовые(_репо(tmp_path / 'проект') / 'out')
    gitignore.скрыть_от_git(out, '*.mp4', '*.srt')
    текст = (out / '.gitignore').read_text(encoding='utf-8')
    assert gitignore.скрыть_от_git(out, '*.mp4', '*.srt') == []
    assert (out / '.gitignore').read_text(encoding='utf-8') == текст
    assert текст.count('*.mp4') == 1 and текст.count(gitignore.ШАПКА) == 1


def test_чужой_gitignore_сохраняется(tmp_path):
    out = _готовые(_репо(tmp_path / 'проект') / 'out')
    (out / '.gitignore').write_text('# моё\nчерновики/', encoding='utf-8')         # без перевода строки в конце
    gitignore.скрыть_от_git(out, '*.mp4')
    строки = (out / '.gitignore').read_text(encoding='utf-8').splitlines()
    assert строки[:2] == ['# моё', 'черновики/'] and '*.mp4' in строки


def test_если_человек_разрешил_коммитить_не_перебиваем(tmp_path):
    out = _готовые(_репо(tmp_path / 'проект') / 'out')
    (out / '.gitignore').write_text('!*.mp4\n', encoding='utf-8')
    assert gitignore.скрыть_от_git(out, '*.mp4') == []
    assert 'out/ролик.mp4' in _видно(tmp_path / 'проект')


def test_уже_игнорируется_ничего_не_создаёт(tmp_path):
    репо = _репо(tmp_path / 'проект')
    (репо / '.gitignore').write_text('out/\n', encoding='utf-8')
    out = _готовые(репо / 'out')
    assert gitignore.скрыть_от_git(out, '*.mp4', '*.srt') == []
    assert not (out / '.gitignore').exists(), 'репозиторий движка и подобные не получают лишних файлов'


def test_вне_репозитория_ничего_не_создаёт(tmp_path, monkeypatch):
    monkeypatch.setenv('GIT_CEILING_DIRECTORIES', str(tmp_path))                  # git не должен искать репозиторий выше
    out = _готовые(tmp_path / 'просто-папка' / 'out')
    assert gitignore.скрыть_от_git(out, '*.mp4') == []
    assert not (out / '.gitignore').exists()


def test_сборка_не_оставляет_следов_в_git(мини, tmp_path):
    проект = _репо(tmp_path / 'проект')
    build.собрать(мини, выход=проект / 'build' / 'ролик')
    assert (проект / 'build' / 'ролик' / 'index.html').exists()
    assert _видно(проект) == [], 'собранная страница игнорируется целиком, вместе с самим .gitignore'


@pytest.mark.browser
def test_кадры_проверки_не_видны_git(мини, tmp_path, monkeypatch):
    from mmlib import frames
    проект = _репо(tmp_path / 'проект')
    monkeypatch.chdir(проект)
    try:
        frames.снять(мини, проект / 'review')
    except Exception as e:
        if 'Executable' in str(e):
            pytest.skip(f'нет Chromium: {e}')
        raise
    assert (проект / 'review' / 'лист-1.png').exists()
    assert _видно(проект) == ['review/.gitignore']


@pytest.mark.browser
def test_готовое_видео_не_видно_git(мини, tmp_path):
    from mmlib import render
    проект = _репо(tmp_path / 'проект')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1.4', '-codec:a', 'libmp3lame',
                    str(мини / 'audio' / 'один.mp3')], check=True)         # loudnorm на полной тишине даёт NaN, поэтому вместо «голоса» тон
    сборка = build.собрать(мини, выход=проект / 'build' / 'ролик')
    mp4 = проект / 'out' / 'ролик.mp4'
    try:
        render.снять(сборка, mp4, fps=10, высота=480, потоков=1)           # крошечный ролик в один браузер
    except Exception as e:
        if 'Executable' in str(e):
            pytest.skip(f'нет Chromium: {e}')
        raise
    assert mp4.stat().st_size > 1000 and mp4.with_suffix('.srt').exists()
    assert _видно(проект) == ['out/.gitignore'], 'ни видео, ни субтитры, ни сборка не должны быть в `git add -A`'

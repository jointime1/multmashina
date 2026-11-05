import json

import pytest

from mmlib import build, config


def test_сборка_кладёт_всё_рядом(мини, tmp_path):
    вых = build.собрать(мини, выход=config.ROOT / 'build' / 'тест-мини')
    for f in ('index.html', 'style.js', 'data.js', 'cues.json', 'grain.png', 'engine/core.js', 'fonts/oswald.css', 'audio/один.mp3', 'sfx/whoosh.mp3'):
        assert (вых / f).exists(), f
    data = (вых / 'data.js').read_text(encoding='utf-8')
    assert '"dur": 1.4' in data and '"hi"' in data
    assert 'МИР' in data                                    # замена слова для субтитров
    assert json.loads((вых / 'cues.json').read_text(encoding='utf-8'))['один'][0][1] == 'Привет, МИР.'
    assert '<script src="episode/scenes.js">' in (вых / 'index.html').read_text(encoding='utf-8')


def test_нет_озвучки_понятная_ошибка(мини):
    (мини / 'audio' / 'timings.json').unlink()
    with pytest.raises(config.ОшибкаКонфига, match='сначала озвучьте'):
        build.собрать(мини, выход=config.ROOT / 'build' / 'тест-мини')


def test_метка_без_времени_ошибка(мини):
    (мини / 'audio' / 'timings.json').write_text(json.dumps({'один': {'dur': 1.4, 'marks': {'hi': 0.1}, 'words': [[0.1, 'Привет'], [0.7, 'мир']]}}))
    with pytest.raises(config.ОшибкаКонфига, match="метки \\['w'\\]"):
        build.собрать(мини, выход=config.ROOT / 'build' / 'тест-мини')


def test_не_стирает_чужие_папки(мини, tmp_path):
    (tmp_path / 'важное').mkdir()
    with pytest.raises(config.ОшибкаКонфига, match='очищаются только папки внутри build'):
        build.собрать(мини, выход=tmp_path / 'важное')

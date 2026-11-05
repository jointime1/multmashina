import pytest

from mmlib import config


def test_стили_загружаются_и_ключи_переводятся():
    s = config.стиль('dark-yard')
    assert s['palette']['accent'] == '#38bdf8'
    assert 'комната' in s['rooms'] and s['rooms']['комната']['lampX'] == 760
    assert s['fonts']['display_stack'].startswith('Oswald')


def test_второй_стиль_отличается():
    assert config.стиль('light-cartoon')['effects']['grain'] is False


def test_опечатка_в_ключе_даёт_понятную_ошибку(tmp_path):
    f = tmp_path / 'плохой.yaml'
    f.write_text('палитра:\n  тёмныйй: "#000"\n', encoding='utf-8')
    with pytest.raises(config.ОшибкаКонфига, match='неизвестный ключ «тёмныйй»'):
        config.стиль(f)


def test_неизвестный_раздел(tmp_path):
    f = tmp_path / 'плохой.yaml'
    f.write_text('странный: {}\n', encoding='utf-8')
    with pytest.raises(config.ОшибкаКонфига, match='неизвестный раздел'):
        config.стиль(f)


def test_герои_эпизода_добавляются_к_стилю():
    s = config.дополнить_стиль(config.стиль('dark-yard'), {'герои': {'вася': {'кожа': '#fff', 'лысый': True}}, 'комнаты': {'комната': {'свет': '#000000'}}})
    assert s['characters']['вася'] == {'skin': '#fff', 'bald': True}
    assert s['rooms']['комната']['glow'] == '#000000' and s['rooms']['комната']['lampX'] == 760   # правка поверх пресета

"""Серии и голоса героев: общий конфиг серии, реплики разных голосов в одном бите, выравнивание их громкости."""
import json
import shutil
import subprocess

import pytest

from mmlib import config
from mmlib import voice as озвучка


def _эпизод(tmp_path, серия, эпизод, нарратив):
    (tmp_path / 'серия.yaml').write_text(серия, encoding='utf-8')
    папка = tmp_path / 'часть1'
    папка.mkdir()
    (папка / 'episode.yaml').write_text(эпизод, encoding='utf-8')
    (папка / 'narration.yaml').write_text(нарратив, encoding='utf-8')
    return папка


СЕРИЯ = """
стиль: dark-yard
озвучка:
  бэкенд: edge
  темп: 1.2
  по_умолчанию: рассказчик
  голоса:
    рассказчик: {голос: ru-RU-DmitryNeural}
    олег: {голос: ru-RU-SvetlanaNeural, скорость: "+5%"}
герои:
  олег: {очки: false, доспех: "#475569"}
  камиль: {очки: true, усы: 1}
"""


def test_серия_сливает_общее_и_своё(tmp_path):
    папка = _эпизод(tmp_path, СЕРИЯ, 'название: Часть 1\nсерия: ../серия.yaml\nозвучка: {темп: 1.4}\nгерои: {серёга: {комплекция: 1.5}}\n', 'биты:\n  один: "Привет."\n')
    ep, _ = config.эпизод(папка)
    assert ep['название'] == 'Часть 1' and ep['стиль'] == 'dark-yard'
    assert ep['озвучка']['темп'] == 1.4 and ep['озвучка']['бэкенд'] == 'edge', 'значение эпизода перекрывает общее, остальное остаётся'
    assert set(ep['герои']) == {'олег', 'камиль', 'серёга'}
    assert 'серия' not in ep


def test_бит_строкой_и_списком_голосов(tmp_path):
    нар = 'биты:\n  один: "Просто текст."\n  два:\n    - олег: "[[a]]Первая реплика."\n    - камиль: "Вторая."\n'
    ep, биты = config.эпизод(_эпизод(tmp_path, СЕРИЯ, 'название: X\nсерия: ../серия.yaml\n', нар))
    assert биты['один'] == 'Просто текст.' and биты['два'] == '[[a]]Первая реплика. Вторая.'
    assert ep['_реплики']['один'] == [(None, 'Просто текст.')]
    assert ep['_реплики']['два'] == [('олег', '[[a]]Первая реплика.'), ('камиль', 'Вторая.')]


def test_бит_неправильной_формы(tmp_path):
    нар = 'биты:\n  один:\n    - олег: "Раз."\n      камиль: "Два."\n'
    with pytest.raises(config.ОшибкаКонфига, match='строка или список реплик'):
        config.эпизод(_эпизод(tmp_path, СЕРИЯ, 'название: X\nсерия: ../серия.yaml\n', нар))


def test_настройки_голоса():
    н = {'бэкенд': 'edge', 'темп': 1.2, 'по_умолчанию': 'рассказчик', 'голоса': {'рассказчик': {'голос': 'A'}, 'олег': {'голос': 'B', 'скорость': '+5%'}}}
    assert озвучка._голос(н, None) == ('рассказчик', {'бэкенд': 'edge', 'темп': 1.2, 'голос': 'A'})
    assert озвучка._голос(н, 'олег')[1] == {'бэкенд': 'edge', 'темп': 1.2, 'голос': 'B', 'скорость': '+5%'}
    with pytest.raises(config.ОшибкаКонфига, match='не описан'):
        озвучка._голос(н, 'вася')
    assert озвучка._голос({'бэкенд': 'edge', 'голос': 'X'}, None) == (None, {'бэкенд': 'edge', 'голос': 'X'}), 'без голосов всё как раньше'


def test_склейка_выравнивает_громкость(tmp_path):
    np = pytest.importorskip('numpy')
    sf = pytest.importorskip('soundfile')
    sr = 24000
    t = np.arange(sr) / sr
    sf.write(str(tmp_path / 'тихий.wav'), (.05 * np.sin(2 * np.pi * 200 * t)).astype('float32'), sr)
    sf.write(str(tmp_path / 'громкий.wav'), (.6 * np.sin(2 * np.pi * 120 * t)).astype('float32'), sr)
    озвучка._склеить([tmp_path / 'тихий.wav', tmp_path / 'громкий.wav'], tmp_path / 'бит.wav')
    x, _ = sf.read(str(tmp_path / 'бит.wav'))
    rms = lambda a: float(np.sqrt(np.mean(a ** 2)))
    первая, вторая = x[:sr], x[-sr:]
    assert .6 < rms(первая) / rms(вторая) < 1.6, 'громкость реплик разных голосов должна быть сопоставимой'
    assert len(x) > 2 * sr, 'между репликами есть пауза'


def test_озвучка_нескольких_голосов_склеивает_и_кэширует(tmp_path, monkeypatch):
    np = pytest.importorskip('numpy')
    sf = pytest.importorskip('soundfile')
    if not shutil.which('ffmpeg'):
        pytest.skip('нужен ffmpeg')
    вызовы = []

    class Ненастоящий:
        def __init__(self, настройки, папка):
            self.н = настройки
            self.тон = настройки['тон']

        def синтез(self, текст, wav):
            вызовы.append((self.тон, текст))
            t = np.arange(24000) / 24000
            sf.write(str(wav), (.3 * np.sin(2 * np.pi * self.тон * t) * np.linspace(1, 0, t.size) ** 2).astype('float32'), 24000)   # затухает, как настоящая речь

    class Слова:
        def __init__(self, модель): pass
        def слова(self, mp3, текст, длит): return [[0.0, 'а']], len(текст.split())

    монтаж = {'ненастоящий': Ненастоящий}
    monkeypatch.setattr(озвучка, 'БЭКЕНДЫ', монтаж)
    monkeypatch.setattr(озвучка, 'Выравнивание', Слова)
    monkeypatch.setattr(озвучка, 'время_меток', lambda чистый, метки, слова: {м: .1 for м in метки})
    серия = 'озвучка:\n  бэкенд: ненастоящий\n  по_умолчанию: ведущий\n  голоса:\n    ведущий: {тон: 100}\n    олег: {тон: 300}\n'
    папка = _эпизод(tmp_path, серия, 'название: X\nсерия: ../серия.yaml\n', 'биты:\n  один:\n    - ведущий: "[[a]]Раз."\n    - олег: "Два."\n')
    озвучка.озвучить(папка)
    assert вызовы == [(100, 'Раз.'), (300, 'Два.')]
    тайминги = json.loads((папка / 'audio' / 'timings.json').read_text(encoding='utf-8'))
    assert 'a' in тайминги['один']['marks'] and тайминги['один']['dur'] > 1.5, 'в одном бите склеены две реплики'
    озвучка.озвучить(папка)
    assert len(вызовы) == 2, 'неизменённые реплики не озвучиваются заново'
    (папка / 'narration.yaml').write_text('биты:\n  один:\n    - ведущий: "[[a]]Раз."\n    - олег: "Три."\n', encoding='utf-8')
    озвучка.озвучить(папка)
    assert вызовы[2:] == [(300, 'Три.')], 'изменилась только вторая реплика — озвучивается только она'


def test_обрывок_озвучивается_повторно_с_другим_seed(tmp_path, monkeypatch):
    np = pytest.importorskip('numpy')
    sf = pytest.importorskip('soundfile')
    if not shutil.which('ffmpeg'):
        pytest.skip('нужен ffmpeg')
    seeds = []

    class Капризный:
        def __init__(self, настройки, папка):
            self.н = настройки

        def синтез(self, текст, wav):
            seeds.append(self.н['seed'])
            длит = .05 if self.н['seed'] < 13 else 1.2                    # первые попытки — обрывок, потом нормальная речь
            t = np.arange(int(24000 * длит)) / 24000
            sf.write(str(wav), (.3 * np.sin(2 * np.pi * 150 * t) * np.linspace(1, 0, max(t.size, 1)) ** 2).astype('float32'), 24000)

    class Слова:
        def __init__(self, модель): pass
        def слова(self, mp3, текст, длит): return [[0.0, 'а']], len(текст.split())

    monkeypatch.setattr(озвучка, 'БЭКЕНДЫ', {'капризный': Капризный})
    monkeypatch.setattr(озвучка, 'Выравнивание', Слова)
    monkeypatch.setattr(озвучка, 'время_меток', lambda чистый, метки, слова: {})
    папка = _эпизод(tmp_path, 'озвучка: {бэкенд: капризный, seed: 11}\n', 'название: X\nсерия: ../серия.yaml\n', 'биты:\n  один: "Раз два."\n')
    озвучка.озвучить(папка)
    assert seeds == [11, 12, 13], 'обрывки перезаписываются другим seed, пока не получится речь нормальной длины'


def test_охрана_памяти(monkeypatch):
    from mmlib import mem
    monkeypatch.delenv('MM_IGNORE_MEMORY', raising=False)
    monkeypatch.setattr(mem, 'доступно_гб', lambda: 3.0)
    with pytest.raises(MemoryError, match='Мало свободной памяти'):
        mem.проверить(5, 'модель')
    mem.проверить(2, 'модель')                                   # хватает — молча
    monkeypatch.setenv('MM_IGNORE_MEMORY', '1')
    mem.проверить(50, 'модель')                                  # проверку можно отключить
    monkeypatch.setattr(mem, 'доступно_гб', lambda: None)
    monkeypatch.delenv('MM_IGNORE_MEMORY')
    mem.проверить(50, 'модель')                                  # не смогли узнать — не мешаем


def test_обрыв_на_полуслове_виден_по_громкому_хвосту(tmp_path):
    np = pytest.importorskip('numpy')
    sf = pytest.importorskip('soundfile')
    sr = 24000
    t = np.arange(sr * 2) / sr
    речь = (.3 * np.sin(2 * np.pi * 150 * t)).astype('float32')
    затухание = речь * np.linspace(1, 0, речь.size).astype('float32') ** 2
    sf.write(str(tmp_path / 'целая.wav'), затухание, sr)                        # речь затухает: хвост тихий
    sf.write(str(tmp_path / 'обрыв.wav'), речь, sr)                              # звук резко кончается на полной громкости
    assert not озвучка._хвост_обрезан(tmp_path / 'целая.wav')
    assert озвучка._хвост_обрезан(tmp_path / 'обрыв.wav')


def test_неразобранная_речь_перезаписывается(tmp_path, monkeypatch):
    """Длина нормальная, но Whisper разобрал мало слов (речь невнятная или оборвана) — реплику озвучивают заново с другим seed."""
    np = pytest.importorskip('numpy')
    sf = pytest.importorskip('soundfile')
    if not shutil.which('ffmpeg'):
        pytest.skip('нужен ffmpeg')
    seeds = []

    class Мямлит:
        def __init__(self, настройки, папка):
            self.н = настройки

        def синтез(self, текст, wav):
            seeds.append(self.н['seed'])
            t = np.arange(int(24000 * .5 * len(текст.split()))) / 24000          # 0,5 с на слово — по длине всё в порядке
            sf.write(str(wav), (.3 * np.sin(2 * np.pi * 150 * t) * np.linspace(1, 0, t.size) ** 2).astype('float32'), 24000)

    class Слова:
        def __init__(self, модель): pass
        def слова(self, mp3, текст, длит):
            число = len(текст.split())
            return [[0.0, 'а']] * число, (число if seeds[-1] >= 13 else 1)       # первые попытки: распознано 1 слово

    monkeypatch.setattr(озвучка, 'БЭКЕНДЫ', {'мямлит': Мямлит})
    monkeypatch.setattr(озвучка, 'Выравнивание', Слова)
    monkeypatch.setattr(озвучка, 'время_меток', lambda чистый, метки, слова: {})
    папка = _эпизод(tmp_path, 'озвучка: {бэкенд: мямлит, seed: 11}\n', 'название: X\nсерия: ../серия.yaml\n', 'биты:\n  один: "Раз два три четыре."\n')
    озвучка.озвучить(папка)
    assert seeds == [11, 12, 13], 'пока Whisper не разобрал слова, реплика озвучивается с новым seed'


def test_текст_эталона_должен_соответствовать_записи(tmp_path):
    """Незаквоченный текст в YAML-скобках обрывается на запятой: клон получает обрубок и «заикается». Это ловится до загрузки модели."""
    np = pytest.importorskip('numpy')
    sf = pytest.importorskip('soundfile')
    from mmlib.voice.backends import QwenКлон, ОшибкаОзвучки
    sf.write(str(tmp_path / 'ref.wav'), np.zeros(24000 * 13, dtype='float32'), 24000)            # 13 секунд записи
    with pytest.raises(ОшибкаОзвучки, match='не соответствует записи'):
        QwenКлон({'эталон': 'ref.wav', 'текст_эталона': 'Триста сорок семь отказов'}, tmp_path)   # а в тексте 4 слова

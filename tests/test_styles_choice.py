"""Выбор стиля: у каждого готового стиля есть описание, команда `стили` показывает таблицу, а витрина снимает кадры каждого стиля одним взглядом."""
import pytest

from mmlib import config, styles


def test_список_описывает_каждый_готовый_стиль():
    список = styles.список()
    файлы = sorted(f.stem for f in (config.ROOT / 'styles').glob('*.yaml'))
    assert [с['имя'] for с in список] == файлы
    for с in список:
        assert с['название'] and len(с['описание']) > 40, f'у стиля {с["имя"]} нет описания в комментарии файла'
        assert с['персонаж'] and с['характер'], с


def test_список_знает_школу_стиля():
    по_имени = {с['имя']: с for с in styles.список()}
    assert по_имени['classic']['персонаж'] == 'классика' and по_имени['classic']['характер'] == 'пружина'
    assert по_имени['cutout']['персонаж'] == 'вырезка' and по_имени['cutout']['характер'] == 'механика'
    assert по_имени['dark-yard']['персонаж'] == 'обычный' and по_имени['dark-yard']['характер'] == 'плавный'


def test_команда_стили_печатает_все_стили(capsys):
    styles.показать()
    вывод = capsys.readouterr().out
    for с in styles.список():
        assert с['имя'] in вывод and с['название'] in вывод


def test_скилл_просит_выбрать_стиль_и_показывает_витрину():
    текст = (config.ROOT / '.claude' / 'skills' / 'multmashina' / 'SKILL.md').read_text(encoding='utf-8')
    assert 'стили' in текст and 'в каком стиле' in текст.lower(), 'скилл должен предлагать пользователю выбрать стиль'
    assert 'docs/previews' in текст


@pytest.mark.browser
def test_витрина_снимает_кадры_стиля_в_одну_полосу(tmp_path):
    файл = styles.превью(tmp_path, ['classic'])[0]
    assert файл.exists() and файл.stat().st_size > 15000, файл
    assert (tmp_path / 'styles.jpg').exists(), 'общая витрина всех снятых стилей'

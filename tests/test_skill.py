"""Скилл для ИИ-агента не должен расходиться с инструментом: ссылки живы, все команды описаны, setup.sh находит репозиторий."""
import os
import re
import subprocess
from pathlib import Path

import pytest

КОРЕНЬ = Path(__file__).resolve().parents[1]
СКИЛЛ = КОРЕНЬ / '.claude' / 'skills' / 'multmashina'
ФАЙЛЫ = [СКИЛЛ / 'SKILL.md', *sorted((СКИЛЛ / 'references').glob('*.md'))]
# служебная команда для тех, кто правит сам движок (генерация звуков и зерна): агенту для роликов не нужна
НЕ_ДЛЯ_АГЕНТА = {'ассеты'}


def _текст():
    return '\n'.join(f.read_text(encoding='utf-8') for f in ФАЙЛЫ)


def test_шапка_скилла():
    t = (СКИЛЛ / 'SKILL.md').read_text(encoding='utf-8')
    m = re.match(r'---\nname: (\S+)\ndescription: (.+)\n---\n', t)
    assert m, 'в SKILL.md нужна шапка name/description'
    assert m.group(1) == 'multmashina' and СКИЛЛ.name == m.group(1)
    assert len(m.group(2)) > 100, 'description должен перечислять, когда включать скилл'
    for фраза in ('рилс', 'мультик'):
        assert фраза in m.group(2).lower(), f'в description нет «{фраза}»: агент не узнает, когда включать'


@pytest.mark.parametrize('файл', ФАЙЛЫ, ids=lambda f: f.name)
def test_ссылки_ведут_к_файлам(файл):
    for цель in re.findall(r'\]\(([^)#\s]+)\)', файл.read_text(encoding='utf-8')):
        if цель.startswith(('http://', 'https://')):
            continue
        assert (файл.parent / цель).exists(), f'{файл.name}: ссылка на несуществующий файл {цель}'


def test_все_команды_описаны():
    import argparse
    import mm
    команды = next(a for a in mm.парсер()._actions if isinstance(a, argparse._SubParsersAction)).choices
    assert {'окружение', 'новый', 'проверить', 'кадры', 'озвучить', 'снять'} <= set(команды)
    t = _текст()
    for к in set(команды) - НЕ_ДЛЯ_АГЕНТА:
        assert any(форма in t for форма in (f'`{к}', f'$MM {к}', f'mm.py {к}')), f'команда «{к}» нигде не описана в скилле'


def test_скилл_называет_справочники_которые_есть():
    for ссылка in re.findall(r'\$MM_HOME/((?:docs|examples)/[\w./-]+)', _текст()):
        assert (КОРЕНЬ / ссылка.rstrip('/')).exists(), f'скилл ссылается на {ссылка}, а его нет'


def test_setup_печатает_корень_репозитория():
    sh = СКИЛЛ / 'setup.sh'
    assert os.access(sh, os.X_OK), 'setup.sh должен быть исполняемым'
    r = subprocess.run(['bash', str(sh)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert Path(r.stdout.strip()).resolve() == КОРЕНЬ.resolve()


def test_setup_находит_репозиторий_через_ссылку_на_скилл(tmp_path):
    """Проект может подключить живой скилл ссылкой: иначе setup.sh уйдёт в старый клон и правки движка до роликов не дойдут."""
    ссылка = tmp_path / ".claude" / "skills" / "multmashina"
    ссылка.parent.mkdir(parents=True)
    ссылка.symlink_to(СКИЛЛ)
    среда = {k: v for k, v in os.environ.items() if k != "MULTMASHINA_HOME"}
    r = subprocess.run(["bash", str(ссылка / "setup.sh")], capture_output=True, text=True, timeout=60, env=среда)
    assert Path(r.stdout.strip()).resolve() == КОРЕНЬ.resolve(), r.stdout + r.stderr


def test_скилл_не_предписывает_одну_раскладку():
    """Жёсткая привязка головы к y≈1000 в инструкции и сделала все ролики одинаковыми."""
    assert "y≈1000" not in (СКИЛЛ / "SKILL.md").read_text(encoding="utf-8")
    assert "ставьте на y" not in (КОРЕНЬ / "docs" / "scenes.md").read_text(encoding="utf-8")


def test_скилл_требует_раскадровку_до_сцен():
    t = (СКИЛЛ / "SKILL.md").read_text(encoding="utf-8")
    assert "раскадровк" in t.lower() and t.lower().index("раскадровк") < t.index("scenes.js")


def test_mm_sh_запускает_команды_из_любой_папки(tmp_path):
    sh = СКИЛЛ / 'mm.sh'
    assert os.access(sh, os.X_OK), 'mm.sh должен быть исполняемым'
    r = subprocess.run([str(sh), '+voice', 'окружение'], cwd=tmp_path, capture_output=True, text=True, timeout=300)
    assert 'Озвучка' in r.stdout and 'ffmpeg' in r.stdout, r.stdout + r.stderr


def test_в_скилле_нет_переменной_с_командой_uv():
    """В zsh переменная MM="uv run …" не разбивается на слова: скилл должен ходить через mm.sh."""
    assert not re.search(r'MM="uv run', _текст()), 'не определяйте MM как строку «uv run …»'
    assert 'mm.sh' in (СКИЛЛ / 'SKILL.md').read_text(encoding='utf-8')


def test_файлы_для_агентов_на_месте():
    assert '@../AGENTS.md' in (КОРЕНЬ / '.claude' / 'CLAUDE.md').read_text(encoding='utf-8')
    assert '.claude/skills/multmashina/SKILL.md' in (КОРЕНЬ / 'AGENTS.md').read_text(encoding='utf-8')
    команда = (КОРЕНЬ / '.opencode' / 'commands' / 'multmashina.md').read_text(encoding='utf-8')
    assert '$ARGUMENTS' in команда and (КОРЕНЬ / '.claude/skills/multmashina/SKILL.md').exists()


def test_скилл_велит_делать_ролик_по_материалу_из_источника():
    """Сценарий по чужому материалу растёт из него, а не из привычек автора: правило есть везде, где агент принимает решения."""
    скилл = (СКИЛЛ / 'SKILL.md').read_text(encoding='utf-8')
    письмо = (СКИЛЛ / 'references' / 'writing.md').read_text(encoding='utf-8')
    работа = (СКИЛЛ / 'references' / 'workflow.md').read_text(encoding='utf-8')
    for имя, текст in (('SKILL.md', скилл), ('writing.md', письмо), ('workflow.md', работа)):
        assert 'источник.md' in текст, f'{имя}: не сказано про источник.md'
    assert 'клише' in письмо and 'Откуда' in письмо, 'writing.md: нет правила про выдуманные клише темы и столбца «Откуда» в раскадровке'
    assert 'клише' in скилл, 'SKILL.md: нет запрета на шутки «из головы»'

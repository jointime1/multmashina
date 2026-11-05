"""Память: тяжёлые шаги (нейросеть озвучки, параллельные браузеры) не должны загонять компьютер в своп, поэтому перед ними смотрим, сколько её доступно."""
import os
import re
import subprocess
import sys


def доступно_гб():
    """Сколько гигабайт можно занять, не уходя в своп (с учётом того, что система освободит сама); None, если узнать не вышло."""
    try:
        if sys.platform == 'darwin':
            # memory_pressure врёт про «свободно 90%»: сюда попадает и память виртуальных машин (Docker). Считаем сами: свободные страницы
            # + файловый кэш + purgeable — то, что система отдаст без свопа; анонимная (занятая программами) память не в счёт
            вывод = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=5).stdout
            страница = int(re.search(r'page size of (\d+) bytes', вывод).group(1))
            число = lambda имя: int(re.search(rf'{имя}:\s*(\d+)', вывод).group(1))
            return sum(число(n) for n in ('Pages free', 'Pages speculative', 'File-backed pages', 'Pages purgeable')) * страница / 2 ** 30
        if sys.platform.startswith('linux'):
            return int(re.search(r'MemAvailable:\s*(\d+) kB', open('/proc/meminfo').read()).group(1)) / 2 ** 20
    except Exception:
        return None
    return None


def проверить(нужно_гб, что):
    """Бросает ошибку, если памяти заведомо мало; MM_IGNORE_MEMORY=1 отключает проверку."""
    if os.environ.get('MM_IGNORE_MEMORY'):
        return
    есть = доступно_гб()
    if есть is not None and есть < нужно_гб:
        raise MemoryError(f'Мало свободной памяти: доступно ≈{есть:.0f} ГБ, для «{что}» нужно ≈{нужно_гб:.0f} ГБ. '
                          'Закройте тяжёлые программы (Docker, браузеры) и повторите; MM_IGNORE_MEMORY=1 отключает проверку на свой страх и риск')

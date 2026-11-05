#!/usr/bin/env python3
"""Мультмашина: универсальный генератор мультиков и рилсов. Команды:

  python scripts/mm.py ассеты                        сгенерировать звуковые эффекты (assets/sfx) и зерно (assets/grain.png)
  python scripts/mm.py озвучить examples/<эпизод>   озвучить биты выбранным голосом и выровнять слова
  python scripts/mm.py собрать examples/<эпизод>    собрать автономную страницу в build/<эпизод>
  python scripts/mm.py смотреть examples/<эпизод>   собрать и открыть предпросмотр в браузере (со звуком)
  python scripts/mm.py снять examples/<эпизод>      собрать и снять MP4 (1080×1920) + субтитры .srt
"""
import argparse
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mmlib import build, config


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='команда', required=True)
    sub.add_parser('ассеты')
    for имя in ('озвучить', 'собрать', 'смотреть', 'снять'):
        s = sub.add_parser(имя)
        s.add_argument('эпизод', help='папка эпизода, например examples/jobturbo')
        if имя in ('собрать', 'смотреть', 'снять'):
            s.add_argument('--стиль', help='стиль из styles/ (или путь к .yaml) вместо указанного в эпизоде')
        if имя == 'озвучить':
            s.add_argument('--голос', help='бэкенд озвучки из episode.yaml (по умолчанию тот, что указан в эпизоде)')
            s.add_argument('--только', help='озвучить только эти биты через запятую')
        if имя == 'смотреть':
            s.add_argument('--порт', type=int, default=8765)
        if имя == 'снять':
            s.add_argument('--выход', help='куда сохранить MP4 (по умолчанию out/<эпизод>.mp4)')
            s.add_argument('--fps', type=int, default=30)
            s.add_argument('--потоков', type=int, default=4, help='сколько браузеров снимают кадры одновременно')
            s.add_argument('--кодек', default='libx264', choices=['libx264', 'videotoolbox'])
    a = p.parse_args()
    try:
        if a.команда == 'ассеты':
            from mmlib import assets
            assets.всё(config.ROOT)
        elif a.команда == 'озвучить':
            from mmlib.voice import озвучить
            озвучить(a.эпизод, a.голос, a.только)
        elif a.команда == 'собрать':
            print('Собрано:', build.собрать(a.эпизод, стиль_имя=a.стиль))
        elif a.команда == 'смотреть':
            from mmlib import serve
            папка = build.собрать(a.эпизод, стиль_имя=a.стиль)
            srv, порт = serve.запустить(папка, a.порт)
            url = f'http://127.0.0.1:{порт}/index.html'
            print(f'Предпросмотр: {url}  (Ctrl+C — остановить)')
            webbrowser.open(url)
            try:
                import time
                while True:
                    time.sleep(3600)
            except KeyboardInterrupt:
                srv.shutdown()
        elif a.команда == 'снять':
            from mmlib import render
            папка = build.собрать(a.эпизод, стиль_имя=a.стиль)
            выход = a.выход or config.ROOT / 'out' / (Path(a.эпизод).resolve().name + (f'--{Path(a.стиль).stem}' if a.стиль else '') + '.mp4')
            render.снять(папка, выход, fps=a.fps, потоков=a.потоков, кодек=a.кодек)
    except config.ОшибкаКонфига as e:
        sys.exit(f'Ошибка: {e}')


if __name__ == '__main__':
    main()

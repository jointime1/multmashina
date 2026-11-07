#!/usr/bin/env python3
"""Мультмашина: универсальный генератор мультиков и рилсов. Команды:

  python scripts/mm.py окружение                    что есть на машине: ffmpeg, Chromium, голосовые бэкенды (с чего начинать агенту)
  python scripts/mm.py стили                        какие есть стили, чем отличаются (персонаж, движение); --превью снимает витрину docs/previews
  python scripts/mm.py новый examples/<имя>         новый эпизод из шаблона (3 бита, герой, комната, субтитры)
  python scripts/mm.py проверить examples/<эпизод>  ошибки в сценах, слова вне безопасной зоны, длины и темп речи
  python scripts/mm.py кадры examples/<эпизод>      контактные листы кадров: увидеть свою работу глазами
  python scripts/mm.py ассеты                        сгенерировать звуковые эффекты (assets/sfx) и зерно (assets/grain.png)
  python scripts/mm.py образец voices/имя ...      образцы голоса по описанию (несколько вариантов) — выбрать тембр для клона
  python scripts/mm.py озвучить examples/<эпизод>   озвучить биты выбранным голосом (или голосами героев) и выровнять слова
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


def парсер():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='команда', required=True)
    sub.add_parser('ассеты')
    sub.add_parser('окружение')
    st = sub.add_parser('стили'); st.add_argument('--превью', nargs='?', const='docs/previews', help='снять витрину: полоса кадров на стиль и общий лист (по умолчанию docs/previews)')
    st.add_argument('--только', help='снять витрину только этих стилей через запятую')
    ob = sub.add_parser('образец'); ob.add_argument('база', help='путь без расширения, например voices/олег'); ob.add_argument('--описание', required=True, help='голос словами, лучше по-английски')
    ob.add_argument('--текст', required=True, help='что произнести (10–15 секунд речи; это же текст_эталона)'); ob.add_argument('--seeds', default='1,2,3', help='варианты, через запятую')
    n = sub.add_parser('новый'); n.add_argument('эпизод', help='куда создать, например examples/мой-ролик')
    n.add_argument('--стиль', default='dark-yard'); n.add_argument('--название')
    pr = sub.add_parser('проверить'); pr.add_argument('эпизод'); pr.add_argument('--стиль'); pr.add_argument('--строго', action='store_true', help='замечания тоже считать ошибкой')
    kd = sub.add_parser('кадры'); kd.add_argument('эпизод'); kd.add_argument('--стиль'); kd.add_argument('--куда', help='папка для листов (по умолчанию review/<эпизод>)')
    kd.add_argument('--моменты', help='свои моменты: hook:0.3,offer:mid,outro:end')
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
    return p


def main():
    a = парсер().parse_args()
    try:
        if a.команда == 'окружение':
            from mmlib import env
            sys.exit(env.проверить())
        elif a.команда == 'стили':
            from mmlib import styles
            if a.превью:
                for f in styles.превью(a.превью, a.только.split(',') if a.только else None):
                    print('Снято:', f)
                print(f'Общий лист: {a.превью}/styles.jpg')
            else:
                styles.показать()
        elif a.команда == 'образец':
            from mmlib.voice import sample
            sample.сделать(a.база, a.описание, a.текст, [int(x) for x in a.seeds.split(',')])
        elif a.команда == 'новый':
            from mmlib import new
            new.создать(a.эпизод, a.стиль, a.название)
        elif a.команда == 'проверить':
            from mmlib import check
            sys.exit(check.проверить(a.эпизод, a.стиль, a.строго))
        elif a.команда == 'кадры':
            from mmlib import frames
            frames.снять(a.эпизод, a.куда, a.моменты, a.стиль)
        elif a.команда == 'ассеты':
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
            выход = a.выход or Path.cwd() / 'out' / (Path(a.эпизод).resolve().name + (f'--{Path(a.стиль).stem}' if a.стиль else '') + '.mp4')
            render.снять(папка, выход, fps=a.fps, потоков=a.потоков, кодек=a.кодек)
    except config.ОшибкаКонфига as e:
        sys.exit(f'Ошибка: {e}')


if __name__ == '__main__':
    main()

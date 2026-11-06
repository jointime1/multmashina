"""Озвучка эпизода: реплики из narration.yaml → audio/<бит>.mp3 и audio/timings.json (длительность, метки, слова со временем)."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .. import config, gitignore
from .align import Выравнивание, разобрать_метки, время_меток
from .backends import БЭКЕНДЫ, ОшибкаОзвучки


def _длительность(f):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(f)], capture_output=True, text=True, check=True)
    return round(float(r.stdout), 3)


def _длина_нормальная(wav, слов):
    """Нейросеть иногда выдаёт обрывок в 0,1 с или бесконечную болтовню на минуту. Сырая речь — примерно 0,5 с на слово (потом она ускоряется); короче 0,3 или длиннее 1,2 — брак."""
    if слов < 1:
        return True
    return .3 <= _длительность(wav) / слов <= 1.2


def _хвост_обрезан(wav):
    """Речь, оборванная на полуслове, кончается громко: у нормальной записи в последние 60 мс уже тихо (затухание или пауза)."""
    import numpy as np
    import soundfile as sf
    x, sr = sf.read(str(wav), dtype='float32')
    x = x.reshape(-1) if x.ndim == 1 else x.mean(axis=1)
    if x.size < sr * .3:
        return True
    речь = np.abs(x)[np.abs(x) > .02]
    if not речь.size:
        return True
    n = int(sr * .06)
    return float(np.sqrt(np.mean(x[-n:] ** 2))) > .5 * float(np.sqrt(np.mean(речь ** 2)))


def _озвучить_сегмент(движок, текст, слов, wav, seed0, выравнивание, метка):
    """Одна реплика: до 8 попыток с разными seed. Попытка годна, если длина нормальна, хвост не оборван и Whisper разобрал почти все слова.
    Если идеальной нет — берётся лучшая по этим признакам; если нет даже сносной по длине — ошибка."""
    лучший, лучший_балл, пробная = None, -1.0, wav.with_suffix('.try.wav')
    for попытка in range(8):
        движок.н['seed'] = seed0 + попытка
        print(f'{метка}: озвучиваю…' + (f' (попытка {попытка + 1}, seed {seed0 + попытка})' if попытка else ''), flush=True)
        движок.синтез(текст, пробная)
        длина_ок, хвост_ок = _длина_нормальная(пробная, слов), not _хвост_обрезан(пробная)
        доля = 0.0
        if длина_ок:
            _, услышано = выравнивание.слова(пробная, текст, _длительность(пробная))
            доля = min(1.0, услышано / max(1, слов))
        балл = доля + (.3 if хвост_ок else 0) + (.3 if длина_ок else 0)
        if not (длина_ок and хвост_ок and доля >= (.9 if слов > 3 else .66)):
            print(f'    брак: {_длительность(пробная) / max(1, слов):.2f} с/слово, хвост {"цел" if хвост_ок else "оборван"}, распознано {доля:.0%}', flush=True)
        if балл > лучший_балл:
            лучший_балл = балл
            shutil.move(str(пробная), str(wav))
            лучший = (длина_ок, хвост_ок, доля)
        if длина_ок and хвост_ок and доля >= (.9 if слов > 3 else .66):
            break
    if пробная.exists():
        пробная.unlink()
    if not лучший[0]:
        raise ОшибкаОзвучки(f'«{текст[:40]}…»: за 8 попыток нейросеть не выдала речь нормальной длины. Перепишите реплику или смените голос')
    if not (лучший[1] and лучший[2] >= .8):
        print(f'  ⚠ {метка}: лучшая из попыток всё ещё сомнительна (распознано {лучший[2]:.0%} слов, хвост {"цел" if лучший[1] else "оборван"})', flush=True)


def _обработать(сырой, mp3, темп, lufs):
    """Паузы длиннее ~0,2 с сжимаются, речь ускоряется (высота не меняется), компрессор, громкость; на выходе mp3."""
    цепочка = ','.join(['highpass=f=60', 'silenceremove=stop_periods=-1:stop_duration=0.22:stop_threshold=-42dB:stop_silence=0.15',
                        f'atempo={темп:.4f}', 'acompressor=threshold=-24dB:ratio=2.5:attack=8:release=120', 'alimiter=limit=0.92',
                        f'loudnorm=I={lufs}:TP=-1.5:LRA=11'])
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(сырой), '-af', цепочка, '-ar', '44100', '-ac', '1', '-codec:a', 'libmp3lame', '-b:a', '128k', str(mp3)], check=True)


def _голос(н, имя):
    """Настройки голоса: общие настройки озвучки + то, что задано для этого голоса в озвучка → голоса (имя None — голос по умолчанию)."""
    общие = {k: v for k, v in н.items() if k not in ('голоса', 'по_умолчанию')}
    имя = имя or н.get('по_умолчанию')
    if имя is None:
        return None, общие
    голоса = н.get('голоса') or {}
    if имя not in голоса:
        raise config.ОшибкаКонфига(f'Голос «{имя}» не описан в episode.yaml → озвучка → голоса. Описаны: {", ".join(голоса) or "(пусто)"}')
    return имя, {**общие, **голоса[имя]}


def _склеить(wavs, выход, пауза=.22, цель=.07):
    """Реплики разных голосов в одном бите: громкость каждой выравнивается (по речи, без пауз), между ними короткая тишина."""
    import numpy as np
    import soundfile as sf
    куски, sr = [], None
    for w in wavs:
        x, sr_w = sf.read(str(w), dtype='float32')
        x = x.reshape(-1) if x.ndim == 1 else x.mean(axis=1)
        sr = sr or sr_w
        голос = np.abs(x)[np.abs(x) > .02]
        rms = float(np.sqrt(np.mean(голос ** 2))) if голос.size else цель
        куски += [np.clip(x * min(8.0, max(.1, цель / max(rms, 1e-4))), -.98, .98), np.zeros(int(sr * пауза), dtype='float32')]
    sf.write(str(выход), np.concatenate(куски[:-1]), sr)


def озвучить(папка, бэкенд=None, только=None):
    папка = Path(папка).resolve()
    ep, биты = config.эпизод(папка)
    н = ep.get('озвучка', {})
    имя = бэкенд or н.get('бэкенд')
    if имя not in БЭКЕНДЫ:
        raise config.ОшибкаКонфига(f'Бэкенд озвучки «{имя}» неизвестен. Доступные: {", ".join(БЭКЕНДЫ)}; задаётся в episode.yaml → озвучка → бэкенд')
    выбор = set(только.split(',')) if только else None
    аудио, сырые = папка / 'audio', папка / 'audio' / 'raw'
    сырые.mkdir(parents=True, exist_ok=True)
    gitignore.скрыть_от_git(сырые, '*')                              # сырые дорожки воспроизводятся командой «озвучить»; в коммит идут готовые mp3 и timings.json
    tf = аудио / 'timings.json'
    тайминги = json.loads(tf.read_text(encoding='utf-8')) if tf.exists() else {}
    тайминги = {k: v for k, v in тайминги.items() if k in биты}      # убранные из сценария биты уходят и отсюда
    темп, lufs = float(н.get('темп', 1.0)), float(н.get('громкость', -14))
    движки = {}                                                      # по одному на голос; модель Qwen внутри общая
    try:
        выравнивание = Выравнивание(н.get('whisper', 'small'))
        for id_, сырой_текст in биты.items():
            if выбор and id_ not in выбор:
                continue
            чистый, метки = разобрать_метки(сырой_текст)
            сегменты = ep['_реплики'][id_]
            файлы = []
            for k, (голос, текст) in enumerate(сегменты):
                имя_голоса, настройки = _голос(н, голос)
                чист_сег = разобрать_метки(текст)[0]
                ключ = hashlib.sha1(f'{имя}|{json.dumps(настройки, ensure_ascii=False, sort_keys=True)}|{чист_сег}'.encode()).hexdigest()
                wav, kf = (сырые / f'{id_}.wav', сырые / f'{id_}.key') if len(сегменты) == 1 else (сырые / f'{id_}.{k}.wav', сырые / f'{id_}.{k}.key')
                слов = len(re.findall(r"[\w'’-]+", чист_сег))
                if not (wav.exists() and kf.exists() and kf.read_text() == ключ and _длина_нормальная(wav, слов)):
                    if имя_голоса not in движки:
                        движки[имя_голоса] = БЭКЕНДЫ[имя](настройки, папка)
                    метка = "" if len(сегменты) == 1 else f" [{k + 1}/{len(сегменты)}, {имя_голоса or 'голос по умолчанию'}]"
                    _озвучить_сегмент(движки[имя_голоса], чист_сег, слов, wav, int(настройки.get('seed', 11)), выравнивание, f'{id_}{метка}')
                    kf.write_text(ключ)
                файлы.append(wav)
            wav = файлы[0]
            if len(файлы) > 1:
                wav = сырые / f'{id_}.beat.wav'
                _склеить(файлы, wav)
            mp3 = аудио / f'{id_}.mp3'
            _обработать(wav, mp3, темп, lufs)
            длит = _длительность(mp3)
            слова, услышано = выравнивание.слова(mp3, чистый, длит)
            тайминги[id_] = {'dur': длит, 'marks': время_меток(чистый, метки, слова), 'words': слова}
            print(f'{id_}: {длит} с, слов {len(слова)}, услышано {услышано}, метки {тайминги[id_]["marks"]}', flush=True)
            if слова and услышано < .85 * len(слова):
                print(f'  ⚠ {id_}: распознано {услышано} слов из {len(слова)} — возможно, речь оборвана или невнятна; послушайте бит или озвучьте заново (--только {id_})', flush=True)
    except (ОшибкаОзвучки, ValueError) as e:
        sys.exit(f'Ошибка озвучки: {e}')
    порядок = {k: тайминги[k] for k in биты if k in тайминги}
    tf.write_text(json.dumps(порядок, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Готово: {tf}')

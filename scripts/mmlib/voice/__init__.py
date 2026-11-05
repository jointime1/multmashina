"""Озвучка эпизода: реплики из narration.yaml → audio/<бит>.mp3 и audio/timings.json (длительность, метки, слова со временем)."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from .. import config
from .align import Выравнивание, разобрать_метки, время_меток
from .backends import БЭКЕНДЫ, ОшибкаОзвучки


def _длительность(f):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(f)], capture_output=True, text=True, check=True)
    return round(float(r.stdout), 3)


def _обработать(сырой, mp3, темп, lufs):
    """Паузы длиннее ~0,2 с сжимаются, речь ускоряется (высота не меняется), компрессор, громкость; на выходе mp3."""
    цепочка = ','.join(['highpass=f=60', 'silenceremove=stop_periods=-1:stop_duration=0.22:stop_threshold=-42dB:stop_silence=0.15',
                        f'atempo={темп:.4f}', 'acompressor=threshold=-24dB:ratio=2.5:attack=8:release=120', 'alimiter=limit=0.92',
                        f'loudnorm=I={lufs}:TP=-1.5:LRA=11'])
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(сырой), '-af', цепочка, '-ar', '44100', '-ac', '1', '-codec:a', 'libmp3lame', '-b:a', '128k', str(mp3)], check=True)


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
    tf = аудио / 'timings.json'
    тайминги = json.loads(tf.read_text(encoding='utf-8')) if tf.exists() else {}
    тайминги = {k: v for k, v in тайминги.items() if k in биты}      # убранные из сценария биты уходят и отсюда
    темп, lufs = float(н.get('темп', 1.0)), float(н.get('громкость', -14))
    try:
        движок = None
        выравнивание = Выравнивание(н.get('whisper', 'small'))
        for id_, сырой_текст in биты.items():
            if выбор and id_ not in выбор:
                continue
            чистый, метки = разобрать_метки(сырой_текст)
            ключ = hashlib.sha1(f'{имя}|{json.dumps(н, ensure_ascii=False, sort_keys=True)}|{чистый}'.encode()).hexdigest()
            wav, kf = сырые / f'{id_}.wav', сырые / f'{id_}.key'
            if not (wav.exists() and kf.exists() and kf.read_text() == ключ):
                движок = движок or БЭКЕНДЫ[имя](н, папка)
                print(f'{id_}: озвучиваю…', flush=True)
                движок.синтез(чистый, wav)
                kf.write_text(ключ)
            mp3 = аудио / f'{id_}.mp3'
            _обработать(wav, mp3, темп, lufs)
            длит = _длительность(mp3)
            слова, услышано = выравнивание.слова(mp3, чистый, длит)
            тайминги[id_] = {'dur': длит, 'marks': время_меток(чистый, метки, слова), 'words': слова}
            print(f'{id_}: {длит} с, слов {len(слова)}, услышано {услышано}, метки {тайминги[id_]["marks"]}', flush=True)
    except (ОшибкаОзвучки, ValueError) as e:
        sys.exit(f'Ошибка озвучки: {e}')
    порядок = {k: тайминги[k] for k in биты if k in тайминги}
    tf.write_text(json.dumps(порядок, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Готово: {tf}')

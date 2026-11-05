"""Общие ресурсы, которые генерируются один раз: звуковые эффекты и плитка киношного зерна (PNG пишется вручную, без Pillow)."""
import struct
import zlib
from pathlib import Path

import numpy as np

from . import sfx


def _png(rgba, path):
    h, w, _ = rgba.shape
    сырые = b''.join(b'\x00' + rgba[y].tobytes() for y in range(h))
    def блок(тип, данные):
        c = struct.pack('>I', len(данные)) + тип + данные
        return c + struct.pack('>I', zlib.crc32(тип + данные) & 0xffffffff)
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n' + блок(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + блок(b'IDAT', zlib.compress(сырые, 9)) + блок(b'IEND', b''))


def зерно(path):
    rng = np.random.default_rng(7)
    n = rng.random((256, 256))
    rgba = np.zeros((256, 256, 4), dtype=np.uint8)
    rgba[n > .94] = (255, 244, 225, 46)    # светлые крапинки
    rgba[n < .06] = (0, 0, 0, 70)          # тёмные крапинки
    _png(rgba, path)
    print(f'зерно: {path}')


def всё(корень):
    корень = Path(корень)
    sfx.сгенерировать(корень / 'assets' / 'sfx')
    зерно(корень / 'assets' / 'grain.png')

import shutil

import pytest

from mmlib import sfx


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='нужен ffmpeg')
def test_эффекты_синтезируются(tmp_path):
    sfx.сгенерировать(tmp_path)
    for имя in sfx.ЭФФЕКТЫ:
        assert (tmp_path / f'{имя}.mp3').stat().st_size > 500

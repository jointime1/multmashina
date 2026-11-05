#!/usr/bin/env bash
# Запускает команды Мультмашины из любой папки: bash mm.sh <команда> …  (или просто mm.sh, если путь к нему лежит в переменной MM).
# Обёртка нужна вместо переменной с командой «uv run …»: в zsh (оболочка Mac по умолчанию) такая переменная не разбивается на слова.
# Ведущие аргументы вида +имя включают экстры (озвучка ставится по выбору):
#   mm.sh окружение
#   mm.sh +voice +qwen озвучить reels/ролик      →  uv run --extra voice --extra qwen python …/scripts/mm.py озвучить reels/ролик
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
home="$(bash "$here/setup.sh")"
extras=()
while [ $# -gt 0 ] && [[ "$1" == +* ]]; do extras+=(--extra "${1#+}"); shift; done
exec uv run --project "$home" ${extras[@]+"${extras[@]}"} python "$home/scripts/mm.py" "$@"

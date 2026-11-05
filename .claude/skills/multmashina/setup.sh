#!/usr/bin/env bash
# Печатает путь к рабочей копии Мультмашины. Если скилл лежит внутри репозитория — это он сам; иначе копия
# клонируется в $MULTMASHINA_HOME (по умолчанию ~/.local/share/multmashina). Уже склонированную копию
# обновляет только явный вызов с --update. Сообщения идут в stderr, в stdout — один путь:
#   MM_HOME="$(bash setup.sh)"
# (Имена переменных латиницей: bash не принимает кириллицу в идентификаторах.)
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../../.." 2>/dev/null && pwd || true)"
if [ -n "$repo" ] && [ -f "$repo/scripts/mm.py" ] && [ -d "$repo/engine" ]; then
  echo "$repo"; exit 0
fi

home="${MULTMASHINA_HOME:-$HOME/.local/share/multmashina}"
if [ -d "$home/.git" ]; then
  if [ "${1:-}" = "--update" ]; then
    echo "Обновляю $home" >&2
    git -C "$home" pull --ff-only -q >&2 || echo "Не удалось обновить, использую то, что есть" >&2
  fi
else
  echo "Клонирую Мультмашину в $home" >&2
  git clone --depth 1 -q https://github.com/jointime1/multmashina "$home" >&2
fi
echo "$home"

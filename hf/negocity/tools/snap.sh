#!/usr/bin/env bash
# Uso: tools/snap.sh "t1,t2,..." [nombre]  -> hoja de contacto en .snaps/<nombre>.jpg
set -e
cd "$(dirname "$0")/.."
N="${2:-sheet}"; O=".snaps/$N"; rm -rf "$O"; mkdir -p "$O"
npx hyperframes snapshot --at "$1" --no-end -o "$O" >/dev/null 2>&1 || npx hyperframes snapshot --at "$1" --no-end -o "$O" 2>&1 | tail -5
C=$(ls "$O"/*.png | wc -l); COLS=${3:-4}
ffmpeg -v error -y -pattern_type glob -i "$O/*.png" -vf "scale=${4:-405}:-1,tile=${COLS}x$(( (C + COLS - 1) / COLS ))" -frames:v 1 ".snaps/$N.jpg"
ls "$O" | tr '\n' ' '

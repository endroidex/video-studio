#!/usr/bin/env bash
# Uso: ./make.sh <proyecto> [--preview]
#   1) voz + subtítulos + SFX + música + mezcla (scripts/build.py)
#   2) render 1080x1920 con Remotion
#   3) post en ffmpeg: grano de película + faststart para redes
set -euo pipefail
cd "$(dirname "$0")"
P="${1:?Uso: ./make.sh <proyecto>}"
.venv/bin/python scripts/build.py "$P"
mkdir -p out
SCALE=1; SUF=""
[[ "${2:-}" == "--preview" ]] && { SCALE=0.5; SUF="-preview"; }
npx remotion render src/index.ts Reel "out/.$P$SUF.raw.mp4" --props="{\"project\":\"$P\"}" --scale=$SCALE 2>&1 \
  | grep -E "Encoded [0-9]+/[0-9]+$|Error|error" | awk 'NR%200==0 || /Error|error/' || true
ffmpeg -v error -y -i "out/.$P$SUF.raw.mp4" -vf "noise=c0s=6:c0f=t+u" -c:v libx264 -crf 18 -preset medium \
  -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "out/$P$SUF.mp4"
rm -f "out/.$P$SUF.raw.mp4"
echo "Listo: out/$P$SUF.mp4"

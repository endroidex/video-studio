#!/usr/bin/env bash
# Render final: HyperFrames renderiza la imagen y después se sustituye el audio por la mezcla masterizada
# (el render de HyperFrames puede dejar el audio varios dB por debajo de la mezcla) con limitador de pico real.
# Uso: tools/render.sh ../../out/nombre.mp4
set -e
cd "$(dirname "$0")/.."
OUT="${1:?Uso: tools/render.sh salida.mp4}"
npx hyperframes render -o "$OUT.raw.mp4"
ffmpeg -v error -y -i "$OUT.raw.mp4" -i assets/audio/mix.wav -map 0:v -map 1:a -c:v copy \
  -af "alimiter=limit=0.71:attack=2:release=50:level=false" -c:a aac -b:a 256k -movflags +faststart "$OUT"
rm -f "$OUT.raw.mp4"
ffmpeg -nostats -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -A14 Summary | grep -E " I:|Peak:"

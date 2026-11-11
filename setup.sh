#!/usr/bin/env bash
# Reinstala todo lo que no se guarda en el repositorio (dependencias y modelos). Uso: bash setup.sh
set -e
cd "$(dirname "$0")"
npm install --silent
python3 -m venv .venv && .venv/bin/pip install -q faster-whisper piper-tts numpy scipy soundfile pyloudnorm pillow qrcode
python3 -m venv .venv-tts && .venv-tts/bin/pip install -q kokoro-onnx soundfile
pip3 install -q uv && uv python install 3.11 && uv venv -q -p 3.11 .venv-tts2 && VIRTUAL_ENV=.venv-tts2 uv pip install -q chatterbox-tts "setuptools<81"
mkdir -p models/voices models/kokoro
B=https://huggingface.co/rhasspy/piper-voices/resolve/main/es
for v in es_MX/claude/high/es_MX-claude-high es_MX/ald/medium/es_MX-ald-medium; do n=$(basename $v)
  [ -f models/voices/$n.onnx ] || { curl -sSfL -o models/voices/$n.onnx "$B/$v.onnx"; curl -sSfL -o models/voices/$n.onnx.json "$B/$v.onnx.json"; }; done
for f in kokoro-v1.0.onnx voices-v1.0.bin; do [ -f models/kokoro/$f ] || curl -sSfL -o models/kokoro/$f https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f; done
echo "Listo. Los modelos de Whisper y Chatterbox se descargan solos en el primer uso."

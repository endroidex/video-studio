#!/usr/bin/env python3
"""Efectos de sonido con ElevenLabs, con biblioteca en caché: cada efecto se genera UNA vez y se reutiliza
en todos los videos (assets/sfx/<nombre>.wav), para no gastar créditos de más.
  get("whoosh-suave", "soft airy whoosh transition, short", 1.0) -> ruta al .wav
CLI: python scripts/sfx_eleven.py <nombre> "<descripción en inglés>" [segundos]
     python scripts/sfx_eleven.py lista"""
import json, subprocess, sys, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from eleven import call

LIB = Path(__file__).resolve().parent.parent / "assets" / "sfx"


def get(name, prompt=None, seconds=1.0, influence=0.5):
    LIB.mkdir(parents=True, exist_ok=True)
    out = LIB / f"{name}.wav"
    if out.exists() or prompt is None:
        return out if out.exists() else None
    data = call("/v1/sound-generation?output_format=mp3_44100_128", {"text": prompt, "duration_seconds": seconds, "prompt_influence": influence}, raw=True)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(data); mp3 = f.name
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ar", "48000", "-ac", "1", str(out)], check=True)
    os.unlink(mp3)
    idx = LIB / "index.json"
    reg = json.loads(idx.read_text()) if idx.exists() else {}
    reg[name] = {"prompt": prompt, "seconds": seconds}
    idx.write_text(json.dumps(reg, ensure_ascii=False, indent=1))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "lista":
        idx = LIB / "index.json"; print(idx.read_text() if idx.exists() else "{}")
    else:
        print(get(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, float(sys.argv[3]) if len(sys.argv) > 3 else 1.0))

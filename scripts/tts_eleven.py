#!/usr/bin/env python3
"""Voz con ElevenLabs + tiempos palabra por palabra exactos (sin Whisper).
  synth(texto, voice_id, salida.wav, model=..., **ajustes) -> {"dur": s, "words": [{"text","start","end"}], "chars": n}
CLI: python scripts/tts_eleven.py voces            (lista las voces de la cuenta)
     python scripts/tts_eleven.py uso              (caracteres usados del mes)
     python scripts/tts_eleven.py di <voz> "texto" salida.wav [modelo]"""
import base64, json, os, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from eleven import call

ROOT = Path(__file__).resolve().parent.parent
VOICES = ROOT / "voices.json"           # alias -> voice_id (voces elegidas para los videos)
DEFAULT_MODEL = "eleven_v4"


def voice_id(name):
    reg = json.loads(VOICES.read_text()) if VOICES.exists() else {}
    return reg.get(name, {}).get("id", name)


def default_voice():
    reg = json.loads(VOICES.read_text()) if VOICES.exists() else {}
    return reg.get("_default", {}).get("alias") or next((k for k in reg if not k.startswith("_")), "marto")


def synth(text, voice, out_wav, model=None, stability=0.5, similarity=0.8, style=0.0, speed=1.0, lang="es", prev=None, nxt=None):
    body = {"text": text, "model_id": model or DEFAULT_MODEL, "language_code": lang,
            "voice_settings": {"stability": stability, "similarity_boost": similarity, "style": style, "use_speaker_boost": True, "speed": speed}}
    if prev: body["previous_text"] = prev
    if nxt: body["next_text"] = nxt
    try:
        r = call(f"/v1/text-to-speech/{voice_id(voice)}/with-timestamps?output_format=mp3_44100_128", body)
    except RuntimeError as e:          # algunos modelos no aceptan language_code / previous_text
        if "language_code" in str(e) or "previous_text" in str(e) or "next_text" in str(e) or "unsupported" in str(e).lower():
            for k in ("language_code", "previous_text", "next_text"): body.pop(k, None)
            r = call(f"/v1/text-to-speech/{voice_id(voice)}/with-timestamps?output_format=mp3_44100_128", body)
        else:
            raise
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(base64.b64decode(r["audio_base64"])); mp3 = f.name
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ar", "48000", "-ac", "1", str(out_wav)], check=True)
    os.unlink(mp3)
    al = r.get("alignment") or r.get("normalized_alignment")
    words, cur = [], None
    for ch, s, e in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch.isspace():
            if cur: words.append(cur); cur = None
        elif cur is None: cur = {"text": ch, "start": s, "end": e}
        else: cur["text"] += ch; cur["end"] = e
    if cur: words.append(cur)
    import soundfile as sf
    return {"dur": sf.info(str(out_wav)).duration, "words": words, "chars": len(text)}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "uso"
    if cmd == "uso":
        s = call("/v1/user/subscription"); print(f'{s["character_count"]} / {s["character_limit"]} caracteres usados ({s["tier"]})')
    elif cmd == "voces":
        for v in call("/v2/voices?page_size=100")["voices"]:
            l = v.get("labels") or {}; print(v["voice_id"], "|", v["name"], "|", v.get("category"), l.get("gender"), l.get("accent"), l.get("language"))
    elif cmd == "di":
        r = synth(sys.argv[3], sys.argv[2], sys.argv[4], model=sys.argv[5] if len(sys.argv) > 5 else None)
        print(f'{r["dur"]:.2f}s', " ".join(f'{w["text"]}@{w["start"]:.2f}' for w in r["words"]))

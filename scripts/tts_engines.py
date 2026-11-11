"""
Motores de voz. Se ejecuta con el venv que corresponde al motor:
  kokoro            -> .venv-tts   (rápido, voces ef_dora / em_alex / em_santa)
  chatterbox        -> .venv-tts2  (natural, expresivo, CLONA una voz desde 10-20 s de audio)
  qwen              -> .venv-tts2  (Qwen3-TTS, también clona; lento en CPU)
Uso: python tts_engines.py <motor> <voz|-> <jobs.json> [ref.wav|-] [velocidad]
     jobs.json = [{"text": "...", "out": "ruta.wav"}, ...]  (el modelo se carga una sola vez)
"""
import os, sys
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("HF_HOME", os.path.join(ROOT, "models/hf"))

import json
engine, voice, jobs_file = sys.argv[1:4]
ref = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] not in ("", "-") else None
speed = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
jobs = json.load(open(jobs_file, encoding="utf-8"))

if engine == "kokoro":
    from kokoro_onnx import Kokoro
    k = Kokoro(f"{ROOT}/models/kokoro/kokoro-v1.0.onnx", f"{ROOT}/models/kokoro/voices-v1.0.bin")
    for j in jobs:
        a, sr = k.create(j["text"], voice=voice if voice != "-" else "ef_dora", speed=speed, lang="es")
        sf.write(j["out"], a, sr)

elif engine == "chatterbox":
    import torch, torchaudio as ta
    torch.set_num_threads(os.cpu_count() or 4)
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    ex = float(os.environ.get("CB_EXAGGERATION", "0.6"))
    cfg = float(os.environ.get("CB_CFG", "0.4"))
    for j in jobs:
        w = m.generate(j["text"], language_id="es", audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfg)
        ta.save(j["out"], w, m.sr)

elif engine == "qwen":
    import torch
    torch.set_num_threads(os.cpu_count() or 4)
    from qwen_tts import Qwen3TTSModel
    if ref:
        m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-0.6B-Base", device_map="cpu", dtype=torch.float32)
        ref_text = os.environ.get("QWEN_REF_TEXT")
        gen = lambda t: m.generate_voice_clone(text=t, language="Spanish", ref_audio=ref, ref_text=ref_text,
                                               x_vector_only_mode=ref_text is None)
    else:
        m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice", device_map="cpu", dtype=torch.float32)
        gen = lambda t: m.generate_custom_voice(text=t, language="Spanish", speaker=voice if voice != "-" else "ryan")
    for j in jobs:
        wavs, sr = gen(j["text"])
        sf.write(j["out"], wavs[0], sr)
else:
    sys.exit(f"motor desconocido: {engine}")

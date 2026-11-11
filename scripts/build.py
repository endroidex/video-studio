#!/usr/bin/env python3
"""
Pipeline de audio + timeline:
  guion (projects/<id>/script.json)
   -> voz por escena (Piper TTS, o ElevenLabs si hay API key)
   -> timestamps palabra por palabra (faster-whisper) alineados al guion
   -> tiempos de animación (items que aparecen cuando se nombran)
   -> SFX + música + ducking + master a -14 LUFS
   -> public/projects/<id>/{timeline.json, mix.wav}
Uso: python scripts/build.py <id>
"""
import json, os, re, subprocess, sys, difflib, unicodedata, shutil
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy import signal

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import audio_lib as A  # noqa: E402

SR = A.SR
FPS = 30


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        raise RuntimeError(f"{cmd[0]} falló:\n{r.stderr[-2000:]}")
    return r.stdout


def normw(w):
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9%]", "", w)


def tokens(text):
    out = []
    for raw in text.split():
        acc = "*" in raw
        out.append({"text": raw.replace("*", ""), "accent": acc})
    return out


def spoken(text):
    import pron
    return pron.say(text.replace("*", ""))


# ------------------------------------------------------------------ voz
ENGINE_VENV = {"kokoro": ".venv-tts", "chatterbox": ".venv-tts2", "qwen": ".venv-tts2"}


def engine_of(cfg):
    # Por defecto, voz local gratuita (pruebas y demos). ElevenLabs SOLO si el guion dice "tts": "elevenlabs",
    # y además el comando debe llevar ELEVEN_APPROVED=1 (el usuario pidió explícitamente ese video con ElevenLabs).
    if cfg.get("tts") in ("elevenlabs", "eleven"):
        return "elevenlabs"
    return cfg.get("tts", "chatterbox")


def batch_tts(jobs, cfg, tmp):
    """Motores externos (kokoro/chatterbox/qwen): una sola carga del modelo para todas las escenas."""
    eng = engine_of(cfg)
    if eng not in ENGINE_VENV or not jobs:
        return
    jf = tmp / "tts_jobs.json"
    jf.write_text(json.dumps([{"text": t, "out": str(tmp / (w.stem + "_raw.wav"))} for t, w in jobs], ensure_ascii=False))
    ref = cfg.get("voice_ref")
    ref = str((ROOT / "projects" / cfg["_id"] / ref) if ref and not os.path.isabs(ref) else ref or "-")
    print(f"  {eng}: generando {len(jobs)} escenas...")
    r = subprocess.run([str(ROOT / ENGINE_VENV[eng] / "bin/python"), str(ROOT / "scripts/tts_engines.py"), eng,
                        cfg.get("voice", "-"), str(jf), ref, str(cfg.get("speed", 1.0))], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-3000:])


def tts(text, out_wav, cfg, tmp):
    raw = tmp / (out_wav.stem + "_raw.wav")
    if engine_of(cfg) in ENGINE_VENV:
        pass  # ya generado por batch_tts
    elif engine_of(cfg) == "elevenlabs":
        # ElevenLabs: voz + tiempos exactos de cada palabra (no hace falta Whisper)
        import tts_eleven
        r = tts_eleven.synth(text, cfg.get("elevenlabs_voice") or cfg.get("voice") or tts_eleven.default_voice(), raw, model=cfg.get("elevenlabs_model"),
                             speed=float(cfg.get("speed", 1.0)), stability=float(cfg.get("stability", 0.5)), style=float(cfg.get("style", 0.0)))
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", "highpass=f=70,acompressor=threshold=-22dB:ratio=2.5:attack=5:release=90:makeup=1.5",
            "-ar", str(SR), "-ac", "1", str(out_wav)])
        (tmp / (out_wav.stem + ".words.json")).write_text(json.dumps(r["words"], ensure_ascii=False))
        return
    else:
        voice = ROOT / "models/voices" / f"{cfg.get('voice', 'es_MX-claude-high')}.onnx"
        speed = float(cfg.get("speed", 1.0))
        subprocess.run(
            [str(ROOT / ".venv/bin/piper"), "-m", str(voice), "-f", str(raw), "--length_scale", str(1 / speed),
             "--sentence_silence", "0.18", "--noise_scale", "0.6", "--noise_w", "0.75"],
            input=text, text=True, capture_output=True, check=True,
        )
    # cadena de voz: limpieza, compresión, presencia, recorte de silencios en extremos
    sh(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
        "highpass=f=80,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3800:t=q:w=1.2:g=3,"
        "acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=2",
        "-ar", str(SR), "-ac", "1", str(out_wav)])


_model = None


def whisper_words(wav, prompt):
    global _model
    from faster_whisper import WhisperModel
    if _model is None:
        os.environ.setdefault("HF_HOME", str(ROOT / "models/hf"))
        _model = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")
    a, sr = sf.read(wav, dtype="float32")
    if sr != 16000:
        a = signal.resample_poly(a, 16000, sr).astype(np.float32)
    segs, _ = _model.transcribe(a, language="es", word_timestamps=True, initial_prompt=prompt)
    return [{"text": w.word.strip(), "start": w.start, "end": w.end} for s in segs for w in s.words]


def align(script_toks, wwords, dur):
    """Pone los tiempos de whisper sobre las palabras exactas del guion."""
    a = [normw(t["text"]) for t in script_toks]
    b = [normw(w["text"]) for w in wwords]
    times = [None] * len(a)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                times[i1 + k] = (wwords[j1 + k]["start"], wwords[j1 + k]["end"])
        elif tag == "replace" and j2 > j1:
            s, e = wwords[j1]["start"], wwords[j2 - 1]["end"]
            for k in range(i2 - i1):
                times[i1 + k] = (s + (e - s) * k / (i2 - i1), s + (e - s) * (k + 1) / (i2 - i1))
    # interpola huecos
    known = [i for i, t in enumerate(times) if t]
    for i, t in enumerate(times):
        if t is None:
            prev = max([k for k in known if k < i], default=None)
            nxt = min([k for k in known if k > i], default=None)
            s = times[prev][1] if prev is not None else 0.0
            e = times[nxt][0] if nxt is not None else dur
            times[i] = (s, max(s + 0.05, e))
    return [{**tok, "start": round(t[0], 3), "end": round(t[1], 3)} for tok, t in zip(script_toks, times)]


def find_word(words, key, after=0.0):
    k = normw(key)
    for w in words:
        if w["start"] >= after - 0.01 and normw(w["text"]).startswith(k):
            return w["start"]
    return None


# ------------------------------------------------------------------ main
def build(pid):
    pdir = ROOT / "projects" / pid
    cfg = json.loads((pdir / "script.json").read_text())
    out = ROOT / "public/projects" / pid
    tmp = pdir / ".cache"
    out.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(exist_ok=True)

    cfg["_id"] = pid
    sigs, pending = {}, []
    for i, sc in enumerate(cfg["scenes"]):
        wav, key = tmp / f"s{i:02d}.wav", tmp / f"s{i:02d}.key"
        sigs[i] = json.dumps([spoken(sc["voice"]), cfg.get("tts"), cfg.get("voice"), cfg.get("speed"),
                              cfg.get("voice_ref"), cfg.get("elevenlabs_voice"), cfg.get("elevenlabs_model"), cfg.get("stability"), cfg.get("style")])
        if not (wav.exists() and key.exists() and key.read_text() == sigs[i]):
            pending.append((spoken(sc["voice"]), wav))
    batch_tts(pending, cfg, tmp)

    lead = float(cfg.get("lead_in", 0.35))
    t = lead
    scenes, all_words, voice_parts = [], [], []
    for i, sc in enumerate(cfg["scenes"]):
        text = sc["voice"]
        wav = tmp / f"s{i:02d}.wav"
        key = tmp / f"s{i:02d}.key"
        sig = sigs[i]
        if not (wav.exists() and key.exists() and key.read_text() == sig):
            print(f"  voz escena {i + 1}/{len(cfg['scenes'])}")
            (tmp / f"s{i:02d}.words.json").unlink(missing_ok=True)
            tts(spoken(text), wav, cfg, tmp)
            key.write_text(sig)
        v, _ = sf.read(wav)
        vdur = len(v) / SR
        wcache = tmp / f"s{i:02d}.words.json"
        if wcache.exists():
            ww = json.loads(wcache.read_text())
        else:
            ww = whisper_words(wav, spoken(text))
            wcache.write_text(json.dumps(ww))
        words = align(tokens(text), ww, vdur)
        hold = float(sc.get("hold", 0.3))
        sdur = vdur + hold + (lead if i == 0 else 0)
        start = t - (lead if i == 0 else 0)
        voice_parts.append((t, v))
        for w in words:
            all_words.append({**w, "start": round(t + w["start"], 3), "end": round(t + w["end"], 3), "scene": i})
        sw = [w for w in all_words if w["scene"] == i]

        # tiempos de los elementos del widget (si dicen "at": "palabra", aparecen cuando se pronuncia)
        widget = dict(sc.get("widget") or {})
        items = widget.get("items") or []
        n = len(items)
        times, cursor = [], t
        for k, it in enumerate(items):
            at = it.get("at") if isinstance(it, dict) else None
            tt = find_word(sw, at, cursor) if at else None
            if tt is None:
                tt = t + 0.35 + (vdur * 0.75) * (k / max(1, n))
            times.append(round(tt - start, 3))
            cursor = tt
        widget["itemTimes"] = times
        if widget.get("stampAt"):
            st = find_word(sw, widget["stampAt"], t)
            widget["stampTime"] = round((st if st is not None else t + vdur * 0.6) - start, 3)
        hl_at = sc.get("headlineAt")
        sc_out = {**{k: v for k, v in sc.items() if k not in ("voice", "widget")}, "widget": widget,
                  "start": round(start, 3), "end": round(start + sdur, 3), "voiceStart": round(t, 3),
                  "headlineTime": round(((find_word(sw, hl_at, t) if hl_at else None) or t) - start, 3)}
        scenes.append(sc_out)
        t = start + sdur + (lead if i == 0 else 0) - (lead if i == 0 else 0)
        t = start + sdur
    total = t + float(cfg.get("tail", 0.8))

    # ---------------------------------------------------------- pista de voz
    n = int(total * SR) + SR
    voice = np.zeros(n)
    for st, v in voice_parts:
        s = int(st * SR)
        voice[s:s + len(v)] += v

    # envolvente para la boca del personaje (por frame)
    hop = SR // FPS
    nfr = int(np.ceil(total * FPS))
    rms = np.array([np.sqrt(np.mean(voice[k * hop:(k + 1) * hop] ** 2) + 1e-12) for k in range(nfr)])
    mouth = np.clip(rms / (np.percentile(rms[rms > 1e-4], 90) if np.any(rms > 1e-4) else 1), 0, 1)
    mouth = np.round(mouth, 2).tolist()

    # ---------------------------------------------------------- SFX automáticos
    cues = []
    for i, sc in enumerate(scenes):
        w = sc["widget"]
        typ = w.get("type")
        if i == 0:
            cues.append((sc["start"] + 0.02, "thud", 0.55))
        else:
            cues.append((sc["start"] - 0.12, "whoosh", 0.45))
        if sc.get("headline") and i > 0:
            cues.append((sc["start"] + sc["headlineTime"] + 0.05, "pop", 0.35))
        per = {"checklist": "tick", "steps": "pop_hi", "bars": "pop", "donut": "pop", "cards": "pop", "chat": "pop_hi"}.get(typ, "pop")
        for k, it in enumerate(w.get("itemTimes", [])):
            cues.append((sc["start"] + it + 0.03, per, 0.4))
            if typ == "checklist":
                cues.append((sc["start"] + it + 0.33, "click", 0.4))
        if typ == "stat":
            cues.append((sc["start"] + 0.25, "riser", 0.25))
            cues.append((sc["start"] + 1.45, w.get("endSfx", "ding"), 0.45))
        if typ == "typing":
            cues.append((sc["start"] + 0.35, "typing", 0.5))
        if "stampTime" in w:
            cues.append((sc["start"] + w["stampTime"], "thud", 0.5))
        for extra in sc.get("sfx", []):
            at = extra.get("at", 0)
            if isinstance(at, str):
                at = (find_word([x for x in all_words if x["scene"] == i], at, sc["start"]) or sc["start"]) - sc["start"]
            cues.append((sc["start"] + at, extra["name"], extra.get("gain", 0.5)))

    sfx_bank = {k: f() for k, f in A.SFX.items()}
    # efectos de la biblioteca de ElevenLabs (assets/sfx/<nombre>.wav) sustituyen a los sintetizados del mismo nombre
    for f in sorted((ROOT / "assets/sfx").glob("*.wav")):
        x, _sr = sf.read(f, dtype="float64")
        sfx_bank[f.stem] = A.norm(x if x.ndim == 1 else x.mean(1), 0.6)
    sfx = np.zeros(n)
    for at, name, g in cues:
        x = sfx_bank.get(name)
        if x is None:
            continue
        s = max(0, int(at * SR))
        e = min(n, s + len(x))
        sfx[s:e] += x[: e - s] * g

    # ---------------------------------------------------------- música + ducking
    mstyle = cfg.get("music", "lofi")
    mus = np.zeros(n)
    if mstyle and mstyle != "none":
        m = A.music(total, mstyle)
        mus[: len(m)] = m
        env = np.abs(signal.hilbert(voice[:: 48]))  # rápido, a 1 kHz
        env = signal.savgol_filter(env, 301, 2)
        env = np.interp(np.arange(n), np.arange(len(env)) * 48, env)
        ducked = np.where(env > 0.02, 1.0, 0.0)
        ducked = signal.sosfiltfilt(signal.butter(1, 3, fs=SR, output="sos"), ducked)
        gain = 0.38 - 0.24 * np.clip(ducked, 0, 1)
        mus = mus * gain * float(cfg.get("music_gain", 1.0))

    mix = voice * 1.0 + sfx * 0.8 + mus
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    st = np.stack([mix, mix], 1)  # se mide en estéreo (como lo miden las plataformas)
    mix = mix * 10 ** ((-14.0 - meter.integrated_loudness(st)) / 20)
    peak = 10 ** (-1 / 20)
    mix = np.where(np.abs(mix) > peak * 0.8, np.sign(mix) * (peak * 0.8 + (peak * 0.2) * np.tanh((np.abs(mix) - peak * 0.8) / (peak * 0.2))), mix)
    mix = mix[: int(total * SR)]
    sf.write(out / "mix.wav", np.stack([mix, mix], 1).astype(np.float32), SR, subtype="PCM_16")

    # assets del proyecto (imágenes, etc.)
    if (pdir / "assets").exists():
        shutil.copytree(pdir / "assets", out / "assets", dirs_exist_ok=True)

    timeline = {
        "id": pid, "fps": FPS, "width": cfg.get("width", 1080), "height": cfg.get("height", 1920),
        "durationInFrames": int(np.ceil(total * FPS)), "theme": cfg.get("theme", {}),
        "character": cfg.get("character", True), "scenes": scenes, "words": all_words, "mouth": mouth,
        "audio": f"projects/{pid}/mix.wav", "title": cfg.get("title", pid),
    }
    (out / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False))
    print(f"OK {pid}: {total:.1f}s, {len(scenes)} escenas, {len(all_words)} palabras, {len(cues)} SFX, "
          f"{meter.integrated_loudness(np.stack([mix, mix], 1)):.1f} LUFS")


if __name__ == "__main__":
    build(sys.argv[1])

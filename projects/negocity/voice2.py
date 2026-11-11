"""Voz de Negocity por segmentos: genera tomas con Chatterbox, las verifica con Whisper, elige la mejor,
recorta colas y escribe voice/final.json + voice/final_<seg>.wav.
Uso: ../../.venv/bin/python voice2.py gen <seg...> | ../../.venv/bin/python voice2.py final"""
import json, os, subprocess, sys, difflib, glob, re
from pathlib import Path
import numpy as np, soundfile as sf
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build as B
V = Path(__file__).parent / "voice"
# seg: (texto de subtítulo, texto para el motor)
SEGS = {
 "0": ("¿Tu negocio vive entre libretas, chats y hojas sueltas?", None),
 "1": ("Clientes que no regresan… cuentas que no cuadran… contactos que nunca encuentras.", "Clientes que no regresan. Cuentas que no cuadran. Contactos que nunca encuentras."),
 "2a": ("Conoce Negocity:", "Conoce Negositi."),
 "2b": ("todas las herramientas de tu negocio, en un solo lugar.", "Todas las herramientas de tu negocio, en un solo lugar."),
 "3": ("Tus clientes juntan visitas o puntos con una tarjeta digital en su celular… y siempre regresan.", "Tus clientes juntan visitas o puntos con una tarjeta digital en su celular, y siempre regresan."),
 "4": ("Mira quién vuelve, tus mejores días y cuánto vendes, en tiempo real.", None),
 "5": ("Tu equipo trabaja desde su celular, y tus proveedores y contactos siempre están a la mano.", None),
 "6": ("Clientes, administración y datos, todo conectado. Sin instalar nada.", None),
 "7": ("Negocity. Tu negocio, más fácil.", "Negositi. Tu negocio, más fácil."),
 "8": ("Empieza hoy en negocity punto com punto mx.", "Empieza hoy en negositi punto com, punto eme equis."),
}
TAKES = V / "takes.json"
takes = json.loads(TAKES.read_text()) if TAKES.exists() else {}

def post(raw, out):
    B.sh(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
          "silenceremove=start_periods=1:start_threshold=-45dB,highpass=f=80,equalizer=f=220:t=q:w=1:g=-1.5,equalizer=f=3800:t=q:w=1.2:g=2.5,"
          "acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=2", "-ar", "48000", "-ac", "1", str(out)])

def score(key, wav):
    target = SEGS[key][1] or SEGS[key][0]
    ww = B.whisper_words(wav, target)
    a = [x for x in (B.normw(w) for w in target.split()) if x]; b = [x for x in (B.normw(w["text"]) for w in ww) if x]
    acc = sum(m.size for m in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks()) / len(a)
    span = (ww[-1]["end"] - ww[0]["start"]) if ww else 0.0
    rate = len(a) / span if span > 0 else 99.0
    ok = bool(acc >= 0.99 and len(b) <= len(a) and 2.3 <= rate <= 3.7)
    return {"file": Path(wav).name, "acc": float(acc), "rate": float(rate), "ok": ok, "ww": ww, "heard": " ".join(w["text"] for w in ww)}

def register(key, wav):
    r = score(key, wav); takes.setdefault(key, [])
    takes[key] = [t for t in takes[key] if t["file"] != r["file"]] + [r]
    print(f'{key} {r["file"]}: acc={r["acc"]:.2f} ritmo={r["rate"]:.2f} {"OK" if r["ok"] else "--"} | {r["heard"]}', flush=True)
    TAKES.write_text(json.dumps(takes, ensure_ascii=False))
    return r["ok"]

cmd = sys.argv[1]
if cmd == "adopt":   # tomas ya generadas: adopt seg archivo
    for key, f in zip(sys.argv[2::2], sys.argv[3::2]):
        register(key, V / f)
elif cmd == "gen":
    todo = sys.argv[2:]
    for attempt in range(int(os.environ.get("START", "20")), int(os.environ.get("START", "20")) + int(os.environ.get("TRIES", "3"))):
        if not todo: break
        jobs = [{"text": SEGS[k][1] or SEGS[k][0], "out": str(V / f"s{k}_a{attempt}_raw.wav")} for k in todo]
        (V / "jobs.json").write_text(json.dumps(jobs, ensure_ascii=False))
        env = dict(os.environ, CB_EXAGGERATION=os.environ.get("CB_EXAGGERATION", "0.45"), CB_CFG=os.environ.get("CB_CFG", "0.3"))
        r = subprocess.run([str(ROOT / ".venv-tts2/bin/python"), str(ROOT / "scripts/tts_engines.py"), "chatterbox", "-", str(V / "jobs.json"), "-", "1.0"], capture_output=True, text=True, env=env)
        if r.returncode: raise RuntimeError(r.stderr[-2000:])
        nxt = []
        for k in todo:
            out = V / f"s{k}_a{attempt}.wav"; post(V / f"s{k}_a{attempt}_raw.wav", out)
            if not register(k, out): nxt.append(k)
        todo = nxt
    print("pendientes:", todo)
elif cmd == "final":
    final = {}
    for key in SEGS:
        cands = sorted(takes.get(key, []), key=lambda t: (not t["ok"], -round(t["acc"], 2), abs(t["rate"] - 3.0)))
        if key in os.environ.get("PICK", ""):
            pick = dict(p.split("=") for p in os.environ["PICK"].split(","))
            cands = [t for t in cands if t["file"] == pick.get(key)] or cands
        t = cands[0]
        a, sr = sf.read(V / t["file"], dtype="float32")
        s0 = max(0.0, t["ww"][0]["start"] - 0.06); e0 = min(len(a) / sr, t["ww"][-1]["end"] + 0.30)
        seg = a[int(s0 * sr):int(e0 * sr)].copy()
        fo = int(0.14 * sr); seg[-fo:] *= np.linspace(1, 0, fo) ** 1.5; fi = int(0.02 * sr); seg[:fi] *= np.linspace(0, 1, fi)
        sf.write(V / f"final_{key}.wav", seg, sr)
        k = 1.0
        if t["rate"] > 3.7:   # toma correcta pero rápida: se desacelera sin cambiar el tono
            k = max(0.84, 3.55 / t["rate"])
            flt = f"rubberband=tempo={k:.3f}:pitchq=quality" if os.environ.get("RB") else f"atempo={k:.3f}"
            B.sh(["ffmpeg", "-v", "error", "-y", "-i", str(V / f"final_{key}.wav"), "-af", flt, str(V / f"final_{key}_s.wav")])
            os.replace(V / f"final_{key}_s.wav", V / f"final_{key}.wav")
            seg, sr = sf.read(V / f"final_{key}.wav", dtype="float32")
        dur = len(seg) / sr
        ww = [{"text": w["text"], "start": max(0.0, w["start"] - s0) / k, "end": min(dur, (w["end"] - s0) / k)} for w in t["ww"]]
        words = B.align(B.tokens(SEGS[key][0]), ww, dur)
        final[key] = {"file": f"final_{key}.wav", "src": t["file"], "dur": round(dur, 3), "text": SEGS[key][0].replace(" punto com punto mx.", ".com.mx"), "words": words, "ok": bool(t["acc"] >= 0.99), "rate": round(t["rate"] * k, 2), "tempo": round(k, 3)}
        print(key, t["file"], "ok" if t["ok"] else "NO-OK", f'{dur:.2f}s', f'{t["rate"]:.2f} pal/s', "|", " ".join(f'{w["text"]}@{w["start"]:.2f}' for w in words))
    (V / "final.json").write_text(json.dumps(final, ensure_ascii=False, indent=1))
    print("habla total", round(sum(f["dur"] for f in final.values()), 2))

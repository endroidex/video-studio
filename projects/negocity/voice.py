"""Genera las 9 líneas de voz con Chatterbox, las verifica con Whisper y reintenta las que salgan mal.
Uso: ../../.venv/bin/python voice.py [indices a regenerar...]"""
import json, os, subprocess, sys, difflib
from pathlib import Path
import soundfile as sf
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build as B

HERE = Path(__file__).parent
V = HERE / "voice"
# (texto en pantalla / subtítulos, texto fonético para el motor de voz)
LINES = [
    ("¿Tu negocio vive entre libretas, chats y hojas sueltas?", None),
    ("Clientes que no regresan… cuentas que no cuadran… contactos que nunca encuentras.",
     "Clientes que no regresan. Cuentas que no cuadran. Contactos que nunca encuentras."),
    ("Conoce Negocity: todas las herramientas de tu negocio, en un solo lugar.",
     "Conoce Negositi: todas las herramientas de tu negocio, en un solo lugar."),
    ("Tus clientes juntan visitas o puntos con una tarjeta digital en su celular… y siempre regresan.",
     "Tus clientes juntan visitas o puntos con una tarjeta digital en su celular, y siempre regresan."),
    ("Mira quién vuelve, tus mejores días y cuánto vendes, en tiempo real.", None),
    ("Tu equipo trabaja desde su celular, y tus proveedores y contactos siempre están a la mano.", None),
    ("Clientes, administración y datos, todo conectado. Sin instalar nada.", None),
    ("Negocity. Tu negocio, más fácil.", "Negositi. Tu negocio, más fácil."),
    ("Empieza hoy en negocity.com.mx", "Empieza hoy en negositi punto com, punto eme equis."),
]
SPOKEN_AS = {8: "Empieza hoy en negocity punto com punto mx"}  # palabras para alinear subtítulos

def gen(idx, attempt):
    jobs = [{"text": LINES[i][1] or LINES[i][0], "out": str(V / f"l{i}_a{attempt}_raw.wav")} for i in idx]
    jf = V / "jobs.json"; jf.write_text(json.dumps(jobs, ensure_ascii=False))
    env = dict(os.environ, CB_EXAGGERATION=os.environ.get("CB_EXAGGERATION","0.5"), CB_CFG=os.environ.get("CB_CFG","0.5"))
    r = subprocess.run([str(ROOT / ".venv-tts2/bin/python"), str(ROOT / "scripts/tts_engines.py"), "chatterbox", "-", str(jf), "-", "1.0"],
                       capture_output=True, text=True, env=env)
    if r.returncode: raise RuntimeError(r.stderr[-2000:])

def post(i, attempt):
    raw, out = V / f"l{i}_a{attempt}_raw.wav", V / f"l{i}_a{attempt}.wav"
    B.sh(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
          "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "highpass=f=80,equalizer=f=220:t=q:w=1:g=-1.5,equalizer=f=3800:t=q:w=1.2:g=2.5,"
          "acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=2", "-ar", "48000", "-ac", "1", str(out)])
    return out

def score(i, wav):
    target = LINES[i][1] or LINES[i][0]
    ww = B.whisper_words(wav, target)
    a = [B.normw(w) for w in target.split()]; b = [B.normw(w["text"]) for w in ww]
    a = [x for x in a if x]; b = [x for x in b if x]
    acc = sum(m.size for m in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks()) / len(a)
    dur = sf.info(wav).duration
    return acc, dur, ww, " ".join(w["text"] for w in ww)

todo = [int(x) for x in sys.argv[1:]] or list(range(len(LINES)))
state_f = V / "lines.json"
state = json.loads(state_f.read_text()) if state_f.exists() and not os.environ.get("FRESH") else {}
for attempt in range(int(os.environ.get("START", "0")), int(os.environ.get("START", "0")) + 3):
    if not todo: break
    gen(todo, attempt)
    nxt = []
    for i in todo:
        wav = post(i, attempt)
        acc, dur, ww, heard = score(i, wav)
        nw = len((LINES[i][1] or LINES[i][0]).split())
        span = (ww[-1]["end"] - ww[0]["start"]) if ww else 0
        rate = nw / span if span else 99
        ok = acc >= 0.95 and len(ww) <= nw + 1 and 2.3 <= rate <= float(os.environ.get("MAXRATE", "3.5"))
        print(f"L{i} intento {attempt}: acc={acc:.2f} habla={span:.2f}s archivo={dur:.2f}s ritmo={rate:.2f} pal/s {'OK' if ok else 'REINTENTAR'} | {heard}", flush=True)
        prev = state.get(str(i))
        better = prev is None or (ok and not prev.get("ok")) or (ok == prev.get("ok", False) and acc >= prev["acc"] and abs(rate - 3.0) < abs(prev.get("rate", 99) - 3.0))
        if better:
            disp = SPOKEN_AS.get(i, LINES[i][0])
            words = B.align(B.tokens(disp), ww, dur)
            state[str(i)] = {"file": wav.name, "acc": acc, "dur": dur, "rate": rate, "text": LINES[i][0], "words": words, "heard": heard, "ok": ok}
        if not ok: nxt.append(i)
    todo = nxt
    state_f.write_text(json.dumps(state, ensure_ascii=False, indent=1))
print("pendientes:", todo)
